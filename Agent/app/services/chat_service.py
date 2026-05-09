"""Tool-calling chat orchestration service.
基于工具调用的聊天编排服务。

This module is the "director" of the agent:
这个模块是 agent 的“导演层”：

- Accept user input and build the chat context
  - 接收用户输入并构建上下文
- Bind the available LangChain tools to the LLM
  - 将可用的 LangChain 工具绑定到模型
- Execute the tool-calling loop
  - 执行工具调用循环
- Return the final natural-language answer
  - 返回最终的自然语言回复

Important boundary:
重要边界：
- Do not put SQL, HTTP business logic, or RAG retrieval details here.
  - 不要把 SQL、HTTP 业务逻辑或 RAG 检索细节放在这里。
- Domain operations should be delegated to services such as order/course/booking services.
  - 领域操作应委托给订单、课程、预约等领域服务。
"""

from __future__ import annotations

from typing import Any
from datetime import datetime, timedelta
import json
import re
from zoneinfo import ZoneInfo

from ..integrations.deepseek_client import deepseek_is_configured, get_deepseek_chat_model
from ..schemas.chat import ChatRequest, ChatResponse, ChatToolCall
from ..schemas.intent import IntentAnalysisRequest
from ..services.cart_service import add_cart_item as add_cart_item_service
from ..services.intent_service import analyze_intent
from ..services.member_service import query_member_profile as query_member_profile_service
from ..services.order_service import create_order as create_order_service
from ..services.rag_service import answer_knowledge_question
from ..services.memory_service import (
    append_chat_message,
    clear_pending_action,
    get_chat_messages,
    get_pending_action,
    render_chat_history,
    store_pending_action,
)
from ..tools.gym_tools import get_gym_tools
from ..tools._shared import request_context_scope


_WRITE_TOOL_NAMES = {
    "create_booking",
    "cancel_booking",
    "enroll_course",
    "cancel_enrollment",
    "cancel_order",
    "add_cart_item",
    "update_cart_item",
    "delete_cart_item",
    "create_order",
    "purchase_order",
}

_CONFIRMATION_RE = re.compile(r"^(确认|确定|执行|好的|好|是的|继续|没问题|可以|同意)$", re.IGNORECASE)
_KNOWLEDGE_TOOL_NAMES = {"rag_search", "web_search"}
_BOOKING_INTENT_RE = re.compile(r"(预约|预定|订|帮我约|训练室|健身房|场地)")
_CN_NUMBER_MAP = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


def _resolve_timezone_name(request: ChatRequest) -> str:
    metadata = request.metadata or {}
    timezone_candidates = [
        metadata.get("timezone"),
        metadata.get("time_zone"),
        metadata.get("tz"),
        metadata.get("client_timezone"),
    ]
    for candidate in timezone_candidates:
        if not isinstance(candidate, str):
            continue
        value = candidate.strip()
        if not value:
            continue
        try:
            ZoneInfo(value)
            return value
        except Exception:
            continue
    return "Asia/Shanghai"


def _build_time_anchor(request: ChatRequest) -> dict[str, str]:
    timezone_name = _resolve_timezone_name(request)
    now = datetime.now(ZoneInfo(timezone_name))
    today = now.date()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    return {
        "timezone": timezone_name,
        "now": now.strftime("%Y-%m-%d %H:%M:%S"),
        "today": today.strftime("%Y-%m-%d"),
        "yesterday": yesterday.strftime("%Y-%m-%d"),
        "tomorrow": tomorrow.strftime("%Y-%m-%d"),
    }


def _build_time_anchor_text(request: ChatRequest) -> str:
    anchor = _build_time_anchor(request)
    return (
        "时间锚点（必须遵守）：\n"
        f"- 当前时区: {anchor['timezone']}\n"
        f"- 当前时间: {anchor['now']}\n"
        f"- 今天: {anchor['today']}\n"
        f"- 明天: {anchor['tomorrow']}\n"
        f"- 昨天: {anchor['yesterday']}\n"
        "涉及“今天/明天/昨天”时，必须严格按以上日期解释；优先输出绝对日期（YYYY-MM-DD）。"
    )


def _build_system_message() -> str:
    """Keep the instructions short and direct.
    系统提示词尽量简短直接。
    """

    return (
        "你是健身系统的助手。\n"
        "如果用户的问题需要查询业务数据或执行业务动作，就调用合适的工具。\n"
        "如果是知识问题，就调用 rag_search 或 web_search。\n"
        "如果用户在表达购买意图，先由模型结合上下文理解商品和数量；"
        "如果上下文里没有足够的商品候选，就先调用 query_commodity 获取商品列表，再由模型自己决定后续动作，不要在本地写死购买规则。\n"
        "用户如果是要直接购买或下单，请优先调用 purchase_order，不要先走 add_cart_item、update_cart_item、delete_cart_item 这类购物车步骤；"
        "只有用户明确说要加入购物车时，才使用购物车工具。\n"
        "对于会修改数据的操作（预约、取消预约、报名、取消报名、加购、改购、删购、下单、取消订单），先准备好工具参数，但在提交前要等待用户确认。\n"
        "取消订单时，如果用户没提供订单号，可以把用户原始描述放到 cancel_order 的 query 参数，让工具自动匹配订单候选。\n"
        "你会收到一段“时间锚点”系统消息；涉及今天/明天/昨天时必须严格以该锚点为准，不要自行猜测日期。\n"
        "工具返回结果后，再用自然语言整理成最终回复。\n"
        "如果缺少关键参数，先追问，不要猜。\n"
        "输出时不要使用 Markdown 标记，不要写 **、###、```、> 这些符号。\n"
        "如需分点说明，请使用简短中文和换行，不要输出过长的原始 JSON。"
    )


def _build_context_text(request: ChatRequest) -> str:
    """Turn request metadata into a short context block.
    把请求中的上下文整理成一小段文本。
    """

    lines: list[str] = []
    if request.user_id:
        lines.append(f"user_id: {request.user_id}")
    if request.conversation_id:
        lines.append(f"conversation_id: {request.conversation_id}")
    anchor = _build_time_anchor(request)
    lines.append(f"timezone: {anchor['timezone']}")
    lines.append(f"current_time: {anchor['now']}")
    lines.append(f"today: {anchor['today']}")
    lines.append(f"tomorrow: {anchor['tomorrow']}")
    lines.append(f"yesterday: {anchor['yesterday']}")
    if request.metadata:
        lines.append(f"metadata: {request.metadata}")
    return "\n".join(lines)


def _build_history_text(request: ChatRequest) -> str:
    history = render_chat_history(
        conversation_id=request.conversation_id,
        user_id=request.user_id,
    )
    if not history:
        return ""
    return f"会话历史（按时间顺序）：\n{history}"


def _build_commodity_context_text(request: ChatRequest) -> str:
    """Render the latest commodity query result as model context.
    将最近一次商品查询结果渲染成供模型使用的上下文。
    """

    candidates = _latest_commodity_candidates(request)
    if not candidates:
        return ""

    lines = ["最近一次商品查询结果（仅供模型识别商品，不要原样展示给用户）："]
    for index, candidate in enumerate(candidates[:20], start=1):
        commodity_id = candidate.get("id") or candidate.get("commodityId") or candidate.get("commodity_id")
        commodity_name = _format_commodity_display_name(candidate)
        price = candidate.get("price") or candidate.get("commodityPrice") or candidate.get("commodity_price")
        stock = candidate.get("stock") or candidate.get("commodityStock") or candidate.get("commodity_stock")
        description = candidate.get("description") or candidate.get("commodityDescription") or candidate.get("commodity_description")

        parts = [f"{index}. {commodity_name}"]
        if commodity_id is not None:
            parts.append(f"ID={commodity_id}")
        if price is not None:
            parts.append(f"价格={price}")
        if stock is not None:
            parts.append(f"库存={stock}")
        if description:
            parts.append(f"描述={str(description).strip()[:80]}")
        lines.append("，".join(parts))

    return "\n".join(lines)


def _simplify_commodity_name(name: str) -> str:
    """Strip common size suffixes from a commodity name.
    去掉商品名里常见的规格后缀，便于匹配和展示。
    """

    normalized = re.sub(r"[\s，。！？!?.、,;；:：]+", "", str(name or ""))
    normalized = re.sub(
        r"(?:\d+(?:\.\d+)?(?:kg|g|ml|l|升|毫升|克|斤|磅|oz)|\d+\s*[x×*]\s*\d+)$",
        "",
        normalized,
        flags=re.IGNORECASE,
    )
    return normalized or str(name or "").strip()


def _format_commodity_display_name(item: dict[str, Any]) -> str:
    commodity_name = item.get("display_name") or item.get("name") or item.get("commodityName") or item.get("commodity_name")
    commodity_name = _simplify_commodity_name(str(commodity_name or ""))
    return commodity_name or "未知商品"


def _latest_commodity_candidates(request: ChatRequest) -> list[dict[str, Any]]:
    messages = get_chat_messages(conversation_id=request.conversation_id, user_id=request.user_id)
    for message in reversed(messages):
        if str(message.get("role") or "") != "tool":
            continue
        if str(message.get("tool_name") or "") != "query_commodity":
            continue

        parsed = _parse_tool_result(str(message.get("content") or ""))
        if not parsed:
            continue
        data = parsed.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    return []


def _build_purchase_item_name_lookup(request: ChatRequest) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for candidate in _latest_commodity_candidates(request):
        commodity_id = candidate.get("id") or candidate.get("commodityId") or candidate.get("commodity_id")
        if commodity_id is None:
            continue
        commodity_name = _format_commodity_display_name(candidate)
        if commodity_name and commodity_name != "未知商品":
            lookup[str(commodity_id)] = commodity_name
    return lookup


def _enrich_purchase_items_for_display(
    request: ChatRequest,
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Fill missing purchase item names from the latest commodity query result.
    从最近一次商品查询结果中补全购买条目的商品名。
    """

    if not items:
        return []

    name_lookup = _build_purchase_item_name_lookup(request)
    enriched_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        enriched_item = dict(item)
        commodity_name = _format_commodity_display_name(enriched_item)
        if commodity_name == "未知商品":
            commodity_id = enriched_item.get("id") or enriched_item.get("commodityId") or enriched_item.get("commodity_id")
            if commodity_id is not None:
                commodity_name = name_lookup.get(str(commodity_id), commodity_name)

        if commodity_name and commodity_name != "未知商品":
            enriched_item["display_name"] = commodity_name

        enriched_items.append(enriched_item)

    return enriched_items


def _extract_receiver_info_from_metadata(request: ChatRequest) -> dict[str, str | None]:
    metadata = request.metadata or {}
    name = metadata.get("receiver_name") or metadata.get("receiverName") or metadata.get("contact_name")
    phone = metadata.get("receiver_phone") or metadata.get("receiverPhone") or metadata.get("contact_phone")
    address = metadata.get("receiver_address") or metadata.get("receiverAddress") or metadata.get("shipping_address")
    return {
        "receiver_name": str(name).strip() if name else None,
        "receiver_phone": str(phone).strip() if phone else None,
        "receiver_address": str(address).strip() if address else None,
    }


def _extract_receiver_info_from_history(request: ChatRequest) -> dict[str, str | None]:
    messages = get_chat_messages(conversation_id=request.conversation_id, user_id=request.user_id)
    receiver_name = None
    receiver_phone = None
    receiver_address = None

    name_pattern = re.compile(r"(?:收货人|收件人|联系人|姓名)[:：]?\s*([^\s，,。;；]{2,20})")
    phone_pattern = re.compile(r"(?:手机|手机号|电话)[:：]?\s*(1\d{10})")
    address_pattern = re.compile(r"(?:收货地址|地址)[:：]?\s*([^\n，,。;；]{3,120})")

    for message in reversed(messages):
        if str(message.get("role") or "") != "user":
            continue
        text = str(message.get("content") or "")
        if receiver_name is None:
            match = name_pattern.search(text)
            if match:
                receiver_name = match.group(1).strip()
        if receiver_phone is None:
            match = phone_pattern.search(text)
            if match:
                receiver_phone = match.group(1).strip()
        if receiver_address is None:
            match = address_pattern.search(text)
            if match:
                receiver_address = match.group(1).strip()
        if receiver_name and receiver_phone and receiver_address:
            break

    return {
        "receiver_name": receiver_name,
        "receiver_phone": receiver_phone,
        "receiver_address": receiver_address,
    }


def _extract_receiver_info_from_text(text: str) -> dict[str, str | None]:
    """Extract receiver info from a single user message.
    从单条用户消息中提取收货信息。
    """

    receiver_name = None
    receiver_phone = None
    receiver_address = None

    name_pattern = re.compile(r"(?:收货人|收件人|联系人|姓名)[:：]?\s*([^\s，,。;；]{2,20})")
    phone_pattern = re.compile(r"(?:手机|手机号|电话)[:：]?\s*(1\d{10})")
    address_pattern = re.compile(r"(?:收货地址|地址)[:：]?\s*([^\n，,。;；]{3,120})")

    if text:
        match = name_pattern.search(text)
        if match:
            receiver_name = match.group(1).strip()
        match = phone_pattern.search(text)
        if match:
            receiver_phone = match.group(1).strip()
        match = address_pattern.search(text)
        if match:
            receiver_address = match.group(1).strip()

    # If the user only sends plain text like "张三，138xxxx，广东省..."
    # fall back to simple comma/space splitting.
    if not (receiver_name and receiver_phone and receiver_address):
        chunks = [part.strip() for part in re.split(r"[，,、\n]+", text or "") if part.strip()]
        if chunks:
            if receiver_name is None and len(chunks) >= 1:
                first = chunks[0]
                if 2 <= len(first) <= 20 and not re.search(r"\d", first):
                    receiver_name = first
            if receiver_phone is None:
                for chunk in chunks:
                    phone_match = re.search(r"(1\d{10})", chunk)
                    if phone_match:
                        receiver_phone = phone_match.group(1)
                        break
            if receiver_address is None:
                for chunk in chunks:
                    if receiver_phone and receiver_phone in chunk:
                        continue
                    if len(chunk) >= 6 and any(keyword in chunk for keyword in ["省", "市", "区", "县", "路", "街", "大道", "小区", "号"]):
                        receiver_address = chunk
                        break

    return {
        "receiver_name": receiver_name,
        "receiver_phone": receiver_phone,
        "receiver_address": receiver_address,
    }


def _resolve_receiver_info(request: ChatRequest) -> dict[str, str | None]:
    receiver_info = _extract_receiver_info_from_metadata(request)
    history_info = _extract_receiver_info_from_history(request)
    text_info = _extract_receiver_info_from_text(request.text)
    receiver_info = {
        "receiver_name": receiver_info.get("receiver_name") or history_info.get("receiver_name"),
        "receiver_phone": receiver_info.get("receiver_phone") or history_info.get("receiver_phone"),
        "receiver_address": receiver_info.get("receiver_address") or history_info.get("receiver_address"),
    }
    receiver_info = {
        "receiver_name": receiver_info.get("receiver_name") or text_info.get("receiver_name"),
        "receiver_phone": receiver_info.get("receiver_phone") or text_info.get("receiver_phone"),
        "receiver_address": receiver_info.get("receiver_address") or text_info.get("receiver_address"),
    }

    if receiver_info.get("receiver_name") and receiver_info.get("receiver_phone") and receiver_info.get("receiver_address"):
        return receiver_info

    try:
        profile_result = query_member_profile_service(user_id=request.user_id, auth_token=request.auth_token)
        profile = profile_result.get("data") if profile_result.get("status") == "success" else {}
        if isinstance(profile, dict):
            receiver_info["receiver_name"] = receiver_info.get("receiver_name") or profile.get("realName") or profile.get("nickname")
            receiver_info["receiver_phone"] = receiver_info.get("receiver_phone") or profile.get("phone")
    except Exception:
        pass

    return receiver_info


def _format_purchase_items(items: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        commodity_name = _format_commodity_display_name(item)
        quantity = item.get("quantity") or 1
        lines.append(f"- {index}. {commodity_name} × {quantity}")
    return "\n".join(lines)


def _build_purchase_prompt(
    *,
    items: list[dict[str, Any]],
    receiver_info: dict[str, str | None],
) -> tuple[str, list[str]]:
    missing_fields: list[str] = []
    if not receiver_info.get("receiver_name"):
        missing_fields.append("收货人")
    if not receiver_info.get("receiver_phone"):
        missing_fields.append("联系电话")
    if not receiver_info.get("receiver_address"):
        missing_fields.append("收货地址")

    if missing_fields:
        prompt = (
            "我已经识别到你要购买以下商品，但还缺少下单所需信息：\n"
            f"{_format_purchase_items(items)}\n"
            f"还需要你补充：{'、'.join(missing_fields)}。\n"
            "你补充后我会直接帮你创建订单。"
        )
        return prompt, missing_fields

    prompt = (
        "我已经准备好帮你创建订单，请确认后执行。\n"
        f"{_format_purchase_items(items)}\n"
        f"- 收货人: {receiver_info.get('receiver_name')}\n"
        f"- 联系电话: {receiver_info.get('receiver_phone')}\n"
        f"- 收货地址: {receiver_info.get('receiver_address')}\n"
        "回复“确认”后我就提交。"
    )
    return prompt, missing_fields


def _execute_purchase_order(
    request: ChatRequest,
    *,
    items: list[dict[str, Any]],
    receiver_info: dict[str, str],
) -> tuple[str, list[ChatToolCall], list[str], dict[str, Any] | None]:
    executed_calls: list[ChatToolCall] = []
    used_tools: list[str] = []
    cart_item_ids: list[int] = []
    items = _enrich_purchase_items_for_display(request, items)

    with request_context_scope(
        user_id=request.user_id,
        auth_token=request.auth_token,
        conversation_id=request.conversation_id,
        metadata=request.metadata,
    ):
        for item in items:
            commodity_id = item.get("id") or item.get("commodityId") or item.get("commodity_id")
            commodity_name = _format_commodity_display_name(item)
            quantity = int(item.get("quantity") or 1)
            used_tools.append("add_cart_item")
            add_result = add_cart_item_service(
                commodity_id=str(commodity_id),
                quantity=quantity,
                user_id=request.user_id,
                auth_token=request.auth_token,
            )
            add_result_text = json.dumps(add_result, ensure_ascii=False, default=str)
            executed_calls.append(
                ChatToolCall(
                    name="add_cart_item",
                    arguments={
                        "commodity_id": str(commodity_id),
                        "quantity": quantity,
                        "commodity_name": commodity_name,
                    },
                    result=add_result_text,
                )
            )
            _record_tool_message(
                request,
                tool_name="add_cart_item",
                tool_args={
                    "commodity_id": str(commodity_id),
                    "quantity": quantity,
                    "commodity_name": commodity_name,
                },
                result_text=add_result_text,
            )
            if add_result.get("status") != "success":
                return add_result_text, executed_calls, used_tools, add_result

            cart_data = add_result.get("data") or {}
            cart_item_id = cart_data.get("id") or cart_data.get("cartItemId") or cart_data.get("cart_item_id")
            if cart_item_id is not None:
                cart_item_ids.append(int(cart_item_id))

        used_tools.append("create_order")
        order_result = create_order_service(
            cart_item_ids=cart_item_ids,
            receiver_name=receiver_info["receiver_name"],
            receiver_phone=receiver_info["receiver_phone"],
            receiver_address=receiver_info["receiver_address"],
            user_id=request.user_id,
            auth_token=request.auth_token,
        )
        order_result_text = json.dumps(order_result, ensure_ascii=False, default=str)
        executed_calls.append(
            ChatToolCall(
                name="create_order",
                arguments={
                    "cart_item_ids": cart_item_ids,
                    "receiver_name": receiver_info["receiver_name"],
                    "receiver_phone": receiver_info["receiver_phone"],
                    "receiver_address": receiver_info["receiver_address"],
                },
                result=order_result_text,
            )
        )
        _record_tool_message(
            request,
            tool_name="create_order",
            tool_args={
                "cart_item_ids": cart_item_ids,
                "receiver_name": receiver_info["receiver_name"],
                "receiver_phone": receiver_info["receiver_phone"],
                "receiver_address": receiver_info["receiver_address"],
            },
            result_text=order_result_text,
        )
        return order_result_text, executed_calls, used_tools, order_result


def _parse_tool_result(result_text: str) -> dict[str, Any] | None:
    """Parse a tool result when it is a JSON payload.
    当 tool 返回 JSON 字符串时，解析成字典。
    """

    try:
        parsed = json.loads(result_text)
    except Exception:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def _recover_answer_from_tool_calls(
    *,
    executed_tool_calls: list[ChatToolCall],
    request: ChatRequest,
) -> str | None:
    """Recover a final answer from executed tool payloads when LLM loop does not converge.
    当 LLM 工具循环未收敛时，从已执行工具结果中恢复最终回复。
    """

    for call in reversed(executed_tool_calls):
        parsed = _parse_tool_result(call.result)
        if not parsed:
            continue

        if call.name == "rag_search":
            data = parsed.get("data")
            if isinstance(data, dict):
                answer = str(data.get("answer") or "").strip()
                if answer:
                    return _normalize_and_guard_answer(answer, request)

        message = str(parsed.get("message") or "").strip()
        if parsed.get("status") == "error" and message:
            return _polish_tool_error(call.name, parsed, request)
        if parsed.get("status") == "success" and message and message not in {"knowledge answer generated"}:
            return _normalize_and_guard_answer(message, request)
    return None


def _extract_backend_reason(payload: dict[str, Any]) -> str:
    """Extract the business reason from a backend/tool error payload.
    从后端或工具错误里提取真正的业务原因。
    """

    message = str(payload.get("message") or "").strip()
    details = payload.get("details") or {}
    response_text = str(details.get("response_text") or "").strip()

    if response_text:
        try:
            response_payload = json.loads(response_text)
        except Exception:
            response_payload = None
        if isinstance(response_payload, dict):
            response_message = str(response_payload.get("message") or "").strip()
            if response_message:
                return response_message

    if ": " in message:
        return message.rsplit(": ", 1)[-1].strip()
    return message or "操作失败"


def _safe_int_code(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _fallback_tool_error_text(tool_name: str, payload: dict[str, Any]) -> str:
    """Build a safe Chinese fallback when the LLM cannot polish an error.
    当模型不可用时，生成不会暴露后端细节的中文兜底提示。
    """

    code = _safe_int_code(payload.get("code"))
    reason = _extract_backend_reason(payload)
    reason_key = reason.lower()

    if code == 401 or "login required" in reason_key or "unauthorized" in reason_key:
        return "当前登录已失效或还没有登录，请重新登录后再试。"
    if code == 403 or "forbidden" in reason_key or "only cancel your own" in reason_key:
        if tool_name == "cancel_enrollment":
            return "只能取消您自己的课程报名，当前这条报名无法操作。"
        if tool_name == "cancel_booking":
            return "只能取消您自己的预约，当前这条预约无法操作。"
        if tool_name == "cancel_order":
            return "只能取消您自己的订单，当前这笔订单无法操作。"
        return "当前账号没有权限执行这次操作。"
    if code == 503:
        return "服务暂时不可用，这次操作没有完成，请稍后再试。"
    if code and code >= 500:
        return "服务暂时出了点问题，这次操作没有完成，请稍后再试。"

    known_reasons = {
        "course that has started cannot be canceled": "这门课程已经开始或结束，无法取消报名。",
        "current course enrollment cannot be canceled": "当前课程报名状态不支持取消，可能已经取消或已完成。",
        "course enrollment does not exist": "没有找到对应的课程报名记录，请确认后再试。",
        "enrollment not found for the given identifier": "没有找到对应的课程报名记录，请确认报名编号后再试。",
        "matched enrollment is missing id": "已找到课程报名，但缺少必要的报名编号，暂时无法取消。",
        "booking that has started cannot be canceled": "这个预约已经开始或结束，无法取消。",
        "current booking cannot be canceled": "当前预约状态不支持取消，可能已经取消或已完成。",
        "booking does not exist": "没有找到对应的预约记录，请确认后再试。",
        "order not found": "没有找到对应的订单，请确认订单号后再试。",
        "current order cannot be canceled": "当前订单状态不支持取消，可能已经支付、取消或完成。",
        "no cancellable unpaid orders found": "没有找到可以取消的未支付订单。",
    }
    for key, text in known_reasons.items():
        if key in reason_key:
            return text

    if tool_name == "cancel_enrollment":
        return "课程报名取消失败，当前报名可能不满足取消条件。"
    if tool_name == "cancel_booking":
        return "预约取消失败，当前预约可能不满足取消条件。"
    if tool_name == "cancel_order":
        return "订单取消失败，当前订单可能不满足取消条件。"
    if tool_name == "create_order":
        return "订单创建失败，请检查商品和收货信息后再试。"
    return "这次操作没有完成，请检查信息后再试。"


def _contains_backend_leak(text: str) -> bool:
    lowered = text.lower()
    leak_terms = [
        "java backend",
        "backend",
        "http",
        "post ",
        "get ",
        "put ",
        "delete ",
        "/courses/",
        "/gym/",
        "/orders/",
        "apiresponse",
        "json",
        "traceback",
        "exception",
        "java",
        "后端",
        "接口",
        "请求方法",
        "接口路径",
    ]
    return any(term in lowered for term in leak_terms)


def _polish_tool_error(tool_name: str, payload: dict[str, Any], request: ChatRequest) -> str:
    """Ask the LLM to rewrite a tool/backend error for the user.
    让大模型把工具/后端错误改写成面向用户的自然语言。
    """

    fallback = _fallback_tool_error_text(tool_name, payload)
    if not deepseek_is_configured():
        return _normalize_and_guard_answer(fallback, request)

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
    except ImportError:
        return _normalize_and_guard_answer(fallback, request)

    reason = _extract_backend_reason(payload)
    details = payload.get("details") or {}
    compact_payload = {
        "tool_name": tool_name,
        "domain": payload.get("domain"),
        "operation": payload.get("operation"),
        "source": payload.get("source"),
        "code": payload.get("code"),
        "raw_message": str(payload.get("message") or "")[:1000],
        "business_reason": reason[:500],
        "response_text": str(details.get("response_text") or "")[:1000],
        "safe_fallback": fallback,
        "user_text": request.text,
    }

    try:
        llm = get_deepseek_chat_model()
        ai_message = llm.invoke(
            [
                SystemMessage(
                    content=(
                        "你是健身系统的中文客服助手。现在你会收到一次工具或后端业务错误。"
                        "请把它改写成自然、简短、面向用户的中文回复。\n"
                        "要求：\n"
                        "1. 不要输出 Java、backend、HTTP、接口路径、请求方法、JSON、异常栈等技术细节。\n"
                        "2. 不要说操作已经成功；只能说明没有完成以及用户能理解的原因。\n"
                        "3. 如果原因是课程/预约/订单已经开始、结束或状态不允许取消，要直接说明无法取消。\n"
                        "4. 最多两句话，不使用 Markdown。"
                    )
                ),
                HumanMessage(
                    content=(
                        "请润色下面的错误信息，直接返回要展示给用户的文字：\n"
                        f"{json.dumps(compact_payload, ensure_ascii=False)}"
                    )
                ),
            ]
        )
        polished = _normalize_and_guard_answer(str(ai_message.content or ""), request)
        if not polished or _contains_backend_leak(polished):
            return _normalize_and_guard_answer(fallback, request)
        return polished
    except Exception as exc:
        print(f"[agent] tool error polish failed: tool={tool_name} error={exc}")
        return _normalize_and_guard_answer(fallback, request)


def _normalize_answer_text(text: str) -> str:
    """Make model output easier to read in a plain-text chat UI.
    将模型输出整理成更适合纯文本聊天界面的样式。

    The current UI renders assistant messages as plain text, so markdown
    markers like `**`, `###`, and code fences would appear literally.
    当前 UI 直接以纯文本渲染消息，因此 `**`、`###`、代码块等 Markdown 标记会原样显示。
    This helper strips the most common markers while keeping line breaks.
    这里做一次轻量清洗，去掉常见标记，同时保留换行和列表结构。
    """

    if not text:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.replace("```", "")

    cleaned_lines: list[str] = []
    for raw_line in normalized.split("\n"):
        line = raw_line.strip()
        if not line:
            cleaned_lines.append("")
            continue

        line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
        line = re.sub(r"^\s*>\s*", "", line)
        line = re.sub(r"^\s*[-*+]\s+", "• ", line)
        line = re.sub(r"^\s*(\d+)[.)]\s+", r"\1. ", line)
        line = re.sub(r"(\*\*|__)(.+?)\1", r"\2", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)
        line = re.sub(r"\s{2,}", " ", line)
        cleaned_lines.append(line)

    collapsed: list[str] = []
    previous_blank = False
    for line in cleaned_lines:
        if not line:
            if not previous_blank:
                collapsed.append("")
            previous_blank = True
            continue
        collapsed.append(line)
        previous_blank = False

    return "\n".join(collapsed).strip()


def _apply_date_anchor_guard(answer_text: str, request: ChatRequest) -> str:
    """Append a correction when generated relative-date statements conflict with anchor time.
    当模型给出的相对日期和时间锚点冲突时，追加纠正说明。
    """

    text = answer_text or ""
    anchor = _build_time_anchor(request)
    expected_today = anchor["today"]
    expected_tomorrow = anchor["tomorrow"]

    mismatch = False

    today_match = re.search(r"今天(?:是|为)\s*(\d{4})[年\-/\.](\d{1,2})[月\-/\.](\d{1,2})", text)
    if today_match:
        parsed_today = f"{int(today_match.group(1)):04d}-{int(today_match.group(2)):02d}-{int(today_match.group(3)):02d}"
        mismatch = parsed_today != expected_today

    tomorrow_match = re.search(r"明天(?:是|为|应该是)?\s*(\d{1,2})月(\d{1,2})日", text)
    if tomorrow_match:
        parsed_tomorrow = f"{expected_today[:5]}{int(tomorrow_match.group(1)):02d}-{int(tomorrow_match.group(2)):02d}"
        mismatch = mismatch or (parsed_tomorrow != expected_tomorrow)

    if not mismatch:
        return text

    correction = (
        f"更正：按{anchor['timezone']}时间，今天是{expected_today}，明天是{expected_tomorrow}。"
    )
    if correction in text:
        return text
    return f"{text}\n{correction}".strip()


def _normalize_and_guard_answer(text: str, request: ChatRequest) -> str:
    normalized = _normalize_answer_text(text)
    return _apply_date_anchor_guard(normalized, request)


def _normalize_confirmation_text(text: str) -> str:
    return re.sub(r"[\s，。！？!?.]+", "", text.strip())


def _is_confirmation_text(text: str) -> bool:
    return bool(_CONFIRMATION_RE.match(_normalize_confirmation_text(text)))


def _is_write_tool(tool_name: str) -> bool:
    return tool_name in _WRITE_TOOL_NAMES


def _get_tool(tool_name: str):
    return next((tool for tool in get_gym_tools() if tool.name == tool_name), None)


def _record_user_message(request: ChatRequest, text: str) -> None:
    append_chat_message(
        conversation_id=request.conversation_id,
        user_id=request.user_id,
        role="user",
        content=text,
    )


def _record_assistant_message(request: ChatRequest, text: str) -> None:
    append_chat_message(
        conversation_id=request.conversation_id,
        user_id=request.user_id,
        role="assistant",
        content=text,
    )


def _record_tool_message(
    request: ChatRequest,
    *,
    tool_name: str,
    tool_args: dict[str, Any],
    result_text: str,
    tool_call_id: str | None = None,
) -> None:
    append_chat_message(
        conversation_id=request.conversation_id,
        user_id=request.user_id,
        role="tool",
        content=result_text,
        tool_name=tool_name,
        tool_args=tool_args,
        tool_call_id=tool_call_id,
    )


def _format_pending_confirmation(tool_name: str, tool_args: dict[str, Any]) -> str:
    if tool_name == "purchase_order":
        items = tool_args.get("purchase_items") or []
        receiver_name = tool_args.get("receiver_name")
        receiver_phone = tool_args.get("receiver_phone")
        receiver_address = tool_args.get("receiver_address")
        summary = []
        if isinstance(items, list) and items:
            summary.append("我已经准备好帮你创建订单，请确认后执行。")
            summary.append("商品如下：")
            for index, item in enumerate(items, start=1):
                if not isinstance(item, dict):
                    continue
                commodity_name = _format_commodity_display_name(item)
                quantity = item.get("quantity") or 1
                summary.append(f"- {index}. {commodity_name} × {quantity}")
        if receiver_name:
            summary.append(f"- 收货人: {receiver_name}")
        if receiver_phone:
            summary.append(f"- 联系电话: {receiver_phone}")
        if receiver_address:
            summary.append(f"- 收货地址: {receiver_address}")
        summary.append("回复“确认”后我就提交。")
        return "\n".join(summary)
    if tool_name == "create_booking":
        return (
            "我已经准备好帮你创建预约，请确认后执行。\n"
            f"- 场地ID: {tool_args.get('gym_room_id')}\n"
            f"- 开始时间: {tool_args.get('start_time')}\n"
            f"- 结束时间: {tool_args.get('end_time')}\n"
            f"- 人数: {tool_args.get('head_count')}\n"
            f"- 备注: {tool_args.get('remark') or '无'}\n"
            "回复“确认”后我就提交。"
        )
    if tool_name == "enroll_course":
        return (
            "我已经准备好帮你报名课程，请确认后执行。\n"
            f"- 课程ID: {tool_args.get('course_id')}\n"
            "回复“确认”后我就提交。"
        )
    if tool_name == "create_order":
        return (
            "我已经准备好帮你创建订单，订单会以未支付状态提交，请确认后执行。\n"
            f"- 购物车条目: {tool_args.get('cart_item_ids')}\n"
            f"- 收货人: {tool_args.get('receiver_name')}\n"
            f"- 联系电话: {tool_args.get('receiver_phone')}\n"
            f"- 收货地址: {tool_args.get('receiver_address')}\n"
            "回复“确认”后我就提交。"
        )
    if tool_name == "add_cart_item":
        commodity_name = tool_args.get("commodity_name") or tool_args.get("display_name") or "该商品"
        return (
            "我已经准备好帮你把商品加入购物车，请确认后执行。\n"
            f"- 商品: {commodity_name}\n"
            f"- 数量: {tool_args.get('quantity')}\n"
            "回复“确认”后我就提交。"
        )
    if tool_name == "update_cart_item":
        return (
            "我已经准备好帮你更新购物车，请确认后执行。\n"
            f"- 购物车条目ID: {tool_args.get('cart_item_id')}\n"
            f"- 数量: {tool_args.get('quantity')}\n"
            f"- 是否选中: {tool_args.get('selected')}\n"
            "回复“确认”后我就提交。"
        )
    if tool_name == "delete_cart_item":
        return (
            "我已经准备好帮你删除购物车条目，请确认后执行。\n"
            f"- 购物车条目ID: {tool_args.get('cart_item_id')}\n"
            "回复“确认”后我就提交。"
        )
    if tool_name == "cancel_booking":
        return (
            "我已经准备好帮你取消预约，请确认后执行。\n"
            f"- 预约标识: {tool_args.get('booking_identifier') or tool_args.get('booking_id') or tool_args.get('booking_no')}\n"
            "回复“确认”后我就提交。"
        )
    if tool_name == "cancel_enrollment":
        return (
            "我已经准备好帮你取消课程报名，请确认后执行。\n"
            f"- 报名标识: {tool_args.get('enrollment_identifier') or tool_args.get('enrollment_id') or tool_args.get('enrollment_no')}\n"
            "回复“确认”后我就提交。"
        )
    if tool_name == "cancel_order":
        query_text = str(tool_args.get("query") or "").strip()
        lines = [
            "我已经准备好帮你取消订单，请确认后执行。",
            f"- 订单标识: {tool_args.get('order_identifier') or tool_args.get('order_id') or tool_args.get('order_no')}",
        ]
        if query_text:
            lines.append(f"- 订单描述: {query_text}")
        lines.append("回复“确认”后我就提交。")
        return "\n".join(lines)
    return f"我已经准备好执行工具 {tool_name}，请确认后继续。"


def _format_write_success(tool_name: str, payload: dict[str, Any]) -> str:
    data = payload.get("data")
    if tool_name == "purchase_order":
        tool_name = "create_order"
    if tool_name == "create_booking" and isinstance(data, dict):
        booking_no = data.get("bookingNo") or data.get("booking_no")
        gym_room_name = data.get("gymRoomName") or data.get("gym_room_name")
        start_time = data.get("startTime") or data.get("start_time")
        end_time = data.get("endTime") or data.get("end_time")
        return (
            "预约已提交成功。"
            + (f" 预约号：{booking_no}。" if booking_no else "")
            + (f" 场地：{gym_room_name}。" if gym_room_name else "")
            + (f" 时间：{start_time} - {end_time}。" if start_time and end_time else "")
        )
    if tool_name == "enroll_course" and isinstance(data, dict):
        enrollment_no = data.get("enrollmentNo") or data.get("enrollment_no")
        course_name = data.get("courseName") or data.get("course_name")
        return (
            "课程报名已成功。"
            + (f" 报名号：{enrollment_no}。" if enrollment_no else "")
            + (f" 课程：{course_name}。" if course_name else "")
        )
    if tool_name == "create_order" and isinstance(data, dict):
        order_id = data.get("id") or data.get("orderId") or data.get("order_id")
        order_no = data.get("orderNo") or data.get("order_no")
        if not order_no and not order_id:
            return "下单结果不完整：未返回订单号。请稍后查询订单列表确认是否创建成功。"
        order_status = data.get("status") or data.get("order_status")
        payment_status = data.get("paymentStatus") or data.get("payment_status")
        pay_amount = data.get("payAmount") or data.get("pay_amount")
        receiver_name = data.get("receiverName") or data.get("receiver_name")
        receiver_phone = data.get("receiverPhone") or data.get("receiver_phone")
        receiver_address = data.get("receiverAddress") or data.get("receiver_address")
        created_at = data.get("createdAt") or data.get("created_at")
        payment_text = "未支付" if str(payment_status).upper() == "UNPAID" else str(payment_status or "未知")
        lines = ["订单已创建成功，以下是订单详情："]
        if order_no:
            lines.append(f"- 订单号：{order_no}")
        elif order_id:
            lines.append(f"- 订单ID：{order_id}")
        if order_status:
            lines.append(f"- 订单状态：{order_status}")
        lines.append(f"- 支付状态：{payment_text}")
        if pay_amount is not None:
            lines.append(f"- 金额：{pay_amount}")
        if receiver_name:
            lines.append(f"- 收货人：{receiver_name}")
        if receiver_phone:
            lines.append(f"- 联系电话：{receiver_phone}")
        if receiver_address:
            lines.append(f"- 收货地址：{receiver_address}")
        if created_at:
            lines.append(f"- 创建时间：{created_at}")

        items = data.get("items")
        if isinstance(items, list) and items:
            lines.append("- 商品明细：")
            for index, item in enumerate(items, start=1):
                if not isinstance(item, dict):
                    continue
                commodity_name = item.get("commodityNameSnapshot") or item.get("commodity_name_snapshot") or "未知商品"
                quantity = item.get("quantity")
                unit_price = item.get("unitPrice") or item.get("unit_price")
                subtotal = item.get("subtotalAmount") or item.get("subtotal_amount")
                detail_parts = [f"{index}. {commodity_name}"]
                if quantity is not None:
                    detail_parts.append(f"数量 {quantity}")
                if unit_price is not None:
                    detail_parts.append(f"单价 {unit_price}")
                if subtotal is not None:
                    detail_parts.append(f"小计 {subtotal}")
                lines.append("- " + "，".join(detail_parts))

        lines.append("请尽快完成支付，避免订单被系统取消。")
        return "\n".join(lines)
    if tool_name == "add_cart_item" and isinstance(data, dict):
        return "商品已加入购物车。"
    if tool_name == "update_cart_item" and isinstance(data, dict):
        return "购物车已更新。"
    if tool_name == "delete_cart_item" and isinstance(data, dict):
        return "购物车条目已删除。"
    if tool_name == "cancel_booking":
        return "预约已取消。"
    if tool_name == "cancel_enrollment":
        return "课程报名已取消。"
    if tool_name == "cancel_order":
        if isinstance(data, dict):
            order_no = data.get("orderNo") or data.get("order_no")
            if order_no:
                return f"订单已取消。订单号：{order_no}。"
        return "订单已取消。"
    return "操作已完成。"


def _execute_tool_call(
    tool_name: str,
    tool_args: dict[str, Any],
    request: ChatRequest | None = None,
) -> tuple[str, dict[str, Any] | None]:
    selected_tool = _get_tool(tool_name)
    if selected_tool is None:
        return f"未找到工具：{tool_name}", None

    if request is None:
        result_text = str(selected_tool.invoke(tool_args))
    else:
        with request_context_scope(
            user_id=request.user_id,
            auth_token=request.auth_token,
            conversation_id=request.conversation_id,
            metadata=request.metadata,
        ):
            result_text = str(selected_tool.invoke(tool_args))
    parsed_result = _parse_tool_result(result_text)
    return result_text, parsed_result


def _parse_cn_number(value: Any) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    if text in _CN_NUMBER_MAP:
        return _CN_NUMBER_MAP[text]
    if text == "十":
        return 10
    if text.startswith("十"):
        tail = _parse_cn_number(text[1:])
        return 10 + (tail or 0)
    if "十" in text:
        head_text, tail_text = text.split("十", 1)
        head = _parse_cn_number(head_text) or 1
        tail = _parse_cn_number(tail_text) if tail_text else 0
        return head * 10 + (tail or 0)
    return None


def _normalize_hour(hour: int, period: str | None) -> int:
    if period in {"下午", "晚上"} and 1 <= hour < 12:
        return hour + 12
    if period == "中午" and 1 <= hour < 11:
        return hour + 12
    return hour


def _extract_booking_time_range(text: str, request: ChatRequest) -> tuple[datetime, datetime] | None:
    match = re.search(
        r"(?P<period>上午|下午|晚上|中午)?\s*"
        r"(?P<start>[零〇一二两三四五六七八九十\d]{1,3})\s*(?:点|时)"
        r"(?P<start_half>半)?(?:(?P<start_minute>\d{1,2})\s*分?)?\s*"
        r"(?:到|至|-|~|—)\s*"
        r"(?P<end_period>上午|下午|晚上|中午)?\s*"
        r"(?P<end>[零〇一二两三四五六七八九十\d]{1,3})\s*(?:点|时)"
        r"(?P<end_half>半)?(?:(?P<end_minute>\d{1,2})\s*分?)?",
        text,
    )
    if not match:
        return None

    start_hour = _parse_cn_number(match.group("start"))
    end_hour = _parse_cn_number(match.group("end"))
    if start_hour is None or end_hour is None:
        return None

    period = match.group("period")
    end_period = match.group("end_period") or period
    start_hour = _normalize_hour(start_hour, period)
    end_hour = _normalize_hour(end_hour, end_period)
    start_minute = 30 if match.group("start_half") else int(match.group("start_minute") or 0)
    end_minute = 30 if match.group("end_half") else int(match.group("end_minute") or 0)

    anchor = _build_time_anchor(request)
    date_text = anchor["today"]
    if "明天" in text:
        date_text = anchor["tomorrow"]
    elif "昨天" in text:
        date_text = anchor["yesterday"]

    start_at = datetime.strptime(f"{date_text} {start_hour:02d}:{start_minute:02d}:00", "%Y-%m-%d %H:%M:%S")
    end_at = datetime.strptime(f"{date_text} {end_hour:02d}:{end_minute:02d}:00", "%Y-%m-%d %H:%M:%S")
    if end_at <= start_at:
        end_at = end_at + timedelta(days=1)
    return start_at, end_at


def _extract_head_count(text: str) -> int | None:
    match = re.search(r"([零〇一二两三四五六七八九十\d]{1,3})\s*(?:个人|人位|人)", text)
    if not match:
        return None
    return _parse_cn_number(match.group(1))


def _latest_room_id_from_history(text: str, request: ChatRequest) -> str | None:
    messages = get_chat_messages(conversation_id=request.conversation_id, user_id=request.user_id)
    for message in reversed(messages):
        if getattr(message, "role", None) != "tool" and message.get("role") != "tool":
            continue
        content = getattr(message, "content", None) if not isinstance(message, dict) else message.get("content")
        try:
            payload = json.loads(str(content or ""))
        except Exception:
            continue
        data = payload.get("data") if isinstance(payload, dict) else None
        rooms = data if isinstance(data, list) else []
        for room in rooms:
            if not isinstance(room, dict):
                continue
            room_name = str(room.get("name") or room.get("roomName") or "").strip()
            room_id = room.get("id") or room.get("roomId") or room.get("gymRoomId")
            if room_name and room_id is not None and room_name in text:
                return str(room_id)
    return None


def _extract_gym_room_id(text: str, request: ChatRequest) -> str | None:
    match = re.search(r"([零〇一二两三四五六七八九十\d]{1,3})\s*(?:号|#)\s*(?:训练室|教室|房|健身房|场地)?", text)
    if match:
        room_number = _parse_cn_number(match.group(1))
        if room_number is not None:
            return str(room_number)
    return _latest_room_id_from_history(text, request)


def _maybe_prepare_booking_confirmation(request: ChatRequest, text: str) -> ChatResponse | None:
    if not _BOOKING_INTENT_RE.search(text):
        return None

    gym_room_id = _extract_gym_room_id(text, request)
    time_range = _extract_booking_time_range(text, request)
    head_count = _extract_head_count(text)
    if not gym_room_id or not time_range or not head_count:
        return None

    start_at, end_at = time_range
    timezone_name = _resolve_timezone_name(request)
    now = datetime.now(ZoneInfo(timezone_name)).replace(tzinfo=None)
    if start_at <= now:
        answer_text = (
            f"这个开始时间已经过了。当前时间是 {now.strftime('%Y-%m-%d %H:%M:%S')}，"
            "请换一个未来的预约时段。"
        )
        _record_assistant_message(request, answer_text)
        return ChatResponse(
            answer=answer_text,
            tool_calls=[],
            used_tools=[],
            workflow_state="awaiting_information",
        )

    tool_args = {
        "gym_room_id": gym_room_id,
        "start_time": start_at.strftime("%Y-%m-%d %H:%M:%S"),
        "end_time": end_at.strftime("%Y-%m-%d %H:%M:%S"),
        "head_count": head_count,
        "remark": "Agent 预约",
        "user_id": request.user_id,
    }
    pending = store_pending_action(
        conversation_id=request.conversation_id,
        user_id=request.user_id,
        action={
            "tool_name": "create_booking",
            "tool_args": tool_args,
            "original_text": text,
        },
    )
    confirmation_prompt = _format_pending_confirmation("create_booking", tool_args)
    _record_assistant_message(request, confirmation_prompt)
    return ChatResponse(
        answer=confirmation_prompt,
        tool_calls=[
            ChatToolCall(
                name="create_booking",
                arguments=tool_args,
                result="pending confirmation",
            )
        ],
        used_tools=[],
        workflow_state="awaiting_confirmation",
        requires_confirmation=True,
        confirmation_prompt=confirmation_prompt,
        pending_action=pending,
    )


def _maybe_handle_knowledge_request(
    *,
    request: ChatRequest,
    text: str,
) -> ChatResponse | None:
    """Route clear knowledge questions to RAG before business tool loop.
    在业务工具循环前，将明确知识问题优先路由到 RAG。
    """

    try:
        analysis = analyze_intent(
            IntentAnalysisRequest(
                text=text,
                user_id=request.user_id,
                conversation_id=request.conversation_id,
                metadata=request.metadata,
            )
        )
    except Exception as exc:
        print(f"[agent] intent analysis failed, fallback to tool loop: {exc}")
        return None

    intent_name = str(analysis.intent or "")
    tool_name = str(analysis.tool_name or "")
    category = str(analysis.category or "")
    confidence = float(analysis.confidence or 0.0)

    print(
        "[agent] intent analysis result: "
        f"category={category} intent={intent_name} tool={tool_name} confidence={confidence:.2f}"
    )

    if category != "knowledge":
        return None
    if tool_name and tool_name not in _KNOWLEDGE_TOOL_NAMES and not intent_name.startswith("knowledge."):
        return None
    if confidence < 0.35:
        # Confidence too low, let the regular tool-calling flow decide.
        return None

    rag_result = answer_knowledge_question(question=text)
    print(
        "[agent] rag result: "
        f"answer_cache_hit={bool(rag_result.get('from_cache'))} "
        f"retrieval_cache_hit={bool(rag_result.get('retrieval_from_cache'))} "
        f"retrieval_strategy={rag_result.get('retrieval_strategy')} "
        f"generation_mode={rag_result.get('generation_mode')} "
        f"hits={len(rag_result.get('hits') or [])}"
    )
    answer_text = _normalize_and_guard_answer(str(rag_result.get("answer") or ""), request)
    tool_result_text = json.dumps(
        {
            "status": "success",
            "domain": "knowledge",
            "operation": "rag_search",
            "data": rag_result,
        },
        ensure_ascii=False,
        default=str,
    )
    executed_tool_calls = [
        ChatToolCall(
            name="rag_search",
            arguments={"query": text},
            result=tool_result_text,
        )
    ]
    _record_tool_message(
        request,
        tool_name="rag_search",
        tool_args={"query": text},
        result_text=tool_result_text,
    )
    _record_assistant_message(request, answer_text)
    return ChatResponse(
        answer=answer_text,
        tool_calls=executed_tool_calls,
        used_tools=["rag_search"],
        workflow_state="completed",
    )


def run_tool_calling_chat(request: ChatRequest) -> ChatResponse:
    """Run a LangChain tool-calling loop.
    执行一轮 LangChain 工具调用循环。
    """

    text = request.text.strip()
    print(
        "[agent] chat flow start: "
        f"user_id={request.user_id} conversation_id={request.conversation_id} "
        f"text='{text[:80]}' auth={'yes' if request.auth_token else 'no'}"
    )
    if not text:
        raise ValueError("text must not be empty")

    if not request.auth_token:
        print("[agent] chat flow aborted: missing auth token")
        return ChatResponse(
            answer="请先登录后再查询系统信息。",
            tool_calls=[],
            used_tools=[],
            workflow_state="completed",
        )

    history_text = _build_history_text(request)
    _record_user_message(request, text)

    pending_action = get_pending_action(conversation_id=request.conversation_id, user_id=request.user_id)
    if pending_action:
        action = pending_action.get("action") or {}
        tool_name = str(action.get("tool_name") or "")
        tool_args = dict(action.get("tool_args") or {})

        if tool_name == "purchase_order":
            purchase_items = _enrich_purchase_items_for_display(request, list(tool_args.get("purchase_items") or []))
            if purchase_items:
                receiver_info = {
                    "receiver_name": str(tool_args.get("receiver_name") or ""),
                    "receiver_phone": str(tool_args.get("receiver_phone") or ""),
                    "receiver_address": str(tool_args.get("receiver_address") or ""),
                }
                current_receiver_info = _resolve_receiver_info(request)
                receiver_info = {
                    "receiver_name": receiver_info.get("receiver_name") or current_receiver_info.get("receiver_name"),
                    "receiver_phone": receiver_info.get("receiver_phone") or current_receiver_info.get("receiver_phone"),
                    "receiver_address": receiver_info.get("receiver_address") or current_receiver_info.get("receiver_address"),
                }
                missing_fields: list[str] = []
                if not receiver_info.get("receiver_name"):
                    missing_fields.append("收货人")
                if not receiver_info.get("receiver_phone"):
                    missing_fields.append("联系电话")
                if not receiver_info.get("receiver_address"):
                    missing_fields.append("收货地址")

                if _is_confirmation_text(text):
                    print(
                        "[agent] chat flow pending purchase confirmed: "
                        f"conversation_id={request.conversation_id} items={len(purchase_items)}"
                    )
                    clear_pending_action(conversation_id=request.conversation_id, user_id=request.user_id)
                    result_text, executed_tool_calls, used_tools, parsed_result = _execute_purchase_order(
                        request,
                        items=purchase_items,
                        receiver_info={
                            "receiver_name": str(receiver_info.get("receiver_name") or ""),
                            "receiver_phone": str(receiver_info.get("receiver_phone") or ""),
                            "receiver_address": str(receiver_info.get("receiver_address") or ""),
                        },
                    )
                    if parsed_result is None and result_text.startswith("未找到工具："):
                        _record_assistant_message(request, result_text)
                        return ChatResponse(
                            answer=result_text,
                            tool_calls=executed_tool_calls,
                            used_tools=used_tools,
                            workflow_state="completed",
                        )
                    if parsed_result and parsed_result.get("status") == "error":
                        print(
                            "[agent] chat flow tool error polished after confirmation: "
                            f"tool=create_order code={parsed_result.get('code')}"
                        )
                        answer_text = _polish_tool_error("create_order", parsed_result, request)
                        _record_assistant_message(request, answer_text)
                        return ChatResponse(
                            answer=answer_text,
                            tool_calls=executed_tool_calls,
                            used_tools=used_tools,
                            workflow_state="completed",
                        )

                    print(
                        "[agent] chat flow pending purchase executed: "
                        f"conversation_id={request.conversation_id} items={len(purchase_items)} "
                        f"result_length={len(result_text)}"
                    )
                    answer_text = _format_write_success("purchase_order", parsed_result or {})
                    _record_assistant_message(request, answer_text)
                    return ChatResponse(
                        answer=answer_text,
                        tool_calls=executed_tool_calls,
                        used_tools=used_tools,
                        workflow_state="completed",
                    )

                if any(_extract_receiver_info_from_text(text).values()) or missing_fields:
                    prompt, prompt_missing_fields = _build_purchase_prompt(
                        items=purchase_items,
                        receiver_info=receiver_info,
                    )
                    if prompt_missing_fields:
                        updated_pending = store_pending_action(
                            conversation_id=request.conversation_id,
                            user_id=request.user_id,
                            action={
                                "tool_name": "purchase_order",
                                "tool_args": {
                                    "purchase_items": purchase_items,
                                    "receiver_name": receiver_info.get("receiver_name"),
                                    "receiver_phone": receiver_info.get("receiver_phone"),
                                    "receiver_address": receiver_info.get("receiver_address"),
                                },
                                "original_text": action.get("original_text") or text,
                                "missing_fields": prompt_missing_fields,
                            },
                        )
                        _record_assistant_message(request, prompt)
                        return ChatResponse(
                            answer=prompt,
                            tool_calls=[],
                            used_tools=[],
                            workflow_state="awaiting_information",
                            requires_confirmation=False,
                            pending_action=updated_pending,
                        )

                    updated_pending = store_pending_action(
                        conversation_id=request.conversation_id,
                        user_id=request.user_id,
                        action={
                            "tool_name": "purchase_order",
                            "tool_args": {
                                "purchase_items": purchase_items,
                                "receiver_name": receiver_info.get("receiver_name"),
                                "receiver_phone": receiver_info.get("receiver_phone"),
                                "receiver_address": receiver_info.get("receiver_address"),
                            },
                            "original_text": action.get("original_text") or text,
                            "missing_fields": [],
                        },
                    )
                    prompt, _ = _build_purchase_prompt(items=purchase_items, receiver_info=receiver_info)
                    _record_assistant_message(request, prompt)
                    return ChatResponse(
                        answer=prompt,
                        tool_calls=[],
                        used_tools=[],
                        workflow_state="awaiting_confirmation",
                        requires_confirmation=True,
                        confirmation_prompt=prompt,
                        pending_action=updated_pending,
                    )

                prompt, _ = _build_purchase_prompt(
                    items=purchase_items,
                    receiver_info=receiver_info,
                )
                _record_assistant_message(request, prompt)
                return ChatResponse(
                    answer=prompt,
                    tool_calls=[],
                    used_tools=[],
                    workflow_state="awaiting_confirmation" if not missing_fields else "awaiting_information",
                    requires_confirmation=not missing_fields,
                    confirmation_prompt=prompt if not missing_fields else None,
                    pending_action=pending_action,
                )

        if tool_name:
            confirmation_prompt = _format_pending_confirmation(tool_name, tool_args)
            if not _is_confirmation_text(text):
                _record_assistant_message(request, confirmation_prompt)
                return ChatResponse(
                    answer=confirmation_prompt,
                    tool_calls=[],
                    used_tools=[],
                    workflow_state="awaiting_confirmation",
                    requires_confirmation=True,
                    confirmation_prompt=confirmation_prompt,
                    pending_action=pending_action,
                )

            print(
                "[agent] chat flow pending write confirmed: "
                f"conversation_id={request.conversation_id} tool={tool_name}"
            )
            clear_pending_action(conversation_id=request.conversation_id, user_id=request.user_id)
            result_text, parsed_result = _execute_tool_call(tool_name, dict(tool_args), request=request)
            executed_tool_calls = [
                ChatToolCall(
                    name=tool_name,
                    arguments=dict(tool_args),
                    result=result_text,
                )
            ]
            used_tools = [tool_name]
            _record_tool_message(
                request,
                tool_name=tool_name,
                tool_args=dict(tool_args),
                result_text=result_text,
            )
            if parsed_result is None and result_text.startswith("未找到工具："):
                _record_assistant_message(request, result_text)
                return ChatResponse(
                    answer=result_text,
                    tool_calls=executed_tool_calls,
                    used_tools=used_tools,
                    workflow_state="completed",
                )
            if parsed_result and parsed_result.get("status") == "error":
                print(
                    "[agent] chat flow pending write error polished: "
                    f"tool={tool_name} code={parsed_result.get('code')}"
                )
                answer_text = _polish_tool_error(tool_name, parsed_result, request)
                _record_assistant_message(request, answer_text)
                return ChatResponse(
                    answer=answer_text,
                    tool_calls=executed_tool_calls,
                    used_tools=used_tools,
                    workflow_state="completed",
                )

            answer_text = _format_write_success(tool_name, parsed_result or {})
            _record_assistant_message(request, answer_text)
            return ChatResponse(
                answer=answer_text,
                tool_calls=executed_tool_calls,
                used_tools=used_tools,
                workflow_state="completed",
            )

    booking_confirmation_response = _maybe_prepare_booking_confirmation(request=request, text=text)
    if booking_confirmation_response is not None:
        print(
            "[agent] chat flow booking short-path completed: "
            f"conversation_id={request.conversation_id} workflow={booking_confirmation_response.workflow_state}"
        )
        return booking_confirmation_response

    routed_response = _maybe_handle_knowledge_request(request=request, text=text)
    if routed_response is not None:
        print(
            "[agent] chat flow knowledge short-path completed: "
            f"conversation_id={request.conversation_id}"
        )
        return routed_response

    if not deepseek_is_configured():
        print("[agent] chat flow aborted: DeepSeek not configured")
        answer_text = "DeepSeek 未配置，当前只能返回占位结果。"
        _record_assistant_message(request, answer_text)
        return ChatResponse(
            answer=answer_text,
            tool_calls=[],
            used_tools=[],
            workflow_state="completed",
        )

    try:
        llm = get_deepseek_chat_model().bind_tools(get_gym_tools())
        print(
            "[agent] chat flow llm ready: "
            f"model={get_deepseek_chat_model().model_name if hasattr(get_deepseek_chat_model(), 'model_name') else 'unknown'} "
            f"tools={[tool.name for tool in get_gym_tools()]}"
        )
    except Exception as exc:
        print(f"[agent] chat flow init failed: {exc}")
        answer_text = f"工具调用初始化失败：{exc}"
        _record_assistant_message(request, answer_text)
        return ChatResponse(
            answer=answer_text,
            tool_calls=[],
            used_tools=[],
            workflow_state="completed",
        )

    try:
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
    except ImportError as exc:
        raise RuntimeError("langchain-core is required for tool calling") from exc

    messages = [SystemMessage(content=_build_system_message())]
    messages.append(SystemMessage(content=_build_time_anchor_text(request)))
    if history_text:
        messages.append(SystemMessage(content=history_text))
    commodity_context_text = _build_commodity_context_text(request)
    if commodity_context_text:
        messages.append(SystemMessage(content=commodity_context_text))
    messages.append(HumanMessage(content=f"{text}\n\n上下文:\n{_build_context_text(request) or '无'}"))

    executed_tool_calls: list[ChatToolCall] = []
    used_tools: list[str] = []

    # 最多循环 3 次，避免模型不断调用工具导致死循环。
    with request_context_scope(
        user_id=request.user_id,
        auth_token=request.auth_token,
        conversation_id=request.conversation_id,
        metadata=request.metadata,
    ):
        for step in range(3):
            print(f"[agent] chat flow invoke step={step + 1}")
            ai_message = llm.invoke(messages)

            # 如果模型不再请求工具，就把最终内容直接返回。
            if not getattr(ai_message, "tool_calls", None):
                answer_text = _normalize_and_guard_answer(ai_message.content or "", request)
                print(
                    "[agent] chat flow completed without tool calls: "
                    f"answer_length={len(answer_text)}"
                )
                _record_assistant_message(request, answer_text)
                return ChatResponse(
                    answer=answer_text,
                    tool_calls=executed_tool_calls,
                    used_tools=used_tools,
                    workflow_state="completed",
                )

            messages.append(ai_message)

            # 模型可能一次发起多个工具调用，这里逐个执行。
            for tool_call in ai_message.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {}) or {}
                tool_id = tool_call.get("id", "")
                print(
                    "[agent] chat flow tool call: "
                    f"name={tool_name} args={tool_args} tool_id={tool_id}"
                )

                selected_tool = _get_tool(tool_name)
                if selected_tool is None:
                    print(f"[agent] chat flow tool missing: {tool_name}")
                    result_text = f"未找到工具：{tool_name}"
                else:
                    if _is_write_tool(tool_name) and not _is_confirmation_text(text):
                        if tool_name == "purchase_order":
                            tool_args = dict(tool_args)
                            tool_args["purchase_items"] = _enrich_purchase_items_for_display(
                                request,
                                list(tool_args.get("purchase_items") or []),
                            )
                        pending = store_pending_action(
                            conversation_id=request.conversation_id,
                            user_id=request.user_id,
                            action={
                                "tool_name": tool_name,
                                "tool_args": dict(tool_args),
                                "tool_id": tool_id,
                                "original_text": text,
                            },
                        )
                        confirmation_prompt = _format_pending_confirmation(tool_name, tool_args)
                        print(
                            "[agent] chat flow write action pending confirmation: "
                            f"conversation_id={request.conversation_id} tool={tool_name}"
                        )
                        _record_assistant_message(request, confirmation_prompt)
                        return ChatResponse(
                            answer=confirmation_prompt,
                            tool_calls=executed_tool_calls
                            + [
                                ChatToolCall(
                                    name=tool_name,
                                    arguments=dict(tool_args),
                                    result="pending confirmation",
                                )
                            ],
                            used_tools=used_tools,
                            workflow_state="awaiting_confirmation",
                            requires_confirmation=True,
                            confirmation_prompt=confirmation_prompt,
                            pending_action=pending,
                        )

                    used_tools.append(tool_name)
                    result_text, parsed_result = _execute_tool_call(tool_name, dict(tool_args), request=request)
                    print(
                        "[agent] chat flow tool result: "
                        f"name={tool_name} result_length={len(result_text)}"
                    )
                    if parsed_result is None and result_text.startswith("未找到工具："):
                        _record_tool_message(
                            request,
                            tool_name=tool_name,
                            tool_args=dict(tool_args),
                            result_text=result_text,
                            tool_call_id=tool_id,
                        )
                        _record_assistant_message(request, result_text)
                        executed_tool_calls.append(
                            ChatToolCall(
                                name=tool_name,
                                arguments=dict(tool_args),
                                result=result_text,
                            )
                        )
                        return ChatResponse(
                            answer=result_text,
                            tool_calls=executed_tool_calls,
                            used_tools=used_tools,
                            workflow_state="completed",
                        )
                    if parsed_result and parsed_result.get("status") == "error":
                        print(
                            "[agent] chat flow tool error polished: "
                            f"tool={tool_name} code={parsed_result.get('code')}"
                        )
                        _record_tool_message(
                            request,
                            tool_name=tool_name,
                            tool_args=dict(tool_args),
                            result_text=result_text,
                            tool_call_id=tool_id,
                        )
                        answer_text = _polish_tool_error(tool_name, parsed_result, request)
                        _record_assistant_message(request, answer_text)
                        return ChatResponse(
                            answer=answer_text,
                            tool_calls=executed_tool_calls
                            + [
                                ChatToolCall(
                                    name=tool_name,
                                    arguments=dict(tool_args),
                                    result=result_text,
                                )
                            ],
                            used_tools=used_tools,
                            workflow_state="completed",
                        )

                executed_tool_calls.append(
                    ChatToolCall(
                        name=tool_name,
                        arguments=dict(tool_args),
                        result=result_text,
                    )
                )
                _record_tool_message(
                    request,
                    tool_name=tool_name,
                    tool_args=dict(tool_args),
                    result_text=result_text,
                    tool_call_id=tool_id,
                )

                # ToolMessage 是告诉模型“工具执行后的结果”。
                messages.append(ToolMessage(content=result_text, tool_call_id=tool_id))

    print("[agent] chat flow stopped after max steps")
    recovered_answer = _recover_answer_from_tool_calls(executed_tool_calls=executed_tool_calls, request=request)
    if recovered_answer:
        print("[agent] chat flow recovered final answer from tool results after max steps")
        _record_assistant_message(request, recovered_answer)
        return ChatResponse(
            answer=recovered_answer,
            tool_calls=executed_tool_calls,
            used_tools=used_tools,
            workflow_state="completed",
        )

    answer_text = _normalize_answer_text("工具调用已达到最大循环次数，未能生成最终回复。")
    _record_assistant_message(request, answer_text)
    return ChatResponse(
        answer=answer_text,
        tool_calls=executed_tool_calls,
        used_tools=used_tools,
        workflow_state="completed",
    )
