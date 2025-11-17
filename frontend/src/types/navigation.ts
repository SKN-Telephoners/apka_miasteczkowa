import { StackNavigationProp } from "@react-navigation/stack";
import { BottomTabNavigationProp } from "@react-navigation/bottom-tabs";

export type AuthStackParamList = {
  Welcome: undefined;
  Login: undefined;
  Register: undefined;
  ResetPassword: undefined;
};

export type MainTabParamList = {
  Home: undefined;
  // add more tabs here
};

export type AuthScreenNavigationProp = StackNavigationProp<AuthStackParamList>;
export type MainScreenNavigationProp =
  BottomTabNavigationProp<MainTabParamList>;
