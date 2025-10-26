import { Platform } from "react-native";

export const API_BASE_URL = __DEV__
  ? Platform.select({
      android: "http://10.0.2.2:5000", // Android emulator
      ios: "http://localhost:5000", // iOS simulator
      default: "http://localhost:5000",
    })
  : "https://production-api.com";

export const STORAGE_KEYS = {
  ACCESS_TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
  USER_DATA: "user_data",
} as const;

export const TIMEOUTS = {
  REQUEST_TIMEOUT: 10000, 
  RETRY_DELAY: 1000,
} as const;
