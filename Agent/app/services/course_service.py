"""Course domain service.
课程业务服务。

This service owns course read operations for the agent.
这个服务负责 agent 的课程查询操作。

Current scope:
当前范围：
- List courses
  - 查询课程列表
- Query course detail
  - 查询课程详情
- Query the current user's enrolled courses
  - 查询当前用户已报名课程

Future scope:
未来范围：
- Enroll in a course
  - 报名课程
- Cancel course enrollment
  - 取消课程报名
"""

from __future__ import annotations

from typing import Any

from ..integrations.java_backend_client import JavaBackendClientError, request_json
from ._domain_utils import error_result, success_result


def _filter_courses(courses: list[dict[str, Any]], status: str | None) -> list[dict[str, Any]]:
    """Filter courses by status when needed.
    在需要时按状态过滤课程。
    """

    if not status:
        return courses
    return [item for item in courses if str(item.get("status", "")).lower() == str(status).lower()]


def _match_enrollment_identifier(item: dict[str, Any], enrollment_identifier: str) -> bool:
    """Match an enrollment item by id/number.
    根据报名 id/报名号匹配报名记录。
    """

    target = str(enrollment_identifier).strip().lower()
    if not target:
        return False

    candidates = [
        item.get("enrollmentId"),
        item.get("enrollment_id"),
        item.get("id"),
        item.get("enrollmentNo"),
        item.get("enrollment_no"),
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        if str(candidate).strip().lower() == target:
            return True
    return False


def list_courses(
    *,
    status: str | None = None,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """List available courses.
    查询可用课程列表。
    """

    request = {"status": status, "user_id": user_id}
    try:
        response = request_json(
            "GET",
            "/courses",
            params={"status": status} if status else None,
            auth_token=auth_token,
            user_id=user_id,
        )
        courses = response.get("data") or []
        if isinstance(courses, list):
            courses = _filter_courses(courses, status)
        return success_result(
            domain="course",
            operation="list_courses",
            request=request,
            data=courses,
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="course",
            operation="list_courses",
            request=request,
            error=str(exc),
            source="java_backend",
            code=getattr(exc, "status_code", None),
            details={
                "url": getattr(exc, "url", None),
                "response_text": getattr(exc, "response_text", None),
                "method": getattr(exc, "method", None),
                "path": getattr(exc, "path", None),
            },
        )


def get_course_detail(
    *,
    course_id: str,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Query a single course detail.
    查询单个课程详情。
    """

    request = {"course_id": course_id, "user_id": user_id}
    try:
        response = request_json("GET", f"/courses/{course_id}", auth_token=auth_token, user_id=user_id)
        return success_result(
            domain="course",
            operation="get_course_detail",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="course",
            operation="get_course_detail",
            request=request,
            error=str(exc),
            source="java_backend",
            code=getattr(exc, "status_code", None),
            details={
                "url": getattr(exc, "url", None),
                "response_text": getattr(exc, "response_text", None),
                "method": getattr(exc, "method", None),
                "path": getattr(exc, "path", None),
            },
        )


def query_my_courses(
    *,
    status: str | None = None,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Query courses enrolled by the current user.
    查询当前用户已报名课程。
    """

    request = {"status": status, "user_id": user_id}
    try:
        response = request_json(
            "GET",
            "/courses/me",
            params={"status": status} if status else None,
            auth_token=auth_token,
            user_id=user_id,
        )
        courses = response.get("data") or []
        if isinstance(courses, list):
            courses = _filter_courses(courses, status)
        return success_result(
            domain="course",
            operation="query_my_courses",
            request=request,
            data=courses,
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="course",
            operation="query_my_courses",
            request=request,
            error=str(exc),
            source="java_backend",
            code=getattr(exc, "status_code", None),
            details={
                "url": getattr(exc, "url", None),
                "response_text": getattr(exc, "response_text", None),
                "method": getattr(exc, "method", None),
                "path": getattr(exc, "path", None),
            },
        )


def enroll_course(
    *,
    course_id: str,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Enroll the current user in a course.
    为当前用户报名课程。
    """

    request = {"course_id": course_id, "user_id": user_id}
    try:
        response = request_json("POST", f"/courses/{course_id}/enroll", auth_token=auth_token, user_id=user_id)
        return success_result(
            domain="course",
            operation="enroll_course",
            request=request,
            data=response.get("data"),
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="course",
            operation="enroll_course",
            request=request,
            error=str(exc),
            source="java_backend",
            code=getattr(exc, "status_code", None),
            details={
                "url": getattr(exc, "url", None),
                "response_text": getattr(exc, "response_text", None),
                "method": getattr(exc, "method", None),
                "path": getattr(exc, "path", None),
            },
        )


def cancel_enrollment(
    *,
    enrollment_identifier: str,
    user_id: str | None = None,
    auth_token: str | None = None,
) -> dict[str, Any]:
    """Cancel a course enrollment.
    取消课程报名。
    """

    request = {"enrollment_identifier": enrollment_identifier, "user_id": user_id}
    try:
        list_response = request_json(
            "GET",
            "/courses/me",
            auth_token=auth_token,
            user_id=user_id,
        )
        items = list_response.get("data") or []
        matched_item = next(
            (item for item in items if isinstance(item, dict) and _match_enrollment_identifier(item, enrollment_identifier)),
            None,
        )
        if matched_item is None:
            return error_result(
                domain="course",
                operation="cancel_enrollment",
                request=request,
                error="enrollment not found for the given identifier",
                source="java_backend",
            )

        enrollment_id = (
            matched_item.get("enrollmentId")
            or matched_item.get("enrollment_id")
            or matched_item.get("id")
        )
        if enrollment_id is None:
            return error_result(
                domain="course",
                operation="cancel_enrollment",
                request=request,
                error="matched enrollment is missing id",
                source="java_backend",
            )

        response = request_json(
            "POST",
            f"/courses/enrollments/{enrollment_id}/cancel",
            auth_token=auth_token,
            user_id=user_id,
        )
        result_data = {
            "enrollmentId": enrollment_id,
            "enrollmentNo": matched_item.get("enrollmentNo") or matched_item.get("enrollment_no"),
            "status": "CANCELED",
        }
        return success_result(
            domain="course",
            operation="cancel_enrollment",
            request=request,
            data=result_data,
            source="java_backend",
            code=response.get("code"),
            message=response.get("message", "ok"),
        )
    except JavaBackendClientError as exc:
        return error_result(
            domain="course",
            operation="cancel_enrollment",
            request=request,
            error=str(exc),
            source="java_backend",
            code=getattr(exc, "status_code", None),
            details={
                "url": getattr(exc, "url", None),
                "response_text": getattr(exc, "response_text", None),
                "method": getattr(exc, "method", None),
                "path": getattr(exc, "path", None),
            },
        )
