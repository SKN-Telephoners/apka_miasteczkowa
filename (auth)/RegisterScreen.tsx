import { Ionicons } from "@expo/vector-icons";
import axios from "axios";
import React, { useState } from "react";
import {
  Alert,
  Modal,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import InputField from "./components/InputField";

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
    // We still need this to validate all inputs when the register button is clicked
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
    registerUser(username, email, password);
  };

  async function registerUser(
    username: string,
    email: string,
    password: string
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
        Alert.alert("Rejestracja nie powiodło się", response.data.message);
      }
    } catch (error: any) {
      if (error.response) {
        console.log(
          "Rejestracja nie powiodło się. Kod:",
          error.response.data.message
        );
      } else {
        console.error("Błąd:", error.message);
      }
    }
  }

  const handleInfoPress = () => {
    setInfoModalVisible(true);
  };

  return (
    <View style={styles.container}>
      <TouchableOpacity style={styles.infoButton} onPress={handleInfoPress}>
        <Ionicons name="information-circle-outline" size={36} color="#004aad" />
      </TouchableOpacity>

      <Text style={styles.title}>Rejestracja</Text>

      <View style={styles.inputContainer}>
        <InputField
          icon="person-outline"
          placeholder="Nazwa użytkownika"
          value={username}
          onChangeText={setUsername}
          secureTextEntry={false}
          keyboardType="default"
          errorMessage={usernameError}
          validate={validateUsername}
        />

        <InputField
          icon="mail-outline"
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          secureTextEntry={false}
          keyboardType="email-address"
          errorMessage={emailError}
          validate={validateEmail}
        />

        <InputField
          icon="lock-closed-outline"
          placeholder="Hasło"
          value={password}
          onChangeText={setPassword}
          secureTextEntry={secureText}
          toggleSecure={() => setSecureText(!secureText)}
          errorMessage={passwordError}
          validate={validatePassword}
        />

        <InputField
          icon="lock-closed-outline"
          placeholder="Powtórz hasło"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          secureTextEntry={secureTextConfirm}
          toggleSecure={() => setSecureTextConfirm(!secureTextConfirm)}
          errorMessage={confirmPasswordError}
          validate={validateConfirmPassword}
        />
      </View>

      <TouchableOpacity style={styles.registerButton} onPress={handleRegister}>
        <Text style={styles.buttonText}>Zarejestruj się</Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={() => navigation.navigate("Welcome")}>
        <Text style={styles.backText}>Wróć do strony głównej</Text>
      </TouchableOpacity>

      {/* Modal z wymaganiami */}
      <Modal
        animationType="fade"
        transparent={true}
        visible={infoModalVisible}
        onRequestClose={() => {
          setInfoModalVisible(false);
        }}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>Wymagania</Text>
            <Text style={styles.modalText}>
              Nazwa użytkownika musi zawierać co najmniej 3 znaki.
            </Text>
            <Text style={styles.modalText}>Hasło musi zawierać:</Text>
            <Text style={[styles.modalText, styles.modalBullet]}>
              - Co najmniej 8 znaków
            </Text>
            <Text style={[styles.modalText, styles.modalBullet]}>
              - Jedną wielką literę
            </Text>
            <Text style={[styles.modalText, styles.modalBullet]}>
              - Jedną małą literę
            </Text>
            <Text style={[styles.modalText, styles.modalBullet]}>
              - Jedną cyfrę
            </Text>
            <TouchableOpacity
              style={styles.closeButton}
              onPress={() => setInfoModalVisible(false)}
            >
              <Text style={styles.closeButtonText}>Zamknij</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f5f5f5",
    paddingTop: 50,
  },
  infoButton: {
    position: "absolute",
    top: 50,
    right: 20,
  },
  title: {
    fontSize: 48,
    fontWeight: "bold",
    color: "#004aad",
    marginBottom: 50,
    textAlign: "center",
  },
  inputContainer: {
    marginBottom: 15,
    width: "80%",
    alignItems: "center",
    gap: 30,
  },
  input: {
    flex: 1,
    marginLeft: 10,
  },
  registerButton: {
    backgroundColor: "#4a90e2",
    paddingVertical: 12,
    width: "80%",
    borderRadius: 10,
    alignItems: "center",
    marginTop: 30,
    marginBottom: 10,
  },
  buttonText: {
    color: "#fff",
    fontSize: 18,
  },
  backText: {
    color: "#4a90e2",
    marginTop: 10,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center",
  },
  modalContent: {
    backgroundColor: "#fff",
    borderRadius: 10,
    padding: 20,
    width: "80%",
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 10,
    textAlign: "center",
  },
  modalText: {
    fontSize: 16,
    marginBottom: 5,
    textAlign: "left",
  },
  modalBullet: {
    marginLeft: 10,
  },
  closeButton: {
    marginTop: 20,
    backgroundColor: "#4a90e2",
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: "center",
  },
  closeButtonText: {
    color: "#fff",
    fontSize: 18,
  },
});

export default RegisterScreen;
