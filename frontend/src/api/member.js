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

export function fetchMyProfile() {
  return request("/api/members/me/profile", { method: "GET" });
}

export function updateMyProfile(form) {
  return request("/api/members/me/profile", {
    method: "PUT",
    body: JSON.stringify(form)
  });
}
