import { createStackNavigator } from "@react-navigation/stack";
import React from "react";
import EventScreen from "../screens/home/EventScreen";
import EventCommentsScreen from "../screens/event/EventCommentsScreen";
import EventForm from "../screens/event/EventForm";
import EventMap from "../screens/event/EventMap";
import EventPreviewScreen from "../screens/event/EventPreviewScreen";
import EventFilters from "../screens/event/EventFilters";
import EventInviteUsersScreen from "../screens/event/EventInviteUsersScreen";
import { useTheme } from "../contexts/ThemeContext";

const Stack = createStackNavigator();

const EventStack = () => {
  const { colors } = useTheme();

  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: colors.background },
        headerTintColor: colors.text,
        headerTitleStyle: { color: colors.text },
        headerShadowVisible: false,
      }}
    >
      <Stack.Screen name="EventScreen" component={EventScreen} options={{ headerShown: false }} />
      <Stack.Screen name="EventComments" component={EventCommentsScreen} options={{ title: "Komentarze" }} />
      <Stack.Screen name="AddEvent" component={EventForm} options={{ title: "Dodaj wydarzenie" }} />
      <Stack.Screen name="EditEvent" component={EventForm} options={{title: "Edytuj wydarzenie"}} />
      <Stack.Screen name="EventMap" component={EventMap} options={{ title: "Wybierz lokalizację" }} />
      <Stack.Screen name="EventInviteUsers" component={EventInviteUsersScreen} options={{ title: "Zaproś znajomych" }} />
      <Stack.Screen name="EventPreview" component={EventPreviewScreen} options={{ title: "Podgląd" }} />
      <Stack.Screen name="EventFilters" component={EventFilters} options={{title: "Filtrowanie"}} />
    </Stack.Navigator>
  );
};

export default EventStack;
