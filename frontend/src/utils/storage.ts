import AsyncStorage from "@react-native-async-storage/async-storage";
import { STORAGE_KEYS } from "./constants";

export const tokenStorage = {
  saveTokens: async (accessToken: string, refreshToken: string) => {
    await AsyncStorage.multiSet([
      [STORAGE_KEYS.ACCESS_TOKEN, accessToken],
      [STORAGE_KEYS.REFRESH_TOKEN, refreshToken],
    ]);
  },

  getAccessToken: async () => {
    return await AsyncStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  },

  getRefreshToken: async () => {
    return await AsyncStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  },

  clearTokens: async () => {
    await AsyncStorage.multiRemove([
      STORAGE_KEYS.ACCESS_TOKEN,
      STORAGE_KEYS.REFRESH_TOKEN,
    ]);
  },
};
