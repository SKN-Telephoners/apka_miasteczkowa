import React from "react";
import { View, Text, Image } from "react-native";
import { useTheme } from "../../contexts/ThemeContext";
import { THEME } from "../../utils/constants";

const HomeScreen = () => {
  const { colors } = useTheme();

  return (
    <View style={{ flex: 1, backgroundColor: colors.background, alignItems: "center", paddingTop: 40 }}>
      {/* Przesunięto tekst z center na górę za pomocą usunięcia justifyContent:"center" i dodania paddingTop */}
      <Text style={{...THEME.typography.title, color: colors.text}}>Przewodnik w budowie</Text>
      
      <View style={{ flex: 1, justifyContent: "center" }}>
        <Image 
          source={require("../../../assets/cattt.png")} 
          style={{ width: 300, height: 300, opacity: 0.9 }} 
          resizeMode="contain" 
        />
      </View>
    </View>
  );
};

export default HomeScreen;
