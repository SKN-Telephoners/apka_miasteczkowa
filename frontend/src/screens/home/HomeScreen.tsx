import React from "react";
import { View, Text, Button } from "react-native";
import { useAuth } from "../../contexts/AuthContext";

const HomeScreen = () => {
  const { logout } = useAuth();

  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
      <Text>Witamy na ekranie głównym!</Text>
      <Button title="Logout" onPress={logout} />
    </View>
  );
};

export default HomeScreen;