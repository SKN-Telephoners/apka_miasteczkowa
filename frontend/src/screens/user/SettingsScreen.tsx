import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { useTheme } from "../../contexts/ThemeContext";
import { THEME } from "../../utils/constants";

const SettingsScreen = () => {
    const { colors } = useTheme();

    return (
        <View style={[styles.container, { backgroundColor: colors.background }]}>
            <Text style={[styles.text, { color: colors.text }]}>
                Ustawienia profilu pojawią się tutaj...
            </Text>
            <Text style={[styles.subText, { color: colors.icon }]}>
                (np. zmiana hasła, usunięcie konta)
            </Text>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: "center",
        alignItems: "center",
        padding: THEME.spacing.m,
    },
    text: {
        fontSize: 18,
        fontWeight: "bold",
    },
    subText: {
        fontSize: 14,
        marginTop: 10,
    }
});

export default SettingsScreen;
