import React, { useState } from "react";
import {
  Alert,
  Dimensions,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { ScrollView } from "react-native-gesture-handler";
import Button from "../../components/Button";
import InputField from "../../components/InputField";
import { useTheme } from "../../contexts/ThemeContext";
import { authService } from "../../services/api";
import { MESSAGES, THEME } from "../../utils/constants";

const { height } = Dimensions.get("window");

const RegisterScreen = ({ navigation }: { navigation: any }) => {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [secureText, setSecureText] = useState(true);
  const [secureTextConfirm, setSecureTextConfirm] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const [usernameError, setUsernameError] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [confirmPasswordError, setConfirmPasswordError] = useState("");

  const { colors } = useTheme();

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
      /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
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
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/,
    );
    if (!text) {
      return "Pole jest wymagane";
    } else if (text.length < 8 || text.length > 32) {
      return "Hasło musi mieć pomiędzy 8 a 32 znaki";
    } else if (!password_pattern.test(text)) {
      return "Hasło musi zawierać co najmniej jedną wielką, małą literę i cyfrę";
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

  const handleRegister = async () => {
    if (!validateInputs()) {
      return;
    }
    setIsLoading(true);
    try {
      await authService.register(username, email, password);
      setIsLoading(false);
      Alert.alert(
        "Rejestracja przebiegła pomyślnie!",
        "Konto zostało utworzone. Potwierdź swoje konto przez link, który dostaniesz na maila.",
        [
          {
            text: "Przejdź do logowania",
            onPress: () => {
              navigation.reset({
                index: 0,
                routes: [{ name: "Login" }],
              });
            },
          },
        ],
      );
    } catch (error: any) {
      if (error.response) {
        Alert.alert(
          "Błąd rejestracji",
          error.response.data.message ||
            "Taki użytkownik lub email już istnieje.",
        );
      } else {
        Alert.alert(
          "Błąd rejestracji",
          "Wystąpił nieoczekiwany błąd. Spróbuj ponownie.",
        );
      }
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
        <Text style={[styles.title, { color: colors.text }]}>
          {"MESSAGES.APP.REGISTER_TITLE"}
        </Text>

        <View style={styles.inputContainer}>
          <InputField
            placeholder={MESSAGES.PLACEHOLDERS.USERNAME}
            value={username}
            onChangeText={setUsername}
            secureTextEntry={false}
            floatingLabelColor={colors.text}
            floatingLabelBackgroundColor={colors.background}
            errorMessage={usernameError}
            validate={validateUsername}
          />

          <InputField
            placeholder={MESSAGES.PLACEHOLDERS.EMAIL}
            value={email}
            onChangeText={setEmail}
            secureTextEntry={false}
            floatingLabelColor={colors.text}
            floatingLabelBackgroundColor={colors.background}
            errorMessage={emailError}
            validate={validateEmail}
          />

          <InputField
            placeholder={MESSAGES.PLACEHOLDERS.PASSWORD}
            value={password}
            onChangeText={setPassword}
            secureTextEntry={secureText}
            floatingLabelColor={colors.text}
            floatingLabelBackgroundColor={colors.background}
            toggleSecure={() => setSecureText(!secureText)}
            errorMessage={passwordError}
            validate={validatePassword}
          />

          <InputField
            placeholder={MESSAGES.PLACEHOLDERS.CONFIRM_PASSWORD}
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            secureTextEntry={secureTextConfirm}
            floatingLabelColor={colors.text}
            floatingLabelBackgroundColor={colors.background}
            toggleSecure={() => setSecureTextConfirm(!secureTextConfirm)}
            errorMessage={confirmPasswordError}
            validate={validateConfirmPassword}
          />
        </View>

        <View style={styles.buttonContainer}>
          <Button
            title={MESSAGES.BUTTONS.REGISTER}
            onPress={handleRegister}
            loading={isLoading}
            type="primary"
          />

          <Button
            title={MESSAGES.BUTTONS.BACK_TO_LOGIN}
            onPress={() => navigation.navigate("Login")}
            type="outline"
          />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    minHeight: height,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: 90,
    paddingBottom: 50,
    paddingHorizontal: 20,
  },
  title: {
    ...THEME.typography.title,
    marginVertical: 30,
    textAlign: "center",
  },
  inputContainer: {
    flex: 2,
    width: "80%",
    gap: 10,
    marginBottom: 40,
  },
  buttonContainer: {
    width: "60%",
    alignItems: "center",
    gap: 5,
  },
});

export default RegisterScreen;
