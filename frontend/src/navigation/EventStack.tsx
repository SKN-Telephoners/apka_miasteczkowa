import { createStackNavigator } from "@react-navigation/stack";
import React from "react";
import { SafeAreaView, StyleSheet, Text, View } from "react-native";
import EventScreen from "../screens/home/EventScreen";
import EventDetails from "../screens/event/EventDetails";
import EventCommentsScreen from "../screens/event/EventCommentsScreen";
import AddEvent from "../screens/event/AddEvent";
import EditEvent from "../screens/event/EditEvent";
import { THEME } from "../utils/constants";

const Stack = createStackNavigator();

const EventFiltersScreen = () => {
  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.container}>
        <Text style={styles.title}>Filtrowanie wydarzen</Text>
        <Text style={styles.subtitle}>Placeholder ekranu filtrow</Text>
      </View>
    </SafeAreaView>
  );
};

const EventStack = () => {
  return (
    <Stack.Navigator>
      <Stack.Screen name="EventScreen" component={EventScreen} options={{ headerShown: false }} />
      <Stack.Screen name="EventDetails" component={EventDetails} options={{ title: "Szczegóły Wydarzenia" }} />
      <Stack.Screen name="EventComments" component={EventCommentsScreen} options={{ title: "Komentarze" }} />
      <Stack.Screen name="AddEvent" component={AddEvent} options={{ title: "Dodaj wydarzenie" }} />
      <Stack.Screen name="EditEvent" component={EditEvent} options={{title: "Edytuj wydarzenie"}} />
      <Stack.Screen name="EventFilters" component={EventFiltersScreen} options={{title: "Filtrowanie"}} />
    </Stack.Navigator>
  );
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: THEME.colors.lm_bg,
  },
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 20,
  },
  title: {
    ...THEME.typography.eventTitle,
    textAlign: "center",
    marginBottom: 8,
  },
  subtitle: {
    ...THEME.typography.text,
    color: THEME.colors.lm_ico,
    textAlign: "center",
  },
});

export default EventStack;
