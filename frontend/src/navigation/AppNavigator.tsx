import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import {
  NavigationContainer,
  getFocusedRouteNameFromRoute,
} from "@react-navigation/native";
import { createStackNavigator } from "@react-navigation/stack";
import {
  ActivityIndicator,
  TouchableOpacity,
  View,
} from "react-native";
import AppIcon from "../components/AppIcon";
import Avatar from "../components/Avatar";
import { useAuth } from "../contexts/AuthContext";
import { useFriends } from "../contexts/FriendsContext";
import { useTheme } from "../contexts/ThemeContext";
import { useUser } from "../contexts/UserContext";
import LoginScreen from "../screens/auth/LoginScreen";
import RegisterScreen from "../screens/auth/RegisterScreen";
import ResetPasswordScreen from "../screens/auth/ResetPasswordScreen";
import WelcomeScreen from "../screens/auth/WelcomeScreen";
import EventDetailsScreen from "../screens/event/EventDetailsScreen";
import HomeScreen from "../screens/home/HomeScreen";
import MapScreen from "../screens/home/MapScreen";
import NotificationsScreen from "../screens/home/NotificationsScreen";
import UserScreen from "../screens/user/UserScreen";
import EventStack from "./EventStack";
import ProfileStack from "./ProfileStack";

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

const ICON_SIZE = 30;
const SearchScreen = require("../screens/user/SearchScreen").default;

const ROUTE_ICON_MAP: Record<string, string> = {
  "Przewodnik po miasteczku": "Home",
  Mapa: "Map",
  Wydarzenia: "Events",
};

// for authenticated users
const MainTabs = () => {
  const { colors } = useTheme();
  const { user } = useUser();
  const { incomingRequests } = useFriends();
  const hasNotifications = incomingRequests.length > 0;

  return (
    <Tab.Navigator
      initialRouteName="Mapa"
      screenOptions={({ route, navigation }) => ({
        headerStyle: {
          height: 50,
          elevation: 0,
          shadowOpacity: 0,
          borderBottomWidth: 0,
          backgroundColor: colors.background,
        },
        headerTintColor: colors.text,
        headerTitleStyle: { color: colors.text },
        headerShadowVisible: false,
        headerTitleAlign: "left",
        tabBarStyle: {
          height: 60,
          backgroundColor: colors.background,
          borderTopColor: colors.border,
        },
        tabBarItemStyle: { margin: 8, borderRadius: 10 },
        tabBarShowLabel: false,
        tabBarActiveTintColor: colors.highlight,
        tabBarInactiveTintColor: colors.icon,

        headerRight: () => {
          if (route.name === "Przewodnik po miasteczku") {
            return (
              <View style={{ flexDirection: "row" }}>
                <TouchableOpacity
                  style={{ marginHorizontal: 20 }}
                  onPress={() => navigation.navigate("Search")}
                >
                  <AppIcon name="Search" size={28} />
                </TouchableOpacity>
                <TouchableOpacity
                  style={{ marginHorizontal: 20 }}
                  onPress={() => navigation.navigate("Notifications")}
                >
                  <View>
                    <AppIcon name="Bell" size={28} focused={hasNotifications} />
                    {hasNotifications && (
                      <View
                        style={{
                          position: "absolute",
                          top: 0,
                          right: 0,
                          width: 10,
                          height: 10,
                          borderRadius: 5,
                          backgroundColor: colors.highlight,
                          borderWidth: 1,
                          borderColor: colors.background,
                        }}
                      />
                    )}
                  </View>
                </TouchableOpacity>
              </View>
            );
          }

          if (route.name === "Mapa") {
            return (
              <View style={{ flexDirection: "row", gap: 40, marginRight: 20 }} pointerEvents="box-none">
                <TouchableOpacity onPress={() => ({})}>
                  <AppIcon name="Search" size={28} />
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={() => navigation.navigate("Notifications")}
                >
                  <AppIcon name="Bell" size={28} focused={hasNotifications} />
                  {hasNotifications && (
                    <View
                      style={{
                        position: "absolute",
                        top: 0,
                        right: 0,
                        width: 10,
                        height: 10,
                        borderRadius: 5,
                        backgroundColor: colors.highlight,
                        borderWidth: 1,
                        borderColor: colors.background,
                      }}
                    />
                  )}
                </TouchableOpacity>
              </View>
            );
          }

          if (route.name !== "Wydarzenia") {
            return null;
          }

          const focusedRoute =
            getFocusedRouteNameFromRoute(route) ?? "EventScreen";
          if (focusedRoute !== "EventScreen") {
            return null;
          }

          return (
            <View style={{ flexDirection: "row", alignItems: "center" }}>
              <TouchableOpacity
                style={{ marginHorizontal: 20 }}
                onPress={() =>
                  navigation.navigate("Wydarzenia", { screen: "AddEvent" })
                }
              >
                <AppIcon name="Plus" size={ICON_SIZE} />
              </TouchableOpacity>
              <TouchableOpacity
                style={{ marginHorizontal: 20 }}
                onPress={() => navigation.navigate("Search")}
              >
                <AppIcon name="Search" size={28} />
              </TouchableOpacity>
              <TouchableOpacity
                style={{ marginHorizontal: 20 }}
                onPress={() => navigation.navigate("Notifications")}
              >
                <View>
                  <AppIcon name="Bell" size={28} focused={hasNotifications} />
                  {hasNotifications && (
                    <View
                      style={{
                        position: "absolute",
                        top: 0,
                        right: 0,
                        width: 10,
                        height: 10,
                        borderRadius: 5,
                        backgroundColor: colors.highlight,
                        borderWidth: 1,
                        borderColor: colors.background,
                      }}
                    />
                  )}
                </View>
              </TouchableOpacity>
            </View>
          );
        },

        tabBarIcon: ({ focused }) => {
          if (route.name === "Profil") {
            const uri =
              user?.profile_picture?.url ||
              (typeof user?.profile_picture === "string"
                ? user?.profile_picture
                : undefined);
            return (
              <View style={{ opacity: focused ? 1 : 0.75 }}>
                <Avatar
                  uri={uri}
                  size={32}
                  style={{
                    borderWidth: 2,
                    borderColor: focused ? colors.highlight : "transparent",
                  }}
                />
              </View>
            );
          }
          return (
            <AppIcon
              name={ROUTE_ICON_MAP[route.name] || "Home"}
              focused={focused}
            />
          );
        },
      })}
    >
      <Tab.Screen name="Przewodnik po miasteczku" component={HomeScreen} />
      <Tab.Screen name="Mapa" component={MapScreen} />
      <Tab.Screen name="Wydarzenia" component={EventStack} />
      <Tab.Screen name="Profil" component={ProfileStack} />
    </Tab.Navigator>
  );
};

// root navigator
const AppNavigator = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const { colors, isDark } = useTheme();

  const navigationTheme = {
    dark: isDark,
    colors: {
      primary: colors.highlight,
      background: colors.background,
      card: colors.background,
      text: colors.text,
      border: colors.border,
      notification: colors.highlight,
    },
    fonts: {
      regular: { fontFamily: "System", fontWeight: "400" as const },
      medium: { fontFamily: "System", fontWeight: "500" as const },
      bold: { fontFamily: "System", fontWeight: "700" as const },
      heavy: { fontFamily: "System", fontWeight: "800" as const },
    },
  };

  if (isLoading) {
    return (
      <View
        style={{
          flex: 1,
          justifyContent: "center",
          alignItems: "center",
          backgroundColor: colors.background,
        }}
      >
        <ActivityIndicator size="large" color={colors.highlight} />
      </View>
    );
  }

  return (
    <NavigationContainer theme={navigationTheme}>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {!isAuthenticated ? (
          <Stack.Screen name="Auth" component={AuthStack} />
        ) : (
          <Stack.Group>
            <Stack.Screen name="Main" component={MainTabs} />
            <Stack.Screen
              name="Notifications"
              component={NotificationsScreen}
              options={{
                headerShown: true,
                headerTitle: "Powiadomienia",
                headerStyle: { backgroundColor: colors.background },
                headerTintColor: colors.text,
                headerTitleStyle: { color: colors.text },
              }}
            />
            <Stack.Screen
              name="Search"
              component={SearchScreen}
              options={{
                headerShown: true,
                headerTitle: "Szukaj użytkowników",
                headerStyle: { backgroundColor: colors.background },
                headerTintColor: colors.text,
                headerTitleStyle: { color: colors.text },
              }}
            />
            <Stack.Screen
              name="UserScreen"
              component={UserScreen}
              options={{
                headerShown: true,
                headerTitle: "Profil użytkownika",
                headerStyle: { backgroundColor: colors.background },
                headerTintColor: colors.text,
                headerTitleStyle: { color: colors.text },
              }}
            />
            <Stack.Screen
              name="EventDetails"
              component={EventDetailsScreen}
              options={{
                headerShown: true,
                headerTitle: "Szczegóły wydarzenia",
                headerStyle: { backgroundColor: colors.background },
                headerTintColor: colors.text,
                headerTitleStyle: { color: colors.text },
              }}
            />
          </Stack.Group>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default AppNavigator;
