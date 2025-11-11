import { NavigationContainer } from "@react-navigation/native";
import { createStackNavigator } from "@react-navigation/stack";
import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import WelcomeScreen from "../screens/auth/WelcomeScreen";
import LoginScreen from "../screens/auth/LoginScreen";
import RegisterScreen from "../screens/auth/RegisterScreen";
import ResetPasswordScreen from "../screens/auth/ResetPasswordScreen";
import HomeScreen from "../screens/home/HomeScreen";
import MapScreen from "../screens/home/MapScreen";
import EventScreen from "../screens/home/EventScreen";
import ProfileScreen from "../screens/home/ProfileScreen";
import { Ionicons } from "@expo/vector-icons";
import type { ComponentProps } from "react";
import { useAuth } from "../contexts/AuthContext";
import { ActivityIndicator, View, TouchableOpacity } from "react-native";

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

const getIconName = (routeName: string): ComponentProps<typeof Ionicons>['name'] => {
  const iconMap: Record<string, ComponentProps<typeof Ionicons>['name']> = {
    'Home': 'home',
    'Mapa': 'map',
    'Wydarzenia': 'locate',
    'Profil': 'person'
  };
  
  return iconMap[routeName] ?? 'home';
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

        tabBarIcon: ({ color }) => {
          const iconName = getIconName(route.name)
          return <Ionicons name={iconName} size={28} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Mapa" component={MapScreen} />
      <Tab.Screen name="Wydarzenia" component={EventScreen} />
      <Tab.Screen name="Profil" component={ProfileScreen} />
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


