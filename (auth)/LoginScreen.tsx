import { Ionicons } from "@expo/vector-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import axios from "axios";
import React, { useEffect, useState } from "react";
import {
  Alert,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

const BACKEND_URL = "http://10.0.2.2:5000";

const LoginScreen = ({ navigation }: { navigation: any }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [secureText, setSecureText] = useState(true);
  const [apiUrl, setApiUrl] = useState(BACKEND_URL);
  const [message, setMessage] = useState("");

  const handleLogin = () => {
    if (!username || !password) {
      Alert.alert("Błąd", "Uzupełnij proszę wszystkie pola");
      return;
    }
    console.log("Logowanie:", username, password);
    //wywołanie funkcji login po sprawdzeniu pól
    logIn(username, password);
  };

  //funkcja login
  async function logIn(username: string, password: string): Promise<void> {
    try {
      const response = await axios.post("http://10.0.2.2:5000/api/login", {
        username: username,
        password: password,
      });

      if (response.status === 200) {
        console.log("Logowanie powiodło się!");

        const { access_token, refresh_token } = response.data; // assuming the token is returned as 'token'
        await AsyncStorage.setItem("access_token", access_token);
        await AsyncStorage.setItem("refresh_token", refresh_token);

        navigation.navigate("Home");
      } else {
        console.log("Logowanie nie powiodło się. Kod:", response.status);
      }
    } catch (error: any) {
      if (error.response) {
        console.log("Logowanie nie powiodło się. Kod:", error.response.status);
      } else {
        console.error("Błąd:", error.message);
      }
    }
  }

  return (
    <View style={styles.mainContainer}>
      <View style={styles.titleContainer}>
        <Text style={styles.title}>Aplikacja Miasteczkowa</Text>
      </View>

      <View>
        <View style={styles.inputContainer}>
          <View style={styles.inputBox}>
            <Ionicons name="person-outline" size={20} color="#ff914d" />
            <TextInput
              placeholder="Username"
              value={username}
              onChangeText={setUsername}
              style={styles.input}
            />
          </View>
          <Text
            style={[
              styles.errorMessage,
              { display: message ? "flex" : "none" },
            ]}
          >
            {}
          </Text>
        </View>

        <View style={styles.inputContainer}>
          <View style={styles.inputBox}>
            <Ionicons name="lock-closed-outline" size={20} color="#ff914d" />
            <TextInput
              placeholder="Password"
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
          <Text
            style={[
              styles.errorMessage,
              { display: message ? "flex" : "none" },
            ]}
          >
            {}
          </Text>
        </View>
      </View>

      <TouchableOpacity onPress={() => navigation.navigate("ResetPassword")}>
        <Text style={styles.forgotPassword}>Zapomniałeś hasła?</Text>
      </TouchableOpacity>

      <TouchableOpacity style={styles.loginButton} onPress={handleLogin}>
        <Text style={styles.buttonText}>Zaloguj się</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.signUpButton}
        onPress={() => navigation.navigate("Register")}
      >
        <Text style={styles.buttonText}>Załóż konto</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  mainContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f5f5f5",
  },
  titleContainer: {
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 50,
  },
  title: {
    fontSize: 48,
    fontWeight: "bold",
    color: "#004aad",
    textAlign: "center",
  },
  inputContainer: {
    marginBottom: 15,
    // width: "80%",
  },
  inputBox: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 10,
    paddingHorizontal: 10,
    height: 50,
    borderWidth: 1,
    borderColor: "#ccc",
  },
  input: {
    flex: 1,
    marginLeft: 10,
  },
  errorMessage: {
    color: "red",
    marginTop: 5,
    // display: "none"
  },
  loginButton: {
    backgroundColor: "#4a90e2",
    paddingVertical: 12,
    width: "80%",
    borderRadius: 10,
    alignItems: "center",
    marginTop: 50,
    marginBottom: 10,
  },
  signUpButton: {
    backgroundColor: "#ff914d",
    paddingVertical: 12,
    width: "80%",
    borderRadius: 10,
    alignItems: "center",
    marginTop: 10,
  },
  buttonText: {
    color: "#fff",
    fontSize: 18,
  },
  forgotPassword: {
    marginTop: 10,
    color: "#4a90e2",
  },
  wifi: {
    position: "absolute",
    top: 150,
    right: 95,
    color: "#4a90e2",
  },
});

export default LoginScreen;
