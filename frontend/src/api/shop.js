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

export function fetchCommodities() {
  return request("/api/commodities", { method: "GET" });
}

export function fetchCommodityDetail(id) {
  return request(`/api/commodities/${id}`, { method: "GET" });
}

export function fetchAdminCommodities() {
  return request("/api/admin/commodities", { method: "GET" });
}

export function fetchAdminCommodityDetail(id) {
  return request(`/api/admin/commodities/${id}`, { method: "GET" });
}

export function createCommodity(form) {
  return request("/api/admin/commodities", {
    method: "POST",
    body: JSON.stringify(form)
  });
}

export function updateCommodity(id, form) {
  return request(`/api/admin/commodities/${id}`, {
    method: "PUT",
    body: JSON.stringify(form)
  });
}

export function addCartItem(form) {
  return request("/api/cart/items", {
    method: "POST",
    body: JSON.stringify(form)
  });
}

export function fetchCartItems() {
  return request("/api/cart/items", { method: "GET" });
}

export function updateCartItem(id, form) {
  return request(`/api/cart/items/${id}`, {
    method: "PUT",
    body: JSON.stringify(form)
  });
}

export function deleteCartItem(id) {
  return request(`/api/cart/items/${id}`, { method: "DELETE" });
}

export function createOrder(form) {
  return request("/api/orders", {
    method: "POST",
    body: JSON.stringify(form)
  });
}

export function fetchOrders() {
  return request("/api/orders", { method: "GET" });
}

export function fetchOrderDetail(id) {
  return request(`/api/orders/${id}`, { method: "GET" });
}
