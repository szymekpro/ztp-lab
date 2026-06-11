const API_URL = "http://localhost:8000";

export async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Błąd requestu.");
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function apiGet(path) {
  return apiRequest(path, {
    method: "GET",
  });
}

export function apiPost(path, data) {
  return apiRequest(path, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function apiDelete(path) {
  return apiRequest(path, {
    method: "DELETE",
  });
}

export function apiPatch(path, data) {
  return apiRequest(path, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}