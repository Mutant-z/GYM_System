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

export function fetchGymRooms() {
  return request("/api/gym/rooms", {
    method: "GET"
  });
}

export function fetchGymRoomDetail(id) {
  return request(`/api/gym/rooms/${id}`, {
    method: "GET"
  });
}

export function fetchAdminGymRooms() {
  return request("/api/admin/gym/rooms", {
    method: "GET"
  });
}

export function fetchAdminGymRoomDetail(id) {
  return request(`/api/admin/gym/rooms/${id}`, {
    method: "GET"
  });
}

export function createAdminGymRoom(form) {
  return request("/api/admin/gym/rooms", {
    method: "POST",
    body: JSON.stringify(form)
  });
}

export function updateAdminGymRoom(id, form) {
  return request(`/api/admin/gym/rooms/${id}`, {
    method: "PUT",
    body: JSON.stringify(form)
  });
}

export function enableAdminGymRoom(id) {
  return request(`/api/admin/gym/rooms/${id}/enable`, {
    method: "POST"
  });
}

export function disableAdminGymRoom(id) {
  return request(`/api/admin/gym/rooms/${id}/disable`, {
    method: "POST"
  });
}

export function createGymBooking(form) {
  return request("/api/gym/bookings", {
    method: "POST",
    body: JSON.stringify(form)
  });
}

export function fetchMyBookings(status = "") {
  const suffix = status ? `?status=${encodeURIComponent(status)}` : "";
  return request(`/api/gym/bookings/me${suffix}`, {
    method: "GET"
  });
}

export function cancelGymBooking(id) {
  return request(`/api/gym/bookings/${id}/cancel`, {
    method: "POST"
  });
}

export function fetchAdminBookings(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== "") {
      search.set(key, value);
    }
  });
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return request(`/api/gym/bookings${suffix}`, {
    method: "GET"
  });
}

export function adminCancelGymBooking(id) {
  return request(`/api/gym/bookings/${id}/admin-cancel`, {
    method: "POST"
  });
}
