import React, { useEffect, useState } from "react";
import { StatusBar, ActivityIndicator, View } from "react-native";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./contexts/AuthContext";
import { UserProvider } from "./contexts/UserContext";
import { EventProvider } from "./contexts/EventContext";
import { FriendsProvider } from "./contexts/FriendsContext";
import { ThemeProvider } from "./contexts/ThemeContext";
import AppNavigator from "./navigation/AppNavigator";
import { tokenStorage } from "./utils/storage";

const App = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30000,
            gcTime: 5 * 60 * 1000,
            retry: 1,
            refetchOnReconnect: true,
          },
        },
      }),
  );

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
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <AuthProvider>
            <UserProvider>
              <EventProvider>
                <FriendsProvider>
                  <StatusBar barStyle="dark-content" />
                  <AppNavigator />
                </FriendsProvider>
              </EventProvider>
            </UserProvider>
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
};

export default App;
