const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload.detail || payload.error || `Request failed with ${response.status}`;
    throw new Error(Array.isArray(message) ? message.map((item) => item.msg).join(", ") : message);
  }
  return payload;
}

export async function issueToken() {
  return request("/api/v1/auth/token", {
    method: "POST",
    body: JSON.stringify({ user_id: "demo-user", role: "analyst" }),
  });
}

export async function seedData(token) {
  return request("/api/v1/ingestion/seed", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function askQuestion(token, query) {
  return request("/api/v1/chat", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ query }),
  });
}

export async function getTopTitles(token, year = 2025, limit = 5) {
  return request(`/api/v1/analytics/top-titles?year=${year}&limit=${limit}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getStrongestCity(token, month = "2026-04") {
  return request(`/api/v1/analytics/strongest-city?month=${month}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getWeakGenres(token) {
  return request("/api/v1/analytics/weak-genres", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getAudienceSegments(token) {
  return request("/api/v1/analytics/audience-segments", {
    headers: { Authorization: `Bearer ${token}` },
  });
}
