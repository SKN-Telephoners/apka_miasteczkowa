import { Asset } from "expo-asset";
import * as SplashScreen from "expo-splash-screen";
import React, { useCallback, useEffect, useState } from "react";
import { Image, SafeAreaView, StyleSheet, View } from "react-native";
import Svg, { Text, TSpan } from "react-native-svg";
import Button from "../../components/Button";

import { useTheme } from "../../contexts/ThemeContext";
import { MESSAGES, THEME } from "../../utils/constants";

// zapobieganie automatycznemu ukryciu splash screena
SplashScreen.preventAutoHideAsync();

const WelcomeScreen = ({ navigation }: { navigation: any }) => {
  const [isReady, setIsReady] = useState(false);
  const imageAsset = require("../../../assets/logo_light.png");
  const { colors } = useTheme();

  useEffect(() => {
    async function loadResources() {
      try {
        // cyk do pamięci podręcznej
        await Asset.loadAsync(imageAsset);
      } catch (error) {
        console.warn(error);
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
    <SafeAreaView
      style={{ flex: 1, backgroundColor: colors.background }}
      onLayout={onLayoutRootView}
    >
      <View style={styles.container}>
        <Image
          source={imageAsset}
          style={styles.backgroundImage}
          resizeMode="contain"
        />
        <Svg height="250" width="350">
          <Text
            stroke="white"
            strokeWidth={30}
            strokeLinejoin="round"
            fontSize={40}
            fontWeight="bold"
            textAnchor="middle"
            x="175"
            y="80"
          >
            <TSpan x="175" dy="0">
              Aplikacja
            </TSpan>
            <TSpan x="175" dy="55">
              Miasteczkowa
            </TSpan>
          </Text>

          <Text
            fill="black"
            fontSize={40}
            fontWeight="bold"
            textAnchor="middle"
            x="175"
            y="80"
          >
            <TSpan x="175" dy="0">
              Aplikacja
            </TSpan>
            <TSpan x="175" dy="55">
              Miasteczkowa
            </TSpan>
          </Text>
        </Svg>
          <Text>{MESSAGES.WELCOME.QUOTE}</Text>
        <View style={styles.buttonContainer}>
          <Button
            type="primary"
            title={MESSAGES.WELCOME.LOGIN}
            onPress={() => navigation.navigate("Login")}
          />
          <Button
            type="outline"
            title={MESSAGES.WELCOME.SIGN_UP}
            onPress={() => navigation.navigate("Register")}
          />
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 50,
    paddingHorizontal: 20,
  },
  backgroundImage: {
    position: "absolute",
    top: 50,
    width: "205%",
    height: "100%",
    opacity: 0.4,
  },
  buttonContainer: {
    width: "60%",
    gap: 5,
  },
});

export default WelcomeScreen;
