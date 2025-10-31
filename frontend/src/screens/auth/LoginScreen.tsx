import React, { useState } from "react";
import {
  View,
  Alert,
  StyleSheet,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  TextInput,
} from "react-native";
import { useAuth } from "../../contexts/AuthContext";
import { authService } from "../../services/api";
import { Ionicons } from "@expo/vector-icons";

const LoginScreen = ({ navigation }: { navigation: any }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [secureText, setSecureText] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const { login } = useAuth();

  const handleLogin = async () => {
    if (!username || !password) {
      Alert.alert("Błąd", "Uzupełnij proszę wszystkie pola");
      return;
    }

    setIsLoading(true);
    try {
      const response = await authService.login(username, password);

      // save tokens
      await login(response.access_token, response.refresh_token);

      console.log("login success");
    } catch (error: any) {
      Alert.alert("Błąd", "Nieprawidłowa nazwa użytkownika lub hasło");

      let errorMessage;

      if (error.response) {
        switch (error.response.status) {
          case 401:
            errorMessage = "Nieprawidłowe dane logowania.";
            break;
          case 404:
            errorMessage =
              "Nieautoryzowany dostęp. Sprawdź swoje dane logowania.";
            break;
          case 500:
            errorMessage = "Błąd serwera. Spróbuj ponownie później.";
            break;
          default:
            errorMessage = "Wystąpił nieznany błąd. Spróbuj ponownie.";
        }
      } else if (error.request) {
        errorMessage = "Brak połączenia z serwerem.";
      }

      Alert.alert("Błąd logowania", errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.titleContainer}>
        <Text style={styles.title}>Aplikacja Miasteczkowa</Text>
      </View>

      <View style={styles.inputContainer}>
        <Ionicons name="person-outline" size={20} color="#ff914d" />
        <TextInput
          placeholder="Username"
          value={username}
          onChangeText={setUsername}
          style={styles.input}
        />
      </View>

      <View style={styles.inputContainer}>
        <Ionicons name="lock-closed-outline" size={20} color="#ff914d" />
        <TextInput
          placeholder="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry={secureText}
          style={styles.input}
        />
        <TouchableOpacity onPress={() => setSecureText(!secureText)}>
          <Ionicons
            name={secureText ? "eye-off-outline" : "eye-outline"}
            size={20}
            color="#ff914d"
          />
        </TouchableOpacity>
      </View>

      <TouchableOpacity onPress={() => navigation.navigate("ResetPassword")}>
        <Text style={styles.forgotPassword}>Zapomniałeś hasła?</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.loginButton, isLoading && styles.buttonDisabled]}
        onPress={handleLogin}
        disabled={isLoading}
      >
        {isLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Zaloguj się</Text>
        )}
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.signUpButton}
        onPress={() => navigation.navigate("Register")}
      >
        <Text style={styles.buttonText}>Załóż konto</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f5f5f5",
  },
  titleContainer: {
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 50,
  },
  title: {
    fontSize: 48,
    fontWeight: "bold",
    color: "#004aad",
    textAlign: "center",
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
    borderColor: "#ccc",
  },
  input: {
    flex: 1,
    marginLeft: 10,
  },
  loginButton: {
    backgroundColor: "#4a90e2",
    paddingVertical: 12,
    width: "80%",
    borderRadius: 10,
    alignItems: "center",
    marginTop: 50,
    marginBottom: 10,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
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
  forgotPassword: {
    marginTop: 10,
    color: "#4a90e2",
  },
  wifi: {
    position: "absolute",
    top: 150,
    right: 95,
    color: "#4a90e2",
  },
});

export default LoginScreen;
