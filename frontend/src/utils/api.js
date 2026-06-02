import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const dashboardApi = {
  getStats: () => api.get("/api/dashboard/stats"),
  getSessions: () => api.get("/api/dashboard/sessions"),
};

export const threatsApi = {
  getFeed: (limit = 50, offset = 0) =>
    api.get("/api/threats/feed", { params: { limit, offset } }),
  getProfiles: (limit = 20) =>
    api.get("/api/threats/profiles", { params: { limit } }),
};

export const meshApi = {
  getStatus: () => api.get("/api/mesh/status"),
  getIntel: (limit = 20) =>
    api.get("/api/mesh/intel", { params: { limit } }),
  getNodes: () => api.get("/api/mesh/nodes"),
};

export const agentApi = {
  chat: (message, sessionId = null, history = []) =>
    api.post("/api/agent/chat", {
      message,
      session_id: sessionId,
      conversation_history: history,
    }),
};

export const WS_URL = BASE_URL.replace("http", "ws") + "/ws/live-feed";

export default api;
