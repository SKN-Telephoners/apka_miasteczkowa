import React, { useEffect, useState } from "react";
import { StatusBar, ActivityIndicator, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { AuthProvider } from "./contexts/AuthContext";
import { EventProvider } from "./contexts/EventContext";
import AppNavigator from "./navigation/AppNavigator";
import { tokenStorage } from "./utils/storage";

const App = () => {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initApp = async () => {
      try {
        const token = await tokenStorage.getAccessToken();
        console.log("Access Token on App Start:", !!token);
      } catch (error) {
        console.error("Error retrieving access token:", error);
      } finally {
        setIsLoading(false);
      }
    };
    initApp();
  }, []);

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" color="#0000ff" />
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <AuthProvider>
        <StatusBar barStyle="dark-content" />
        <AppNavigator />
      </AuthProvider>
    </SafeAreaProvider>
  );
};

export default App;
