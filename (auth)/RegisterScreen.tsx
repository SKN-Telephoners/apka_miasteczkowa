import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Modal
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import InputField from "./components/InputField";
import axios from "axios";

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

  const validateInputs = () => {
    let isValid = true;

    if (!username) {
      setUsernameError("Pole jest wymagane");
      isValid = false;
    } else if (username.length < 3) {
      setUsernameError("Nazwa użytkownika musi mieć co najmniej 3 znaki");
      isValid = false;
    } else {
      setUsernameError("");
    }

    const email_pattern = new RegExp(
      /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
    );
    if (!email) {
      setEmailError("Pole jest wymagane");
      isValid = false;
    } else if (!email_pattern.test(email)) {
      setEmailError("Nieprawidłowy adres e-mail");
      isValid = false;
    } else {
      setEmailError("");
    }

    const password_pattern = new RegExp(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/);
    if (!password) {
      setPasswordError("Pole jest wymagane");
      isValid = false;
    } else if (password.length < 8) {
      setPasswordError("Hasło musi mieć co najmniej 8 znaków");
      isValid = false;
    } else if (!password_pattern.test(password)) {
      setPasswordError(
        "Hasło musi zawierać co najmniej jedną wielką literę, jedną małą literę i jedną cyfrę"
      );
      isValid = false;
    } else {
      setPasswordError("");
    }

    if (!confirmPassword) {
      setConfirmPasswordError("Pole jest wymagane");
      isValid = false;
    } else if (confirmPassword !== password) {
      setConfirmPasswordError("Hasła nie pasują do siebie");
      isValid = false;
    } else {
      setConfirmPasswordError("");
    }

    return isValid;
  }


  const handleRegister = () => {
    if (validateInputs()) {
      console.log("Rejestracja:", username, email, password);
      registerUser(username, email, password, confirmPassword);
    }
  };

  async function registerUser(username: string, email: string, password: string, confirmPassword: string): Promise<void> {
    try {
      const response = await axios.post('http://10.0.2.2:5000/api/register', {
        username: username,
        email: email,
        password: password,
        confirmPassword: confirmPassword,
      });

      if (response.status === 200) {
        console.log("Rejestracja powiodło się!");
        navigation.navigate('Login');
      } else {
        console.log("Rejestracja nie powiodło się. Kod:", response.data);
      }
    } catch (error: any) {
      if (error.response) {
        console.log("Rejestracja nie powiodło się. Kod:", error.response.data.message);
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
        />

        <InputField
          icon="mail-outline"
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          secureTextEntry={false}
          keyboardType="email-address"
          errorMessage={emailError}
        />

        <InputField
          icon="lock-closed-outline"
          placeholder="Hasło"
          value={password}
          onChangeText={setPassword}
          secureTextEntry={secureText}
          toggleSecure={() => setSecureText(!secureText)}
          errorMessage={passwordError}
        />

        <InputField
          icon="lock-closed-outline"
          placeholder="Powtórz hasło"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          secureTextEntry={secureTextConfirm}
          toggleSecure={() => setSecureText(!secureTextConfirm)}
          errorMessage={confirmPasswordError}
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
            <Text style={styles.modalText}>
              Hasło musi zawierać:
            </Text>
            <Text style={[styles.modalText, styles.modalBullet]}>- Co najmniej 8 znaków</Text>
            <Text style={[styles.modalText, styles.modalBullet]}>- Jedną wielką literę</Text>
            <Text style={[styles.modalText, styles.modalBullet]}>- Jedną małą literę</Text>
            <Text style={[styles.modalText, styles.modalBullet]}>- Jedną cyfrę</Text>
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
    textAlign: "center"
  },
  inputContainer: {
    marginBottom: 15,
    width: "80%",
    alignItems: "center",
    gap: 30,
  },
  input: {
    flex: 1,
    marginLeft: 10
  },
  registerButton: {
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
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center"
  },
  modalContent: {
    backgroundColor: "#fff",
    borderRadius: 10,
    padding: 20,
    width: "80%"
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 10,
    textAlign: "center"
  },
  modalText: {
    fontSize: 16,
    marginBottom: 5,
    textAlign: "left"
  },
  modalBullet: {
    marginLeft: 10
  },
  closeButton: {
    marginTop: 20,
    backgroundColor: "#4a90e2",
    paddingVertical: 10,
    borderRadius: 10,
    alignItems: "center"
  },
  closeButtonText: {
    color: "#fff",
    fontSize: 18
  }
});

export default RegisterScreen;
