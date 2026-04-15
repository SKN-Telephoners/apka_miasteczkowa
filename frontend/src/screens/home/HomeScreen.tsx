import React from "react";
import { View, Text } from "react-native";
import { useTheme } from "../../contexts/ThemeContext";
import { THEME } from "../../utils/constants";

const HomeScreen = () => {
  const { colors } = useTheme();

  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.background }}>
      <Text style={{...THEME.typography.title, color: colors.text}}>Przewodnik w budowie</Text>
    </View>
  );
};

export default HomeScreen;
