import axios from "axios";

export const API_BASE = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");
const api = axios.create({ baseURL: API_BASE, timeout: 15000 });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("skelo_access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let refreshPromise = null;
api.interceptors.response.use((r) => r, async (error) => {
  const original = error.config;
  const refresh = localStorage.getItem("skelo_refresh");
  if (error.response?.status === 401 && refresh && original && !original._retry && !String(original.url).includes("/auth/token/refresh/")) {
    original._retry = true;
    try {
      refreshPromise ||= axios.post(`${API_BASE}/auth/token/refresh/`, { refresh });
      const { data } = await refreshPromise;
      refreshPromise = null;
      if (data.access) localStorage.setItem("skelo_access", data.access);
      if (data.refresh) localStorage.setItem("skelo_refresh", data.refresh);
      original.headers.Authorization = `Bearer ${data.access}`;
      return api(original);
    } catch (e) {
      refreshPromise = null;
      auth.clearLocal();
      if (window.location.pathname !== "/login") window.location.assign("/login");
    }
  }
  return Promise.reject(error);
});

export function errorMessage(error, fallback = "Something went wrong. Please try again.") {
  const data = error?.response?.data;
  if (!data) return error?.message || fallback;
  if (typeof data === "string") return data;
  if (data.detail) return data.detail;
  for (const value of Object.values(data)) {
    if (Array.isArray(value) && value[0]) return String(value[0]);
    if (typeof value === "string") return value;
  }
  return fallback;
}

export async function get(path, config) { const { data } = await api.get(path, config); return data; }
export async function post(path, body, config) { const { data } = await api.post(path, body, config); return data; }
export async function put(path, body, config) { const { data } = await api.put(path, body, config); return data; }
export async function patch(path, body, config) { const { data } = await api.patch(path, body, config); return data; }
export async function del(path, config) { const { data } = await api.delete(path, config); return data; }

export async function download(path, config) {
  const { data, headers } = await api.get(path, { ...(config || {}), responseType: "blob" });
  const disposition = headers["content-disposition"] || "";
  const match = disposition.match(/filename="?([^";]+)"?/i);
  return { blob: data, filename: match?.[1] || "download.csv" };
}

export async function health() { return get("/dashboard/health/"); }

const saveUser = (user) => localStorage.setItem("skelo_user", JSON.stringify(user));
export const auth = {
  async login(payload) {
    // `identifier` is intentionally used instead of an email-only field.
    // It supports both normal student email login and the Admin ID.
    const body = {
      identifier: String(payload?.identifier ?? payload?.email ?? payload?.username ?? "").trim(),
      password: payload?.password ?? "",
    };
    const { data } = await api.post("/auth/login/", body);
    localStorage.setItem("skelo_access", data.access);
    localStorage.setItem("skelo_refresh", data.refresh);
    saveUser(data.user);
    return data;
  },
  async register(payload) { const { data } = await api.post("/auth/register/", payload); return data; },
  async profile() { const { data } = await api.get("/auth/profile/"); saveUser(data); return data; },
  async updateProfile(body, multipart = false) { const { data } = await api.patch("/auth/profile/", body, multipart ? { headers: { "Content-Type": "multipart/form-data" } } : undefined); saveUser(data); return data; },
  async forgotPassword(payload) { const { data } = await api.post("/auth/forgot-password/", payload); return data; },
  async resetPassword(payload) { const { data } = await api.post("/auth/reset-password/", payload); return data; },
  async verifyEmail(uid, token) { const { data } = await api.get("/auth/verify-email/", { params: { uid, token } }); return data; },
  async resendVerification() { const { data } = await api.post("/auth/resend-verification/"); return data; },
  async logout() { const refresh = localStorage.getItem("skelo_refresh"); try { if (refresh) await api.post("/auth/logout/", { refresh }); } finally { this.clearLocal(); } },
  clearLocal() { localStorage.removeItem("skelo_access"); localStorage.removeItem("skelo_refresh"); localStorage.removeItem("skelo_user"); },
  isAuthenticated() { return Boolean(localStorage.getItem("skelo_access")); },
};

export function unwrapList(data) { return Array.isArray(data) ? data : (data?.results || data?.data || []); }
export default api;
