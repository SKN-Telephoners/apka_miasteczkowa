import React, { useState } from "react";
import { 
  View, 
  Text, 
  TextInput, 
  TouchableOpacity, 
  StyleSheet, 
  Alert 
} from "react-native";
import { Ionicons } from "@expo/vector-icons";

const ResetPasswordScreen = ({ navigation }: { navigation: any }) => {
  const [email, setEmail] = useState("");

  const handleResetPassword = () => {
    if (!email) {
      Alert.alert("Błąd", "Podaj swój adres email");
      return;
    }
    console.log("Wysyłanie linku resetowania hasła na adres:", email);
    Alert.alert("Sukces", "Link do resetowania hasła został wysłany!");
    // miejsce na logike
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Resetowanie hasła</Text>
      
      <View style={styles.inputContainer}>
        <Ionicons name="mail-outline" size={20} color="#ff914d" />
        <TextInput
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          style={styles.input}
          keyboardType="email-address"
        />
      </View>

      <TouchableOpacity style={styles.resetButton} onPress={handleResetPassword}>
        <Text style={styles.buttonText}>Wyślij link</Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={() => navigation.goBack()}>
        <Text style={styles.backText}>Wróć do logowania</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f5f5f5"
  },
  title: {
    fontSize: 50,
    fontWeight: "bold",
    color: "#004aad",
    marginBottom: 50,
    textAlign: "center"
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 10,
    paddingHorizontal: 10,
    marginBottom: 15,
    width: "80%",
    height: 50,
    borderWidth: 1,
    borderColor: "#ccc"
  },
  input: {
    flex: 1,
    marginLeft: 10
  },
  resetButton: {
    backgroundColor: "#4a90e2",
    paddingVertical: 12,
    width: "80%",
    borderRadius: 10,
    alignItems: "center",
    marginTop: 30,
    marginBottom: 10
  },
  buttonText: {
    color: "#fff",
    fontSize: 18
  },
  backText: {
    color: "#4a90e2",
    marginTop: 10
  }
});

export default ResetPasswordScreen;
