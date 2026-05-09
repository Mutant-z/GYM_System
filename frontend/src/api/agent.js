function getToken() {
  return localStorage.getItem("gym-auth-token") || "";
}

function buildClientTimeMetadata() {
  const now = new Date();
  let timezone = "";
  try {
    timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
  } catch (_error) {
    timezone = "";
  }

  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  const hour = String(now.getHours()).padStart(2, "0");
  const minute = String(now.getMinutes()).padStart(2, "0");
  const second = String(now.getSeconds()).padStart(2, "0");

  return {
    timezone,
    client_time_iso: now.toISOString(),
    client_time_local: `${year}-${month}-${day} ${hour}:${minute}:${second}`
  };
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

  if (!response.ok) {
    throw new Error(payload.message || "request failed");
  }

  if (typeof payload.code === "number" && payload.code !== 0) {
    throw new Error(payload.message || "request failed");
  }

  return payload;
}

export function chatWithAgent({
  text,
  userId,
  conversationId = "",
  metadata = {}
}) {
  const authToken = getToken();
  const mergedMetadata = {
    ...buildClientTimeMetadata(),
    ...metadata
  };

  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      text,
      user_id: userId,
      auth_token: authToken,
      conversation_id: conversationId,
      metadata: mergedMetadata
    })
  });
}
