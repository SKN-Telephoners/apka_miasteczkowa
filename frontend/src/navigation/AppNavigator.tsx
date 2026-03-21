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
import { THEME } from "../utils/constants";

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
const ICON_SIZE = 30;
// Skoro ikony są rozłożone w wierszach (górny, na środku) i kolumnach (lewa, środek, prawa),
// założyłem że obrazek to siatka 3x3. Gdyby rozmiary się nie zgadzały, dopasuj IMAGE_WIDTH i IMAGE_HEIGHT.
const IMAGE_WIDTH = 90;
const IMAGE_HEIGHT = 90;
const SEARCH_ICON_OFFSET = { x: -ICON_SIZE * 2, y: 0 };

const getIconOffset = (routeName: string) => {
  const offsets: Record<string, { x: number, y: number }> = {
    // "prawy górny róg" (X: po prawej, Y: u góry)
    'Home': { x: -ICON_SIZE * 2, y: 0 },
    // "na środku po lewej" (X: po lewej, Y: na środku)
    'Mapa': { x: 0, y: -ICON_SIZE },
    // "na samym środku" (X: na środku, Y: na środku)
    'Wydarzenia': { x: -ICON_SIZE, y: -ICON_SIZE },
    // "po prawej na środku" (X: po prawej, Y: na środku)
    'Profil': { x: -ICON_SIZE * 2, y: -ICON_SIZE }
  };

  return offsets[routeName] ?? { x: 0, y: 0 };
};

// for authenticated users
const MainTabs = () => {
  return (
    <Tab.Navigator
      initialRouteName="Mapa"
      screenOptions={({ route, navigation }) => ({
        headerStyle: { height: 50, elevation: 0, shadowOpacity: 0, borderBottomWidth: 0 },
        headerShadowVisible: false,
        headerTitleAlign: "left",
        tabBarStyle: { height: 60 },
        tabBarItemStyle: { margin: 8, borderRadius: 10 },
        tabBarShowLabel: false,
        tabBarActiveTintColor: THEME.colors.transparentOrange,

        headerRight: () => (
          <View style={{ flexDirection: 'row' }}>
            <TouchableOpacity
              style={{ marginHorizontal: 20 }}
              onPress={() => navigation.navigate('Wydarzenia', { screen: 'AddEvent' })}
            >
              <View style={{ width: ICON_SIZE, height: ICON_SIZE, overflow: 'hidden' }}>
                <Image
                  source={require('../../assets/iconset2.jpg')}
                  style={{
                    width: IMAGE_WIDTH,
                    height: IMAGE_HEIGHT,
                    transform: [
                      { translateX: SEARCH_ICON_OFFSET.x },
                      { translateY: SEARCH_ICON_OFFSET.y }
                    ]
                  }}
                  resizeMode="cover"
                />
              </View>
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
        <ActivityIndicator size="large" color={THEME.colors.transparentOrange} />
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


