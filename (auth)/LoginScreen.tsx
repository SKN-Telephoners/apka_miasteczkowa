import React, { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import axios from 'axios';// dodana biblioteka

const DEFAULT_URL = "http://192.168.0.101:5000";  //do łączenia trzeba zmieniać za każdym razem


const LoginScreen = ({ navigation }: { navigation: any }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [secureText, setSecureText] = useState(true);
  const [apiUrl, setApiUrl] = useState(DEFAULT_URL);//zmienna url
  const [message, setMessage] = useState("");//zmienna pobranej wiadmości

  const fetchApiUrl = async () => { //wsysyła żądanie do serwera by potwierdzić połączenie
    try {
      const res = await axios.get(`${DEFAULT_URL}/get-url`);
      setApiUrl(res.data.url);
      console.log("Połączono z backendem:" ,res.data.url);
    } catch (error) {
      console.error("Nie udało się pobrać URL API", error);
    }
  };
  fetchApiUrl();//wywołanie funkcji

  const fetchData = async () => {//pobieranie wiadmości z serwera i wypisywanie na ekran
    try {
      const response = await axios.get(`${DEFAULT_URL}/message`);
      setMessage(response.data.message);
    } catch (error) {
      setMessage("Błąd pobierania danych");
    }
  };

  const sendData = async()=>{ //przykładowe wysyłanie danych
    try{

      const requestBody = {
        name: username,
        password: password
    };

      const responde = await fetch(
        `${DEFAULT_URL}/send_data`,
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

  const handleLogin = () => { //funkcja przycisku
    if (!username || !password) {
      Alert.alert("Błąd", "Uzupełnij proszę wszystkie pola");
      return;
    }
    console.log("Logowanie:", username, password);
    // miejsce na logike
    fetchData(); //wywołanie funkcji
    sendData(); //wywołanie funkcji
    
  };

  return (
    <View style={styles.container}>
      <View style={styles.titleContainer}>
        <Text style={styles.title}>Aplikacja Miasteczkowa</Text>
      </View>

      <View style={styles.wifi}>
        <Ionicons name="wifi-outline" size={65} color="#ff914d" />
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

      <Text style={{ marginTop: 20, fontSize: 18 }}>{message}</Text>/*miejsce testowe */

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