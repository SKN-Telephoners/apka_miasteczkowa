import React from "react";
import { View, Text, Button, Switch } from "react-native";
import { useAuth } from "../../contexts/AuthContext";
import { useTheme } from "../../contexts/ThemeContext";

const HomeScreen = () => {
  const { logout } = useAuth();
  const { isDark, toggleTheme, colors } = useTheme();

  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.background }}>
      <Text style={{ color: colors.text, fontSize: 18, marginBottom: 20 }}>Witamy na ekranie głównym!</Text>
      
      <View style={{ flexDirection: "row", alignItems: "center", marginVertical: 20 }}>
        <Text style={{ color: colors.text, marginRight: 10 }}>Jasny</Text>
        <Switch
          trackColor={{ false: "#767577", true: colors.highlight }}
          thumbColor={isDark ? "#f5dd4b" : "#f4f3f4"}
          ios_backgroundColor="#3e3e3e"
          onValueChange={toggleTheme}
          value={isDark}
        />
        <Text style={{ color: colors.text, marginLeft: 10 }}>Ciemny</Text>
      </View>

      <Button title="Logout" onPress={logout} color={colors.highlight} />
    </View>
  );
};

export default HomeScreen;
