import dotenv from "dotenv";
import path from "path";

dotenv.config({ path: path.resolve(__dirname, ".env.local") });
// dotenv.config({ path: path.resolve(__dirname, ".env") });

export default {
  expo: {
    name: "aplikacja",
    slug: "aplikacja-miasteczkowa",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/icon.png",
    userInterfaceStyle: "light",
    newArchEnabled: false,
    splash: {
      image: "./assets/splash-icon.png",
      resizeMode: "contain",
      backgroundColor: "#ffffff",
    },
    ios: {
      supportsTablet: true,
      bundleIdentifier: "com.skntelephoners.aplikacjamiasteczkowa",
    },
    android: {
      adaptiveIcon: {
        foregroundImage: "./assets/adaptive-icon.png",
        backgroundColor: "#ffffff",
      },
      package: "com.skntelephoners.aplikacjamiasteczkowa",
    },
    web: {
      favicon: "./assets/favicon.png",
    },
    plugins: [
      "@maplibre/maplibre-react-native",
      "expo-image-picker",
      "expo-asset",
    ],
    extra: {
      eas: {
        projectId: "6b3dd378-2802-4aa8-8660-e3f3fd64d98a",
      },
      MAPTILER_KEY: process.env.MAPTILER_API_KEY,
    },
    owner: "skn-telephoners",
  },
};
