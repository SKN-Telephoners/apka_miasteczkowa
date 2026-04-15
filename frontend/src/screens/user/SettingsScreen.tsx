import React from "react";
import { View, Text, StyleSheet, Switch } from "react-native";
import { useTheme } from "../../contexts/ThemeContext";
import { THEME } from "../../utils/constants";
import { useAuth } from "../../contexts/AuthContext";
import Button from "../../components/Button"

const SettingsScreen = () => {

      const { logout } = useAuth();
      const { isDark, toggleTheme, colors } = useTheme();

    return (
        <View style={[styles.container, { backgroundColor: colors.background }]}>
            <View style={styles.themeRow}>
                <Text style={[styles.title, { color: colors.text }]}>Motyw</Text>
                <View style={styles.switchGroup}>
                    <Text style={[styles.text, { color: colors.text }]}>Jasny</Text>
                    <Switch
                        trackColor={{ false: "#767577", true: colors.highlight }}
                        thumbColor={isDark ? "#f5dd4b" : "#f4f3f4"}
                        ios_backgroundColor="#3e3e3e"
                        onValueChange={toggleTheme}
                        value={isDark}
                    />
                    <Text style={[styles.text, { color: colors.text }]}>Ciemny</Text>
                </View>
            </View>

            <Button title="Wyloguj" onPress={logout} />
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: "center",
        alignItems: "flex-start",
        padding: THEME.spacing.m,
    },
    text: {
        ...THEME.typography.text,
    },
    themeRow: {
        width: "100%",
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: THEME.spacing.l,
    },
    switchGroup: {
        flexDirection: "row",
        alignItems: "center",
        gap: THEME.spacing.s,
    },
    title: {
        ...THEME.typography.title,
    },
});

export default SettingsScreen;
