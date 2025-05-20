import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';

const HomeScreen = ({ navigation }: { navigation: any }) => {
  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
      <Text>Witamy na ekranie głównym!</Text>

       <TouchableOpacity
              style={styles.signUpButton}
              onPress={() => navigation.navigate("Welcome")}
            >
              <Text style={styles.buttonText}>Powrót</Text>
            </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  signUpButton: {
    backgroundColor: "#ff914d",
    paddingVertical: 12,
    width: "80%",
    borderRadius: 10,
    alignItems: "center",
    marginTop: 10,
  },
  buttonText: {
    color: "#fff",
    fontSize: 18,
  },
});

export default HomeScreen;