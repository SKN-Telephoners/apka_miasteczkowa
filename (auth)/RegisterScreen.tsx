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
import axios from "axios";

const RegisterScreen = ({ navigation }: { navigation: any }) => {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [secureText, setSecureText] = useState(true);
  const [secureTextConfirm, setSecureTextConfirm] = useState(true);
  const [infoModalVisible, setInfoModalVisible] = useState(false);

  const handleRegister = () => {
    // sprawdzanie czy nie zostawiono pustych pól
    if (!username || !email || !password || !confirmPassword) {
      Alert.alert("Błąd", "Proszę uzupełnić wszystkie pola");
      setInfoModalVisible(true);
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert("Błąd", "Hasła nie są takie same");
      setInfoModalVisible(true);
      return;
    }
    console.log("Rejestracja:", username, email, password);
    
    // wywołanie funkcji rejestracji
    registerUser(username, email, password, confirmPassword);
  };

  // funkcja rejestracji (ta co wysyła api)
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
        console.log("Rejestracja nie powiodło się. Kod:", response.status);
      }
    } catch (error: any) {
      if (error.response) {
        console.log("Rejestracja nie powiodło się. Kod:", error.response.status);
      } else {
        console.error("Błąd:", error.message);
      }
    }
  }

  // Funkcja wyświetlająca modal z wymaganiami
  const handleInfoPress = () => {
    setInfoModalVisible(true);
  };

  return (
    <View style={styles.container}>    
      
      {/* Info button */}
      <TouchableOpacity style={styles.infoButton} onPress={handleInfoPress}>
        <Ionicons name="information-circle-outline" size={36} color="#004aad" />
      </TouchableOpacity>
      
      <Text style={styles.title}>Rejestracja</Text>

      {/* Username */}
      <View style={styles.inputContainer}> 
        <Ionicons name="person-outline" size={20} color="#ff914d" />
        <TextInput
          placeholder="Nazwa użytkownika"
          value={username}
          onChangeText={setUsername}
          style={styles.input}
        />
      </View>
      
      {/* Email */}
      <View style={styles.inputContainer}>
        <Ionicons name="mail-outline" size={20} color="#ff914d" />
        <TextInput
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          style={styles.input}
          keyboardType="email-address"
        />
      </View>

      {/* Password */}
      <View style={styles.inputContainer}> 
        <Ionicons name="lock-closed-outline" size={20} color="#ff914d" />
        <TextInput
          placeholder="Hasło"
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

      {/* Confirm Password */}
      <View style={styles.inputContainer}>
        <Ionicons name="lock-closed-outline" size={20} color="#ff914d" />
        <TextInput
          placeholder="Powtórz hasło"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          secureTextEntry={secureTextConfirm}
          style={styles.input}
        />
        <TouchableOpacity onPress={() => setSecureTextConfirm(!secureTextConfirm)}>
          <Ionicons
            name={secureTextConfirm ? "eye-off-outline" : "eye-outline"}
            size={20}
            color="#ff914d"
          />
        </TouchableOpacity>
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
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 10,
    paddingHorizontal: 10,
    marginBottom: 15,
    width: "80%",
    height: 50,
    borderWidth: 1,
    borderColor: "#ccc"
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
