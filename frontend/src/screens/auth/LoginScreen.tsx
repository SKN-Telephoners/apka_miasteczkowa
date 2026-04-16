import React, { useState } from "react";
import {
  View,
  Alert,
  KeyboardAvoidingView,
  StyleSheet,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  ScrollView,
  Platform,
} from "react-native";
import { useAuth } from "../../contexts/AuthContext";
import { authService } from "../../services/api";
import InputField from "../../components/InputField";
import Button from "../../components/Button";
import { useTheme } from "../../contexts/ThemeContext";
import { MESSAGES, THEME } from "../../utils/constants";

const LoginScreen = ({ navigation }: { navigation: any }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [secureText, setSecureText] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  const [usernameError, setUsernameError] = useState("");
  const [passwordError, setPasswordError] = useState("");

  const { login } = useAuth();
  const { colors } = useTheme();

  const validateUsername = (text: string): string | null => {
    if (!text) {
      return "Nazwa użytkownika jest wymagana.";
    }
    return null;
  };

  const validatePassword = (text: string): string | null => {
    if (!text) {
      return "Hasło jest wymagane.";
    }
    return null;
  };

  const handleLogin = async () => {
    setUsernameError("");
    setPasswordError("");

    const usernameValidation = validateUsername(username);
    const passwordValidation = validatePassword(password);

    if (usernameValidation || passwordValidation) {
      setUsernameError(usernameValidation || "");
      setPasswordError(passwordValidation || "");
      return;
    }

    setIsLoading(true);
    try {
      const response = await authService.login(username, password);
      await login(response.access_token, response.refresh_token);
      console.log("login success");
    } catch (error: any) {
      setUsernameError(MESSAGES.VALIDATION.CHECK_USERNAME);
      setPasswordError(MESSAGES.VALIDATION.CHECK_PASSWORD);
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
        <Text style={[styles.title, { color: colors.text }]}>{MESSAGES.APP.LOGIN_TITLE}</Text>

        <View style={styles.inputContainer}>
          <InputField
            placeholder={MESSAGES.PLACEHOLDERS.USERNAME}
            value={username}
            onChangeText={setUsername}
            secureTextEntry={false}
            autoComplete="username"
            textContentType="username"
            importantForAutofill="yes"
            floatingLabelColor={colors.text}
            floatingLabelBackgroundColor={colors.background}
            errorMessage={usernameError}
            validate={validateUsername}
          />

          <InputField
            placeholder={MESSAGES.PLACEHOLDERS.PASSWORD}
            value={password}
            onChangeText={setPassword}
            secureTextEntry={secureText}
            autoComplete="current-password"
            textContentType="password"
            importantForAutofill="yes"
            floatingLabelColor={colors.text}
            floatingLabelBackgroundColor={colors.background}
            toggleSecure={() => setSecureText(!secureText)}
            errorMessage={passwordError}
            validate={validatePassword}
          />

          <TouchableOpacity
            onPress={() => navigation.navigate("ResetPassword")}
            style={styles.forgotPasswordButton}
            activeOpacity={0.8}
          >
            <Text style={[styles.forgotPassword, { color: colors.highlight }]}>
              {MESSAGES.BUTTONS.FORGOT_PASSWORD}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.buttonContainer}>
          <Button
            title={MESSAGES.BUTTONS.LOGIN}
            onPress={handleLogin}
            loading={isLoading}
            type="primary"
          />

          <Button
            title={MESSAGES.BUTTONS.REGISTER}
            onPress={() => navigation.navigate("Register")}
            type="outline"
          />
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
    ...THEME.typography.title,
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
  forgotPasswordButton: {
    alignSelf: "flex-start",
    marginTop: 6,
    marginBottom: 8,
  },
  forgotPassword: {
    ...THEME.typography.text,
    fontSize: 13,
  },
});

export default LoginScreen;
