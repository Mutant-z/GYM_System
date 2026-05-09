"""Course query tools.
课程查询工具。

This module exposes course-related query tools for the agent.
这个模块向 agent 暴露课程相关的查询工具。

Scope:
职责范围：
- Query course list
  - 查询课程列表
- Query course detail
  - 查询课程详情
- Query the user's enrolled courses
  - 查询用户已报名课程

Enrollment and cancellation write operations are now exposed here.
报名和取消这类写操作已在此模块接入。
"""

from __future__ import annotations

from langchain_core.tools import tool

from ..services.course_service import cancel_enrollment as cancel_enrollment_service
from ..services.course_service import enroll_course as enroll_course_service
from ..services.course_service import get_course_detail as course_detail_service
from ..services.course_service import list_courses as list_courses_service
from ..services.course_service import query_my_courses as query_my_courses_service
from ._shared import build_login_required_result, resolve_request_identity, serialize_result


@tool
def query_course(query: str, course_id: str | None = None, status: str | None = None) -> str:
    """Query courses.
    查询课程。
    """

    request = {"query": query, "course_id": course_id, "status": status}
    identity = resolve_request_identity()
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="course",
                tool_name="query_course",
                request=request,
            )
        )
    if course_id:
        result = course_detail_service(course_id=course_id, auth_token=identity["auth_token"])
    else:
        result = list_courses_service(status=status, auth_token=identity["auth_token"])
    result["request"] = request
    return serialize_result(result)


@tool
def query_course_detail(course_id: str) -> str:
    """Query a single course detail.
    查询单个课程详情。
    """

    identity = resolve_request_identity()
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="course",
                tool_name="query_course_detail",
                request={"course_id": course_id},
            )
        )
    result = course_detail_service(course_id=course_id, auth_token=identity["auth_token"])
    return serialize_result(result)


@tool
def query_my_courses(user_id: str, status: str | None = None) -> str:
    """Query courses enrolled by the current user.
    查询当前用户已报名课程。
    """

    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="course",
                tool_name="query_my_courses",
                request={"user_id": user_id, "status": status},
            )
    )
    result = query_my_courses_service(status=status, user_id=identity["user_id"], auth_token=identity["auth_token"])
    return serialize_result(result)


@tool
def enroll_course(course_id: str, user_id: str | None = None) -> str:
    """Enroll in a course.
    报名课程。
    """

    request = {"course_id": course_id, "user_id": user_id}
    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="course",
                tool_name="enroll_course",
                request=request,
            )
        )
    result = enroll_course_service(course_id=course_id, user_id=identity["user_id"], auth_token=identity["auth_token"])
    return serialize_result(result)


@tool
def cancel_enrollment(
    enrollment_identifier: str | None = None,
    enrollment_id: str | None = None,
    enrollment_no: str | None = None,
    user_id: str | None = None,
) -> str:
    """Cancel a course enrollment.
    取消课程报名。
    """

    request = {
        "enrollment_identifier": enrollment_identifier,
        "enrollment_id": enrollment_id,
        "enrollment_no": enrollment_no,
        "user_id": user_id,
    }
    identity = resolve_request_identity(user_id=user_id)
    if not identity["auth_token"]:
        return serialize_result(
            build_login_required_result(
                domain="course",
                tool_name="cancel_enrollment",
                request=request,
            )
        )
    final_identifier = (enrollment_identifier or enrollment_id or enrollment_no or "").strip()
    if not final_identifier:
        return serialize_result(
            {
                "status": "error",
                "domain": "course",
                "operation": "cancel_enrollment",
                "source": "agent",
                "message": "enrollment_identifier or enrollment_id or enrollment_no is required",
                "request": request,
                "data": None,
            }
        )
    result = cancel_enrollment_service(
        enrollment_identifier=final_identifier,
        user_id=identity["user_id"],
        auth_token=identity["auth_token"],
    )
    return serialize_result(result)
