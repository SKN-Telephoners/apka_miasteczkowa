import axios from "axios";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { API_BASE_URL, STORAGE_KEYS } from "../utils/constants";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor - adds auth token to all requests
api.interceptors.request.use(
  async (config) => {
    const token = await AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
    if (token) {
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

    // if 401 and not already retried, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = await AsyncStorage.getItem(
          STORAGE_KEYS.REFRESH_TOKEN
        );

        if (refreshToken) {
          const response = await axios.post(`${API_BASE_URL}/api/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token } = response.data;
          await AsyncStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, access_token);

          // retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // refresh failed, clear tokens and redirect to login
        await AsyncStorage.multiRemove([
          STORAGE_KEYS.ACCESS_TOKEN,
          STORAGE_KEYS.REFRESH_TOKEN,
        ]);
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export const authService = {
  login: async (username: string, password: string) => {
    const response = await api.post("/api/login", { username, password });
    return response.data;
  },
  register: async (username: string, email: string, password: string) => {
    const response = await api.post("/api/register", {
      username,
      email,
      password,
    });
    return response.data;
  },
  resetPassword: async (email: string) => {
    const response = await api.post("/api/reset-password", { email });
    return response.data;
  },
  logout: async () => {
    const response = await api.post("/api/logout");
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
