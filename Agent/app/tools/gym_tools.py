"""Aggregated gym tools for LangChain.
健身系统 LangChain 工具聚合入口。

This module collects all tools that the agent can use.
这个模块统一收集 agent 可用的查询和操作类工具。

Keep this file thin:
保持这个文件尽量薄：
- define no business logic here
  - 这里不要写业务逻辑
- just import and aggregate tools for the agent
  - 这里只负责导入并聚合工具
"""

from __future__ import annotations

from typing import Any

from .booking_tools import cancel_booking, create_booking, query_booking
from .cart_tools import add_cart_item, delete_cart_item, query_my_cart_items, update_cart_item
from .commodity_tools import query_commodity, query_commodity_stock
from .course_tools import cancel_enrollment, enroll_course, query_course, query_course_detail, query_my_courses
from .gym_room_tools import query_gym_room
from .member_tools import query_member_profile, query_member_status
from .order_tools import cancel_order, create_order, purchase_order, query_order, query_order_detail
from .rag_tools import rag_search, web_search


def get_gym_tools() -> list[Any]:
    """Return all tools that should be visible to the agent.
    返回应该暴露给 agent 的全部工具。
    """

    return [
        query_booking,
        create_booking,
        cancel_booking,
        query_order,
        query_order_detail,
        create_order,
        cancel_order,
        purchase_order,
        query_course,
        query_course_detail,
        query_my_courses,
        enroll_course,
        cancel_enrollment,
        query_member_status,
        query_member_profile,
        query_commodity,
        query_commodity_stock,
        query_gym_room,
        query_my_cart_items,
        add_cart_item,
        update_cart_item,
        delete_cart_item,
        rag_search,
        web_search,
    ]
