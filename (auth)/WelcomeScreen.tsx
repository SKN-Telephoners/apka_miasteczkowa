import React, { useState, useEffect, useCallback } from "react";
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  ImageBackground
} from "react-native";
import { LinearGradient } from "expo-linear-gradient"; 
import * as SplashScreen from "expo-splash-screen"; 
import { Asset } from "expo-asset"; 

// zapobieganie automatycznemu ukryciu splash screena
SplashScreen.preventAutoHideAsync();

const WelcomeScreen = ({ navigation }: { navigation: any }) => {
  const [isReady, setIsReady] = useState(false);
  const imageAsset = require("../assets/telephlogo.jpg");

  useEffect(() => {
    async function loadResources() {
      try {
        // cyk do pamięci podręcznej
        await Asset.loadAsync(imageAsset);
      } catch (error) {
        console.warn("Błąd ładowania zasobów:", error);
      } finally {
        setIsReady(true);
      }
    }
    loadResources();
  }, []);

  // jak sie załaduje ukrywamy splash screen
  const onLayoutRootView = useCallback(async () => {
    if (isReady) {
      await SplashScreen.hideAsync();
    }
  }, [isReady]);

  if (!isReady) {
    // jak obraz sie nie załadował to splashscreen 
    return null;
  }

  return (
    <View style={{ flex: 1 }} onLayout={onLayoutRootView}>
      <ImageBackground 
        source={imageAsset}
        style={styles.background}
      >
        <LinearGradient 
          colors={["rgba(3, 0, 209, 0.8)", "rgba(207, 111, 2, 0.8)"]} 
          style={styles.overlay}
        >
          <View style={styles.container}>
            <Text style={styles.title}>Aplikacja Miasteczkowa</Text>
            <TouchableOpacity 
              style={styles.loginButton} 
              onPress={() => navigation.navigate("Login")}
            >
              <Text style={styles.buttonText}>Zaloguj się</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.signUpButton} 
              onPress={() => navigation.navigate("Register")}
            >
              <Text style={styles.buttonText}>Załóż konto</Text>
            </TouchableOpacity>
            <Text style={styles.quote}>
              "Bo życie studenckie to coś więcej niż nauka"
            </Text>
          </View>
        </LinearGradient>
      </ImageBackground>
    </View>
  );
};

const styles = StyleSheet.create({
  background: {
    flex: 1,
    resizeMode: "cover",
  },
  overlay: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  container: {
    alignItems: "center",
    paddingHorizontal: 20,
  },
  title: {
    fontSize: 50,
    fontWeight: "bold",
    color: "#fff",
    marginBottom: 50,
    textAlign: "center",
  },
  quote: {
    fontSize: 25,
    fontStyle: "italic",
    color: "#fff",
    position: "absolute",
    bottom: -200,
    textAlign: "center",
  },
  loginButton: {
    backgroundColor: "rgba(74, 145, 226, 0)",
    borderWidth: 2,
    borderColor: "#4a90e2",
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 30,
    marginBottom: 20,
    width: "80%",
    alignItems: "center",
  },
  signUpButton: {
    backgroundColor: "rgba(255, 145, 77, 0)",
    borderWidth: 2,
    borderColor: "#ff914d",
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 30,
    width: "80%",
    alignItems: "center",
  },
  buttonText: {
    color: "#fff",
    fontSize: 20,
  },
});

export default WelcomeScreen;
