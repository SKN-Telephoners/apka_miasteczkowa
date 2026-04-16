import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableOpacity,
} from "react-native";
import { useTheme } from "../../contexts/ThemeContext";
import { THEME, MESSAGES } from "../../utils/constants";
import InputField from "../../components/InputField";
import Button from "../../components/Button";

const ResetPasswordScreen = ({ navigation }: { navigation: any }) => {
  const [email, setEmail] = useState("");
  const { colors } = useTheme();

  const handleResetPassword = () => {
    if (!email) {
      Alert.alert("Błąd", "Podaj swój adres email");
      return;
    }

    console.log("Wysyłanie linku resetowania hasła na adres:", email);
    Alert.alert("Sukces", "Link do resetowania hasła został wysłany!");
  };

  return (
    <KeyboardAvoidingView
      style={[styles.screen, { backgroundColor: colors.background }]}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <Text style={[styles.title, { color: colors.text }]}>
          {MESSAGES.APP.RESET_PASSWORD_TITLE}
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
            reserveErrorSpace={false}
            floatingLabelColor={colors.text}
            floatingLabelBackgroundColor={colors.background}
            leadingElement={
              <Text style={[styles.emoji, { color: colors.highlight }]}>✉️</Text>
            }
          />
        </View>

        <View style={styles.buttonContainer}>
          <Button
            title={MESSAGES.BUTTONS.SEND_RESET_LINK}
            onPress={handleResetPassword}
            type="primary"
          />
        </View>

        <TouchableOpacity onPress={() => navigation.goBack()} activeOpacity={0.8}>
          <Text style={[styles.backText, { color: colors.highlight }]}>
            Wróć do logowania
          </Text>
        </TouchableOpacity>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
  },
  container: {
    flexGrow: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: THEME.spacing.m,
  },
  title: {
    ...THEME.typography.title,
    textAlign: "center",
    marginBottom: THEME.spacing.xl,
  },
  inputContainer: {
    width: "80%",
    marginBottom: THEME.spacing.l,
  },
  buttonContainer: {
    width: "80%",
    alignItems: "center",
    marginBottom: THEME.spacing.m,
  },
  emoji: {
    fontSize: 18,
  },
  backText: {
    ...THEME.typography.text,
    fontSize: 13,
    textAlign: "center",
    marginTop: THEME.spacing.s,
  },
});

export default ResetPasswordScreen;
