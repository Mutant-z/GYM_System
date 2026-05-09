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

export function fetchAdminMembers(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request(`/api/admin/members${suffix}`, { method: "GET" });
}

export function fetchAdminMemberDetail(id) {
  return request(`/api/admin/members/${id}`, { method: "GET" });
}

export function updateAdminMember(id, form) {
  return request(`/api/admin/members/${id}`, {
    method: "PUT",
    body: JSON.stringify(form)
  });
}

export function enableAdminMember(id) {
  return request(`/api/admin/members/${id}/enable`, { method: "POST" });
}

export function disableAdminMember(id) {
  return request(`/api/admin/members/${id}/disable`, { method: "POST" });
}
