"""Intent classification service.
意图分类服务。

This module is now a lightweight intent-analysis helper.
这个模块现在更像一个轻量级意图分析辅助模块。

Current status:
当前状态：
- Useful for experiments, debugging, or future standalone intent analysis
  - 适合实验、调试或未来的独立意图分析
- Not part of the main `/chat` tool-calling path
  - 不属于主 `/chat` tool-calling 主流程

Avoid putting business execution logic here.
不要把业务执行逻辑放在这里。
"""

from __future__ import annotations

import json
import re
from typing import Any

from ..integrations.deepseek_client import deepseek_is_configured, get_deepseek_chat_model
from ..schemas.intent import IntentAnalysisRequest, IntentAnalysisResponse


# 这张表只做一件事：把业务意图映射到具体工具名。
_TOOL_MAP: dict[str, str] = {
    "business.booking.query": "query_booking",
    "business.booking.create": "create_booking",
    "business.booking.cancel": "cancel_booking",
    "business.course.query": "query_course",
    "business.course.enrollment.query": "query_course_enrollment",
    "business.course.enrollment.create": "create_course_enrollment",
    "business.course.enrollment.cancel": "cancel_course_enrollment",
    "business.order.query": "query_order",
    "business.order.create": "create_order",
    "business.order.cancel": "cancel_order",
    "business.commodity.query": "query_commodity",
    "business.commodity.stock.query": "query_commodity_stock",
    "business.member.status.query": "query_member_status",
    "business.member.update": "update_member_profile",
    "business.gym.room.query": "query_gym_room",
    "knowledge.rag_search": "rag_search",
    "knowledge.web_search": "web_search",
    "unknown": "unknown",
}


_SMALL_TALK_PATTERNS = [
    re.compile(r"^(你好|您好|哈喽|hello|hi|hey)[!！。.\s]*$", re.IGNORECASE),
    re.compile(r"^(早上好|上午好|中午好|下午好|晚上好|晚安)[!！。.\s]*$", re.IGNORECASE),
    re.compile(r"^(谢谢|感谢|thank you|thanks)[!！。.\s]*$", re.IGNORECASE),
    re.compile(r"^(在吗|有人吗|忙吗|嗨)[!！。.\s]*$", re.IGNORECASE),
]


def _build_prompt() -> str:
    """Build a short instruction prompt for the model.
    为模型准备简洁的提示词。
    """

    return (
        "你是健身系统的意图识别器。\n"
        "请判断用户输入属于什么类别，并选择下一步应该调用的工具。\n"
        "只返回结构化结果，不要输出多余解释。\n\n"
        "分类规则：\n"
        "1. 业务类：查询或操作预约、课程、订单、商品、会员、场地。\n"
        "2. 知识类：健身知识、平台说明、训练建议、网页知识。\n"
        "3. 如果用户要执行动作，如预约、取消、报名、下单，就归为业务类。\n"
        "4. 如果是寒暄、打招呼、感谢等闲聊，不走知识检索，归为 unknown。\n"
        "5. 如果缺少关键参数，请标记 needs_follow_up=true。\n"
    )


def _build_context(request: IntentAnalysisRequest) -> str:
    """Turn request metadata into a simple context string.
    把请求中的上下文整理成一段简单字符串。
    """

    context: dict[str, Any] = {}
    if request.user_id:
        context["user_id"] = request.user_id
    if request.conversation_id:
        context["conversation_id"] = request.conversation_id
    if request.metadata:
        context["metadata"] = request.metadata
    return json.dumps(context, ensure_ascii=False) if context else "{}"


def _build_chain():
    """Create a very small LangChain pipeline.
    构建一个非常简单的 LangChain 流程。
    """

    try:
        from langchain_core.prompts import ChatPromptTemplate
    except ImportError as exc:
        raise RuntimeError("langchain-core is required for intent analysis") from exc

    # `with_structured_output` will ask the model to return the schema directly.
    model = get_deepseek_chat_model().with_structured_output(IntentAnalysisResponse)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _build_prompt()),
            ("human", "用户输入：{text}\n上下文：{context}\n请返回结构化结果。"),
        ]
    )
    return prompt | model


def _fallback_analysis(request: IntentAnalysisRequest) -> IntentAnalysisResponse:
    """Use simple keyword rules when the model is unavailable.
    当模型不可用时，使用简单关键词规则兜底。
    """

    text = request.text.strip()

    if _is_small_talk(text):
        return IntentAnalysisResponse(
            category="unknown",
            intent="smalltalk.greeting",
            tool_name=_TOOL_MAP["unknown"],
            tool_args={},
            confidence=0.95,
            reason="Small-talk greeting or courtesy expression",
            source="fallback",
        )

    if _is_membership_catalog_question(text):
        return IntentAnalysisResponse(
            category="knowledge",
            intent="knowledge.rag_search",
            tool_name=_TOOL_MAP["knowledge.rag_search"],
            tool_args={"query": text},
            confidence=0.72,
            reason="Membership category/type question should go to knowledge retrieval",
            source="fallback",
        )

    # 先匹配“更明确”的动作，再匹配更宽泛的查询词，避免误判。
    rules: list[tuple[list[str], str]] = [
        (["取消预约", "退预约", "撤销预约"], "business.booking.cancel"),
        (["查预约", "查询预约", "预约记录", "我的预约", "查看预约"], "business.booking.query"),
        (["预约场地", "帮我预约", "预约房间", "预约健身房", "预约"], "business.booking.create"),
        (["取消报名", "退课", "取消课程报名"], "business.course.enrollment.cancel"),
        (["查报名", "查询报名", "报名记录", "我的课程", "查看课程报名"], "business.course.enrollment.query"),
        (["报名课程", "报名这节课", "帮我报名", "报名"], "business.course.enrollment.create"),
        (["取消订单"], "business.order.cancel"),
        (["查订单", "查询订单", "我的订单", "订单记录"], "business.order.query"),
        (["下单", "购买", "帮我买", "买这个商品"], "business.order.create"),
        (["库存", "库存多少", "还有货吗"], "business.commodity.stock.query"),
        (["商品详情", "商品信息", "查询商品", "商品"], "business.commodity.query"),
        (["会员状态", "会员到期", "我的会员", "会籍状态"], "business.member.status.query"),
        (["修改资料", "更新资料", "改手机号", "修改会员"], "business.member.update"),
        (["场地", "房间", "健身房"], "business.gym.room.query"),
        (["课程详情", "课程时间", "查询课程", "课程"], "business.course.query"),
    ]

    for keywords, intent in rules:
        if any(keyword in text for keyword in keywords):
            return IntentAnalysisResponse(
                category="business",
                intent=intent,
                tool_name=_TOOL_MAP[intent],
                tool_args={"query": text},
                confidence=0.55,
                reason=f"Matched keyword: {keywords[0]}",
                source="fallback",
            )

    if "最新" in text or "网上" in text or "网页" in text:
        return IntentAnalysisResponse(
            category="knowledge",
            intent="knowledge.web_search",
            tool_name=_TOOL_MAP["knowledge.web_search"],
            tool_args={"query": text},
            confidence=0.55,
            reason="Likely needs web search",
            source="fallback",
        )

    if _looks_like_knowledge_question(text):
        return IntentAnalysisResponse(
            category="knowledge",
            intent="knowledge.rag_search",
            tool_name=_TOOL_MAP["knowledge.rag_search"],
            tool_args={"query": text},
            confidence=0.45,
            reason="Looks like explicit knowledge question",
            source="fallback",
        )

    return IntentAnalysisResponse(
        category="unknown",
        intent="unknown",
        tool_name=_TOOL_MAP["unknown"],
        tool_args={},
        confidence=0.35,
        reason="No strong keyword match",
        source="fallback",
    )


def analyze_intent(request: IntentAnalysisRequest) -> IntentAnalysisResponse:
    """Analyze user input and return the next action.
    分析用户输入，并返回下一步该走的动作。
    """

    text = request.text.strip()
    if not text:
        raise ValueError("text must not be empty")

    if _is_small_talk(text):
        return IntentAnalysisResponse(
            category="unknown",
            intent="smalltalk.greeting",
            tool_name=_TOOL_MAP["unknown"],
            tool_args={},
            confidence=0.95,
            reason="Small-talk greeting or courtesy expression",
            source="fallback",
        )

    if _is_membership_catalog_question(text):
        return IntentAnalysisResponse(
            category="knowledge",
            intent="knowledge.rag_search",
            tool_name=_TOOL_MAP["knowledge.rag_search"],
            tool_args={"query": text},
            confidence=0.75,
            reason="Membership category/type question should go to knowledge retrieval",
            source="fallback",
        )

    # 如果模型没配好，直接走本地规则，保证服务能用。
    if not deepseek_is_configured():
        return _fallback_analysis(request)

    try:
        chain = _build_chain()
        result = chain.invoke(
            {
                "text": text,
                "context": _build_context(request),
            }
        )

        # 有些情况下模型可能没填 tool_name，这里按 intent 补一下。
        if not result.tool_name and result.intent in _TOOL_MAP:
            result.tool_name = _TOOL_MAP[result.intent]

        if _is_small_talk(text):
            return IntentAnalysisResponse(
                category="unknown",
                intent="smalltalk.greeting",
                tool_name=_TOOL_MAP["unknown"],
                tool_args={},
                confidence=0.95,
                reason="Small-talk greeting or courtesy expression",
                source="fallback",
            )

        return result
    except Exception:
        # 任何模型或解析问题，都不要影响主流程。
        return _fallback_analysis(request)


def _is_small_talk(text: str) -> bool:
    normalized = re.sub(r"\s+", "", str(text or "")).strip().lower()
    if not normalized:
        return False
    for pattern in _SMALL_TALK_PATTERNS:
        if pattern.match(normalized):
            return True
    # short courtesy inputs like "你好呀", "thanks~"
    if len(normalized) <= 8 and any(token in normalized for token in ["你好", "您好", "谢谢", "thanks", "hello", "hi"]):
        return True
    return False


def _looks_like_knowledge_question(text: str) -> bool:
    normalized = str(text or "").strip().lower()
    if not normalized:
        return False
    if len(normalized) < 3:
        return False

    knowledge_cues = [
        "怎么",
        "如何",
        "是什么",
        "原理",
        "注意事项",
        "建议",
        "科普",
        "训练",
        "健身",
        "营养",
        "器械",
        "跑步机",
        "增肌",
        "减脂",
        "会籍",
        "会员卡",
        "种类",
        "类型",
    ]
    return any(cue in normalized for cue in knowledge_cues)


def _is_membership_catalog_question(text: str) -> bool:
    normalized = re.sub(r"\s+", "", str(text or "")).lower()
    if not normalized:
        return False

    membership_terms = ["会员", "会员卡", "会籍", "健身卡"]
    catalog_terms = ["种类", "类型", "几种", "多少种", "哪几种", "有哪些"]
    business_status_terms = ["我的", "到期", "状态", "续费", "手机号", "修改", "更新", "个人"]

    has_membership = any(term in normalized for term in membership_terms)
    has_catalog = any(term in normalized for term in catalog_terms)
    has_status_intent = any(term in normalized for term in business_status_terms)

    return has_membership and has_catalog and not has_status_intent
