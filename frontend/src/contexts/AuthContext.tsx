import React, { createContext, useContext, useState, useEffect } from "react";
import AsyncStorage from '@react-native-async-storage/async-storage'
import { tokenStorage } from "../utils/storage";

interface AuthContextType {
  isAuthenticated: boolean;
  userId: string | null;
  isLoading: boolean;
  login: (accessToken: string, refreshToken: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userId, setUserId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const token = await tokenStorage.getAccessToken();
      const id = await tokenStorage.getUserId();
      setIsAuthenticated(!!token);
      setUserId(id);
    } catch (error) {
      console.error("Error checking auth status:", error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (accessToken: string, refreshToken: string) => {
    await tokenStorage.saveTokens(accessToken, refreshToken);
    const id = await tokenStorage.getUserId();
    setUserId(id);
    setIsAuthenticated(true);
    setIsLoading(false);
  };

  const logout = async () => {
    await tokenStorage.clearTokens();
    await AsyncStorage.clear();
    setUserId(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider value={{ isAuthenticated, userId, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};


