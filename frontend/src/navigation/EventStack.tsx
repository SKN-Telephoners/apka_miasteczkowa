import { createStackNavigator } from "@react-navigation/stack";
import React from "react";
import { SafeAreaView, StyleSheet, Text, View } from "react-native";
import EventScreen from "../screens/home/EventScreen";
import EventCommentsScreen from "../screens/event/EventCommentsScreen";
import AddEvent from "../screens/event/AddEvent";
import EditEvent from "../screens/event/EditEvent";
import EventPreviewScreen from "../screens/event/EventPreviewScreen";
import EventFilters from "../screens/event/EventFilters";
import { THEME } from "../utils/constants";
import { useTheme } from "../contexts/ThemeContext";

const Stack = createStackNavigator();

const CommentFiltersScreen = () => {
  const { colors } = useTheme();
  const styles = createStyles(colors);

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.container}>
        <Text style={styles.title}>Filtrowanie komentarzy</Text>
        <Text style={styles.subtitle}>Placeholder filtrowania komentarzy dla posta</Text>
      </View>
    </SafeAreaView>
  );
};

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
      <Stack.Screen name="AddEvent" component={AddEvent} options={{ title: "Dodaj wydarzenie" }} />
      <Stack.Screen name="EditEvent" component={EditEvent} options={{title: "Edytuj wydarzenie"}} />
      <Stack.Screen name="EventPreview" component={EventPreviewScreen} options={{ title: "Podgląd" }} />
      <Stack.Screen name="EventFilters" component={EventFilters} options={{title: "Filtrowanie"}} />
      <Stack.Screen name="CommentFilters" component={CommentFiltersScreen} options={{title: "Filtry komentarzy"}} />
    </Stack.Navigator>
  );
};

const createStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
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
    color: colors.icon,
    textAlign: "center",
  },
});

export default EventStack;
