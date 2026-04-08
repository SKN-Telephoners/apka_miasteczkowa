import axios from "axios";
import { tokenStorage } from "../utils/storage";
import { API_BASE_URL } from "../utils/constants";

const MAX_RETRY_ATTEMPTS = 2;
const INITIAL_RETRY_DELAY = 500; // in milliseconds
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms)); // helper function for delay
let refreshPromise: Promise<string> | null = null;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});


// LOGOUT function to clear tokens
export async function handleSessionExpiry() {
  console.log("Token refresh failed, logging out");
  await tokenStorage.clearTokens();
    //TO DO : redirect to login screen
}

async function refreshAccessToken(): Promise<string> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const refreshToken = await tokenStorage.getRefreshToken();

      if (!refreshToken) {
        throw new Error("Missing refresh token");
      }

      console.log("Attempting token refresh");
      const response = await axios.post(`${API_BASE_URL}/api/auth/refresh`, {}, {
        headers: { Authorization: `Bearer ${refreshToken}` },
      });

      const { access_token, refresh_token } = response.data;

      if (!access_token || !refresh_token) {
        throw new Error("Invalid refresh response");
      }

      await tokenStorage.saveTokens(access_token, refresh_token);
      return access_token;
    })().finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
}
// Request interceptor - adds auth token to all requests
api.interceptors.request.use(
  async (config) => {
    console.log("Request interceptor for", config.url);
    const token = await tokenStorage.getAccessToken();
    if (token && !config.headers?.Authorization) {
      console.log("Found token, adding to headers");
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handles token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    console.log('Response error Błąd:', error.response?.status, 'dla URL:', originalRequest?.url);

    if (!originalRequest) {
      return Promise.reject(error);
    }
    
    const requestUrl: string = String(originalRequest.url || "");
    const isAuthEndpoint =
      requestUrl.includes("/api/auth/login") ||
      requestUrl.includes("/api/auth/register") ||
      requestUrl.includes("/api/auth/refresh");

    if (error.response?.status === 401 && !originalRequest._retry && !isAuthEndpoint) {
      originalRequest._retry = true;

      try {
        const accessToken = await refreshAccessToken();
        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        await handleSessionExpiry();
        return Promise.reject(new Error("Session expired. Please log in again."));
      }
    }
    const isRetryableError = !error.response || (error.response.status >= 500 && error.response.status < 600);
    if (isRetryableError) {
      originalRequest._retryCount = originalRequest._retryCount || 0;
      if (originalRequest._retryCount < MAX_RETRY_ATTEMPTS) {
        originalRequest._retryCount += 1;
        const delayDuration = INITIAL_RETRY_DELAY * Math.pow(2, originalRequest._retryCount - 1);

        console.log(`Retrying request to ${originalRequest.url} (attempt ${originalRequest._retryCount}) after ${delayDuration}ms`);

        await delay(delayDuration);

        return api(originalRequest);
      }
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: async (username: string, password: string) => {
    const response = await api.post("/api/auth/login", { username, password });
    return response.data;
  },
  register: async (username: string, email: string, password: string) => {
    const response = await api.post("/api/auth/register", {
      username,
      email,
      password,
    });
    return response.data;
  },
  resetPassword: async (email: string) => {
    const response = await api.post("/api/email/reset_password_request", { email });
    return response.data;
  },
  logout: async () => {
    const refreshToken = await tokenStorage.getRefreshToken();
    const accessToken = await tokenStorage.getAccessToken();

    const response = await api.delete("/api/auth/logout", {
      data: { access_token: accessToken },
      headers: refreshToken
        ? { Authorization: `Bearer ${refreshToken}` }
        : undefined,
    });
    return response.data;
  },
};

export const userService = {
  getProfile: async () => {
    const response = await api.get("/api/user/profile");
    return response.data;
  },

  updateProfile: async (data: any) => {
    const response = await api.put("/api/user/profile", data);
    return response.data;
  },
};

export default api;
