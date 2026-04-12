import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SecureStore from "expo-secure-store";
import { STORAGE_KEYS } from "./constants";

export const tokenStorage = {
  saveTokens: async (accessToken: string, refreshToken: string) => {
    await SecureStore.setItemAsync(STORAGE_KEYS.ACCESS_TOKEN, accessToken);
    await SecureStore.setItemAsync(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
  },

  getAccessToken: async () => {
    return await SecureStore.getItemAsync(STORAGE_KEYS.ACCESS_TOKEN);
  },

  getRefreshToken: async () => {
    return await SecureStore.getItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
  },

  clearTokens: async () => {
    await SecureStore.deleteItemAsync(STORAGE_KEYS.ACCESS_TOKEN);
    await SecureStore.deleteItemAsync(STORAGE_KEYS.REFRESH_TOKEN);
  },

  getUserId: async () => {
    try {
      const accessToken = await SecureStore.getItemAsync(STORAGE_KEYS.ACCESS_TOKEN);

      if (!accessToken) {
        return null;
      }

      const parts = accessToken.split(".");
      if (parts.length !== 3) return null;

      const payload = parts[1];
      // Manuall base64 decode for react-native
      const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
      const jsonPayload = decodeURIComponent(
        Array.prototype.map
          .call(atob(base64), (c) => {
            return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2);
          })
          .join("")
      );

      const plainObject = JSON.parse(jsonPayload);
      return plainObject.sub || plainObject.user_id || null;
    } catch (e) {
      console.error("Error decoding JWT:", e);
      return null;
    }
  },
};
