import React, { useState } from "react";
import {
  Alert,
  Dimensions,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Button from "../../components/Button";
import InputField from "../../components/InputField";
import { useTheme } from "../../contexts/ThemeContext";
import { MESSAGES, THEME } from "../../utils/constants";

const { height } = Dimensions.get("window");

const ResetPasswordScreen = ({ navigation }: { navigation: any }) => {
  const [email, setEmail] = useState("");
  const [emailError, setEmailError] = useState("");
  const { colors } = useTheme();

  const validateEmail = (text: string): string | null => {
    const email_pattern = new RegExp(
      /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
    );
    if (!email_pattern.test(text)) {
      return "Nieprawidłowy adres e-mail";
    }
    return null;
  };

  const handleResetPassword = () => {
    const error = validateEmail(email);
    if (error) {
      setEmailError(error);
      return;
    }
    setEmailError("");

    Alert.alert("Sukces", "Link do resetowania hasła został wysłany!");
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
          {"MESSAGES.APP.RESET_PASSWORD_TITLE"}
        </Text>

        <View style={styles.inputContainer}>
          <InputField
            placeholder="Email"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            autoComplete="email"
            textContentType="emailAddress"
            importantForAutofill="yes"
            showFloatingLabel={false}
            reserveErrorSpace={true}
            floatingLabelColor={colors.text}
            floatingLabelBackgroundColor={colors.background}
            errorMessage={emailError}
          />
        </View>

        <View style={styles.buttonContainer}>
          <Button
            title={MESSAGES.BUTTONS.SEND_RESET_LINK}
            onPress={handleResetPassword}
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
    justifyContent: "center",
    paddingTop: 180,
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

export default ResetPasswordScreen;
