import React, { useState } from "react";
import {
  View,
  Alert,
  KeyboardAvoidingView,
  StyleSheet,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  TextInput,
  ScrollView,
  Platform,
} from "react-native";
import { useAuth } from "../../contexts/AuthContext";
import { authService } from "../../services/api";
import InputField from "../../components/InputField";
import { MESSAGES } from "../../utils/constants";

const LoginScreen = ({ navigation }: { navigation: any }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [secureText, setSecureText] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [usernameError, setUsernameError] = useState("");
  const [passwordError, setPasswordError] = useState("");

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
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title}>{MESSAGES.APP.LOGIN_TITLE}</Text>

        <View style={styles.inputContainer}>
          <InputField
            placeholder={MESSAGES.PLACEHOLDERS.USERNAME}
            value={username}
            onChangeText={setUsername}
            secureTextEntry={false}
            errorMessage={usernameError}
          />

          <InputField
            placeholder={MESSAGES.PLACEHOLDERS.PASSWORD}
            value={password}
            onChangeText={setPassword}
            secureTextEntry={secureText}
            toggleSecure={() => setSecureText(!secureText)}
            errorMessage={passwordError}
          />

          <TouchableOpacity
            onPress={() => navigation.navigate("ResetPassword")}
          >
            <Text style={styles.forgotPassword}>
              {MESSAGES.BUTTONS.FORGOT_PASSWORD}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={[styles.loginButton, isLoading && styles.buttonDisabled]}
            onPress={handleLogin}
            disabled={isLoading}
          >
            {isLoading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>{MESSAGES.BUTTONS.LOGIN}</Text>
            )}
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.signUpButton}
            onPress={() => navigation.navigate("Register")}
          >
            <Text style={styles.buttonText}>{MESSAGES.BUTTONS.REGISTER}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: "center",
    justifyContent: "center",
  },
  title: {
    fontSize: 48,
    fontWeight: "bold",
    marginVertical: 30,
    textAlign: "center",
  },
  inputContainer: {
    flex: 2,
    width: "80%",
    marginBottom: 40,
  },
  buttonContainer: {
    width: "80%",
    alignItems: "center",
    gap: 15,
  },
  loginButton: {
    backgroundColor: "#4a90e2",
    paddingVertical: 12,
    width: "80%",
    borderRadius: 10,
    alignItems: "center",
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
  },
  buttonText: {
    color: "#fff",
    fontSize: 18,
  },
  forgotPassword: {
    marginTop: 10,
    color: "#4a90e2",
  },
});

export default LoginScreen;
