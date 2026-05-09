const TOKEN_KEY = "gym-auth-token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function saveToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
    return;
  }
  localStorage.removeItem(TOKEN_KEY);
}

export function readToken() {
  return getToken();
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

export function memberLogin(form) {
  return request("/api/auth/member/login", {
    method: "POST",
    body: JSON.stringify(form)
  });
}

export function memberRegister(form) {
  return request("/api/auth/member/register", {
    method: "POST",
    body: JSON.stringify(form)
  });
}

export function adminLogin(form) {
  return request("/api/auth/admin/login", {
    method: "POST",
    body: JSON.stringify(form)
  });
}

export function fetchCurrentUser() {
  return request("/api/auth/me", {
    method: "GET"
  });
}

export function logout() {
  return request("/api/auth/logout", {
    method: "POST"
  });
}
