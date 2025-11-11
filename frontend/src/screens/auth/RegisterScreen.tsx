import React, { useState } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import axios from "axios";
import InputField from "../../components/InputField";
import { MESSAGES } from "../../utils/constants";
import { ScrollView } from "react-native-gesture-handler";

const RegisterScreen = ({ navigation }: { navigation: any }) => {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [secureText, setSecureText] = useState(true);
  const [secureTextConfirm, setSecureTextConfirm] = useState(true);
  const [infoModalVisible, setInfoModalVisible] = useState(false);

  const [usernameError, setUsernameError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");

  // Field-specific validation functions
  const validateUsername = (text: string): string | null => {
    if (!text) {
      return "Pole jest wymagane";
    } else if (text.length < 3) {
      return "Nazwa użytkownika musi mieć co najmniej 3 znaki";
    }
    return null;
  };

  const validateEmail = (text: string): string | null => {
    const email_pattern = new RegExp(
      /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
    );
    if (!text) {
      return "Pole jest wymagane";
    } else if (!email_pattern.test(text)) {
      return "Nieprawidłowy adres e-mail";
    }
    return null;
  };

  const validatePassword = (text: string): string | null => {
    const password_pattern = new RegExp(
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/
    );
    if (!text) {
      return "Pole jest wymagane";
    } else if (text.length < 8) {
      return "Hasło musi mieć co najmniej 8 znaków";
    } else if (!password_pattern.test(text)) {
      return "Hasło musi zawierać co najmniej jedną wielką literę, jedną małą literę i jedną cyfrę";
    }
    return null;
  };

  const validateConfirmPassword = (text: string): string | null => {
    if (!text) {
      return "Pole jest wymagane";
    } else if (text !== password) {
      return "Hasła nie pasują do siebie";
    }
    return null;
  };

  const validateInputs = () => {
    const usernameValidation = validateUsername(username);
    const emailValidation = validateEmail(email);
    const passwordValidation = validatePassword(password);
    const confirmPasswordValidation = validateConfirmPassword(confirmPassword);

    setUsernameError(usernameValidation || "");
    setEmailError(emailValidation || "");
    setPasswordError(passwordValidation || "");
    setConfirmPasswordError(confirmPasswordValidation || "");

    return (
      !usernameValidation &&
      !emailValidation &&
      !passwordValidation &&
      !confirmPasswordValidation
    );
  };

  const handleRegister = () => {
    if (!validateInputs()) {
      return;
    }
    console.log("Rejestracja:", username, email, password);

    // wywołanie funkcji rejestracji
    registerUser(username, email, password, confirmPassword);
  };

  // funkcja rejestracji (ta co wysyła api)
  async function registerUser(
    username: string,
    email: string,
    password: string,
    confirmPassword: string
  ): Promise<void> {
    try {
      const response = await axios.post("http://10.0.2.2:5000/api/register", {
        username: username,
        email: email,
        password: password,
      });

      if (response.status === 200) {
        console.log("Rejestracja powiodło się!");
        navigation.navigate("Welcome");
      } else {
        console.log("Rejestracja nie powiodło się. Kod:", response.status);
      }
    } catch (error: any) {
      if (error.response) {
        console.log(
          "Rejestracja nie powiodło się. Kod:",
          error.response.data.message
        );
        Alert.alert(
          "Rejestracja nie powiodła się",
          error.response.data.message
        );
      } else {
        console.error("Błąd:", error.message);
      }
    }
  }

  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
      >
        <Text style={styles.title}>{MESSAGES.APP.REGISTER_TITLE}</Text>

        <View style={styles.inputContainer}>
          <InputField
            placeholder={MESSAGES.PLACEHOLDERS.USERNAME}
            value={username}
            onChangeText={setUsername}
            secureTextEntry={false}
            errorMessage={usernameError}
            validate={validateUsername}
          />

          <InputField
            placeholder={MESSAGES.PLACEHOLDERS.EMAIL}
            value={email}
            onChangeText={setEmail}
            secureTextEntry={false}
            errorMessage={emailError}
            validate={validateEmail}
          />

          <InputField
            placeholder={MESSAGES.PLACEHOLDERS.PASSWORD}
            value={password}
            onChangeText={setPassword}
            secureTextEntry={secureText}
            toggleSecure={() => setSecureText(!secureText)}
            errorMessage={passwordError}
            validate={validatePassword}
          />

          <InputField
            placeholder={MESSAGES.PLACEHOLDERS.CONFIRM_PASSWORD}
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            secureTextEntry={secureTextConfirm}
            toggleSecure={() => setSecureTextConfirm(!secureTextConfirm)}
            errorMessage={confirmPasswordError}
            validate={validateConfirmPassword}
          />
        </View>

        <View style={styles.buttonContainer}>
          <TouchableOpacity
            style={styles.registerButton}
            onPress={handleRegister}
          >
            <Text style={styles.buttonText}>{MESSAGES.BUTTONS.REGISTER}</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.registerButton}
            onPress={() => navigation.navigate("Login")}
          >
            <Text style={styles.buttonText}>{MESSAGES.BUTTONS.BACK_TO_LOGIN}</Text>
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
  registerButton: {
    backgroundColor: "#4a90e2",
    paddingVertical: 12,
    width: "80%",
    borderRadius: 10,
    alignItems: "center",
  },
  buttonText: {
    color: "#fff",
    fontSize: 18,
  },
});

export default RegisterScreen;
