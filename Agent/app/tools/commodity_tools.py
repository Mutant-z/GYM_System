"""Commodity query tools.
商品查询工具。

This module exposes commodity-related query tools for the agent.
这个模块向 agent 暴露商品相关的查询工具。

Scope:
职责范围：
- Query commodity list and detail
  - 查询商品列表和详情
- Query stock and availability
  - 查询库存和可售状态

Purchase and cart operations will be added later.
购买和购物车操作后面再补。
"""

from __future__ import annotations

from langchain_core.tools import tool

from ..services.commodity_service import get_commodity_detail as commodity_detail_service
from ..services.commodity_service import list_commodities as list_commodities_service
from ..services.commodity_service import query_stock as commodity_stock_service
from ._shared import build_login_required_result, resolve_request_identity, serialize_result


@tool
def query_commodity(query: str, commodity_id: str | None = None) -> str:
    """Query commodity records.
    查询商品记录。
    """

    request = {"query": query, "commodity_id": commodity_id}
    identity = resolve_request_identity()
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="commodity",
                tool_name="query_commodity",
                request=request,
            )
        )
    if commodity_id:
        result = commodity_detail_service(commodity_id=commodity_id, auth_token=identity["auth_token"])
    else:
        result = list_commodities_service(auth_token=identity["auth_token"])
    result["request"] = request
    return serialize_result(result)


@tool
def query_commodity_stock(query: str, commodity_id: str | None = None) -> str:
    """Query commodity stock.
    查询商品库存。
    """

    identity = resolve_request_identity()
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="commodity",
                tool_name="query_commodity_stock",
                request={"query": query, "commodity_id": commodity_id},
            )
        )
    result = commodity_stock_service(commodity_id=commodity_id, auth_token=identity["auth_token"])
    result["request"] = {"query": query, "commodity_id": commodity_id}
    return serialize_result(result)
