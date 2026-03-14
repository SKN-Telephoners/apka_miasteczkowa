import { NavigationContainer } from "@react-navigation/native";
import { createStackNavigator } from "@react-navigation/stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import WelcomeScreen from "../screens/auth/WelcomeScreen";
import LoginScreen from "../screens/auth/LoginScreen";
import RegisterScreen from "../screens/auth/RegisterScreen";
import ResetPasswordScreen from "../screens/auth/ResetPasswordScreen";
import HomeScreen from "../screens/home/HomeScreen";
import MapScreen from "../screens/home/MapScreen";
import ProfileStack from "./ProfileStack";
import EventStack from "./EventStack";
import { Ionicons } from "@expo/vector-icons";
import type { ComponentProps } from "react";
import { useAuth } from "../contexts/AuthContext";
import { ActivityIndicator, View, TouchableOpacity, Image } from "react-native";

const Stack = createStackNavigator();
const Tab = createBottomTabNavigator();

// login register flow
const AuthStack = () => {
  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Welcome" component={WelcomeScreen} />
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
      <Stack.Screen name="ResetPassword" component={ResetPasswordScreen} />
    </Stack.Navigator>
  );
};

// Konfiguracja "sprite'a" dla iconset1.jpg
const ICON_SIZE = 30; // Rozmiar wyświetlanej ikony w pasku
const IMAGE_WIDTH = 120; // Całkowita szerokość pliku (do dostosowania!)
const IMAGE_HEIGHT = 30; // Całkowita wysokość pliku (do dostosowania!)

const getIconOffset = (routeName: string) => {
  // Przesunięcia (offsety) dla poszczególnych ikon wewnątrz pliku iconset1.jpg.
  // Założenie domyślne: 4 ikony w jednym rzędzie. Skorygować wartości w zależności od pliku.
  const offsets: Record<string, { x: number, y: number }> = {
    'Home': { x: 0, y: 0 },
    'Mapa': { x: -ICON_SIZE, y: 0 },
    'Wydarzenia': { x: -ICON_SIZE * 2, y: 0 },
    'Profil': { x: -ICON_SIZE * 3, y: 0 }
  };

  return offsets[routeName] ?? { x: 0, y: 0 };
};

// for authenticated users
const MainTabs = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerStyle: { height: 70 },
        headerTitleAlign: "center",
        tabBarStyle: { height: 70 },
        tabBarItemStyle: { margin: 8, borderRadius: 10 },

        headerRight: () => (
          <View style={{ flexDirection: 'row' }}>
            <TouchableOpacity style={{ marginHorizontal: 20 }}>
              <Ionicons name={'search'} size={28} />
            </TouchableOpacity>
            <TouchableOpacity style={{ marginHorizontal: 20 }}>
              <Ionicons name={'notifications'} size={28} />
            </TouchableOpacity>
          </View>
        ),

        tabBarIcon: ({ focused }) => {
          const offset = getIconOffset(route.name);
          return (
            <View style={{
              width: ICON_SIZE,
              height: ICON_SIZE,
              overflow: 'hidden',
              opacity: focused ? 1 : 0.4
            }}>
              <Image
                source={require('../../assets/iconset1.jpg')}
                style={{
                  width: IMAGE_WIDTH,
                  height: IMAGE_HEIGHT,
                  transform: [
                    { translateX: offset.x },
                    { translateY: offset.y }
                  ]
                }}
                resizeMode="cover"
              />
            </View>
          );
        },
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Mapa" component={MapScreen} />
      <Tab.Screen name="Wydarzenia" component={EventStack} />
      <Tab.Screen name="Profil" component={ProfileStack} />
    </Tab.Navigator>
  );
};

// root navigator
const AppNavigator = () => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <ActivityIndicator size="large" color="#0000ff" />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>

         {!isAuthenticated ? (
          <Stack.Screen name="Auth" component={AuthStack} />
        ) : (
          <Stack.Screen name="Main" component={MainTabs} />
        )} 
      </Stack.Navigator>
    </NavigationContainer>
  );
};


export default AppNavigator;


