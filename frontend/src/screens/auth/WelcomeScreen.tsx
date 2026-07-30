import { Asset } from "expo-asset";
import React, { useEffect } from "react";
import { Image, SafeAreaView, StyleSheet, View } from "react-native";
import Svg, { Text as SvgText, TSpan } from "react-native-svg";
import Button from "../../components/Button";
import { useTheme } from "../../contexts/ThemeContext";
import { MESSAGES } from "../../utils/constants";

const WelcomeScreen = ({ navigation }: { navigation: any }) => {
  const { colors } = useTheme();
  const imageAsset = require("../../../assets/logo_light.png");

  useEffect(() => {
    async function loadResources() {
      try {
        await Asset.loadAsync(imageAsset);
      } catch (error) {
        console.warn("Asset load error:", error);
      } finally {
      }
    }
    loadResources();
  }, []);

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }}>
      <View style={styles.container}>
        <Image
          source={imageAsset}
          style={styles.backgroundImage}
          resizeMode="contain"
        />

        <View style={styles.svgContainer}>
          <Svg width="100%" height="100%" viewBox="0 0 350 250">
            <SvgText
              stroke="white"
              strokeWidth={30}
              strokeLinejoin="round"
              fontSize={45}
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
            </SvgText>

            <SvgText
              fill="black"
              fontSize={45}
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
            </SvgText>
          </Svg>
        </View>

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
  svgContainer: {
    width: "100%",
    maxWidth: 400,
    aspectRatio: 350 / 250,
  },
  backgroundImage: {
    position: "absolute",
    top: 90,
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
