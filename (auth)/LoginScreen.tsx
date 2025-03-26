import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import axios from "axios";
import AsyncStorage from '@react-native-async-storage/async-storage';

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
    const response = await axios.post('http://10.0.2.2:5000/api/login', {
      username: username,
      password: password,
    });

    if (response.status === 200) {
      console.log("Logowanie powiodło się!");

      const { access_token, refresh_tocken } = response.data; // assuming the token is returned as 'token'
      await AsyncStorage.setItem('access_token', access_token);
      await AsyncStorage.setItem('refresh_tocken', refresh_tocken);

      navigation.navigate('Home');
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

  useEffect(() => {
    const fetchApiUrl = async () => {
      try {
        const res = await axios.get(`${BACKEND_URL}/get-url`);
        setApiUrl(res.data.url);
        console.log("Połączono z backendem:", res.data.url);
      } catch (error) {
        console.error("Nie udało się pobrać URL API", error);
      }
    };

    fetchApiUrl();
  }, []);

  const fetchData = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/message`);
      setMessage(response.data.message);
    } catch (error) {
      setMessage("Błąd pobierania danych");
    }
  };

  const sendData = async()=>{
    try {

      const requestBody = {
        name: username,
        password: password
    };

      const responde = await fetch(
        `${BACKEND_URL}/send_data`,
        {method: "POST",
          headers:{"Content-Type": "application/json"},
          body:JSON.stringify({name:username,password:password})
        });
        const data = await responde.json();
        console.log("Response:", data);
    }
    catch (error) {
      console.error("Error sending data:", error);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.titleContainer}>
        <Text style={styles.title}>Aplikacja Miasteczkowa</Text>
      </View>

      <View style={styles.inputContainer}>
        <Ionicons name="person-outline" size={20} color="#ff914d" />
        <TextInput
          placeholder="Username"
          value={username}
          onChangeText={setUsername}
          style={styles.input}
        />
      </View>

      <View style={styles.inputContainer}>
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
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f5f5f5"
  },
  titleContainer: {
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 50
  },
  title: {
    fontSize: 48,
    fontWeight: "bold",
    color: "#004aad",
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
  loginButton: {
    backgroundColor: "#4a90e2",
    paddingVertical: 12,
    width: "80%",
    borderRadius: 10,
    alignItems: "center",
    marginTop: 50,
    marginBottom: 10
  },
  signUpButton: {
    backgroundColor: "#ff914d",
    paddingVertical: 12,
    width: "80%",
    borderRadius: 10,
    alignItems: "center",
    marginTop: 10
  },
  buttonText: {
    color: "#fff",
    fontSize: 18
  },
  forgotPassword: {
    marginTop: 10,
    color: "#4a90e2"
  },
  wifi: {
    position: "absolute",
    top: 150,
    right: 95,
    color: "#4a90e2"
  }
});

export default LoginScreen;