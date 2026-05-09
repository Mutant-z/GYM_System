function getToken() {
  return localStorage.getItem("gym-auth-token") || "";
}

async function request(url, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    ...options,
    headers
  });

  const payload = await response.json().catch(() => ({
    code: response.status,
    message: "response is not valid json",
    data: null
  }));

  if (!response.ok || payload.code !== 0) {
    throw new Error(payload.message || "request failed");
  }

  return payload;
}

export function fetchCourses(status = "") {
  const suffix = status ? `?status=${encodeURIComponent(status)}` : "";
  return request(`/api/courses${suffix}`, {
    method: "GET"
  });
}

export function fetchCourseDetail(id) {
  return request(`/api/courses/${id}`, {
    method: "GET"
  });
}

export function enrollCourse(id) {
  return request(`/api/courses/${id}/enroll`, {
    method: "POST"
  });
}

export function fetchMyCourses(status = "") {
  const suffix = status ? `?status=${encodeURIComponent(status)}` : "";
  return request(`/api/courses/me${suffix}`, {
    method: "GET"
  });
}

export function cancelEnrollment(id) {
  return request(`/api/courses/enrollments/${id}/cancel`, {
    method: "POST"
  });
}

export function createCourse(form) {
  return request("/api/courses", {
    method: "POST",
    body: JSON.stringify(form)
  });
}

export function updateCourse(id, form) {
  return request(`/api/courses/${id}`, {
    method: "PUT",
    body: JSON.stringify(form)
  });
}

export function disableCourse(id) {
  return request(`/api/courses/${id}/disable`, {
    method: "POST"
  });
}

export function enableCourse(id) {
  return request(`/api/courses/${id}/enable`, {
    method: "POST"
  });
}

export function fetchCourseEnrollments(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, value);
    }
  });
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return request(`/api/courses/enrollments${suffix}`, {
    method: "GET"
  });
}

export function adminCancelEnrollment(id) {
  return request(`/api/courses/enrollments/${id}/admin-cancel`, {
    method: "POST"
  });
}
