import React, { createContext, useState, useEffect, useContext, ReactNode } from "react";
import { useColorScheme } from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { THEME, STORAGE_KEYS } from "../utils/constants";

type ThemeType = "light" | "dark";

interface ThemeContextData {
  theme: ThemeType;
  isDark: boolean;
  colors: typeof THEME.colors.light;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextData | undefined>(undefined);

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const systemColorScheme = useColorScheme();
  const [theme, setTheme] = useState<ThemeType>(systemColorScheme === "dark" ? "dark" : "light");
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const loadTheme = async () => {
      try {
        const savedTheme = await AsyncStorage.getItem(STORAGE_KEYS.THEME);
        if (savedTheme) {
          setTheme(savedTheme as ThemeType);
        } else if (systemColorScheme) {
          setTheme(systemColorScheme);
        }
      } catch (error) {
        console.error("Error loading theme:", error);
      } finally {
        setIsReady(true);
      }
    };
    loadTheme();
  }, [systemColorScheme]);

  const toggleTheme = async () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.THEME, newTheme);
    } catch (error) {
      console.error("Error saving theme:", error);
    }
  };

  const isDark = theme === "dark";
  const colors = isDark ? THEME.colors.dark : THEME.colors.light;

  if (!isReady) {
    return null;
  }

  return (
    <ThemeContext.Provider value={{ theme, isDark, colors, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};
