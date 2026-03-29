import React from "react";
import { SafeAreaView, StyleSheet, Text, View } from "react-native";
import { THEME } from "../../utils/constants";

const EventFilters = () => {
  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.container}>
        <Text style={styles.title}>Filtrowanie wydarzen</Text>
        <Text style={styles.subtitle}>Placeholder ekranu filtrow</Text>
      </View>
    </SafeAreaView>
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

export default EventFilters;
