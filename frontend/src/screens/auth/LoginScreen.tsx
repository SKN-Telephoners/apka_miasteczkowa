import React, { useState } from "react";
import {
  Dimensions,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import Button from "../../components/Button";
import InputField from "../../components/InputField";
import { useAuth } from "../../contexts/AuthContext";
import { useTheme } from "../../contexts/ThemeContext";
import { authService } from "../../services/api";
import { MESSAGES, THEME } from "../../utils/constants";

const { height } = Dimensions.get("window");

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
      return MESSAGES.VALIDATION.REQUIRED_FIELD;
    }
    return null;
  };

  const validatePassword = (text: string): string | null => {
    if (!text) {
      return MESSAGES.VALIDATION.REQUIRED_FIELD;
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
        <Text style={styles.title}>{"MESSAGES.APP.LOGIN_TITLE"}</Text>

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
    flexGrow: 1,
    minHeight: height,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: 120,
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
