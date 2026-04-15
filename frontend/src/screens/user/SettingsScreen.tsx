import React from "react";
import { View, Text, StyleSheet, Switch, ScrollView, TouchableOpacity, Alert } from "react-native";
import { useTheme } from "../../contexts/ThemeContext";
import { THEME } from "../../utils/constants";
import { useAuth } from "../../contexts/AuthContext";
import Button from "../../components/Button"

const SettingsScreen = () => {

      const { logout } = useAuth();
      const { isDark, toggleTheme, colors } = useTheme();

    const handleSoftDelete = () => {
        Alert.alert(
            "Zawieszenie konta",
            "Czy na pewno chcesz zawiesić konto? Twój profil i dane zostaną ukryte do momentu ponownej aktywacji przez administratora.",
            [
                { text: "Anuluj", style: "cancel" },
                { 
                    text: "Dezaktywuj", 
                    style: "destructive",
                    onPress: () => {
                        // Tutaj w przyszłości dodamy call do backendu "softDeleteAccount()"
                        Alert.alert("Informacja", "Funkcja tymczasowo niedostępna (wymaga podłączenia backendu).");
                    }
                }
            ]
        );
    };

    return (
        <ScrollView style={[styles.container, { backgroundColor: colors.background }]} contentContainerStyle={styles.contentContainer}>
            
            <View style={styles.sectionHeader}>
                <Text style={styles.sectionTitle}>WYGLĄD APLIKACJI</Text>
            </View>
            <View style={[styles.card, { backgroundColor: colors.border, borderColor: colors.border }]}>
                <View style={[styles.row, { borderBottomWidth: 0 }]}>
                    <Text style={[styles.text, { color: colors.text, fontSize: 16 }]}>Tryb Ciemny</Text>
                    <Switch
                        trackColor={{ false: "#767577", true: colors.highlight }}
                        thumbColor={isDark ? "#f5dd4b" : "#f4f3f4"}
                        ios_backgroundColor="#3e3e3e"
                        onValueChange={toggleTheme}
                        value={isDark}
                    />
                </View>
            </View>

            <View style={styles.sectionHeader}>
                <Text style={styles.sectionTitle}>ZARZĄDZANIE KONTEM</Text>
            </View>
            <View style={[styles.card, { backgroundColor: colors.border, borderColor: colors.border }]}>
                <TouchableOpacity style={[styles.row, { borderBottomWidth: 0 }]} onPress={handleSoftDelete}>
                    <Text style={[styles.text, { color: colors.aghRed, fontSize: 16, fontWeight: "500" }]}>Zawieś konto</Text>
                </TouchableOpacity>
            </View>

            {/* Logout Button directly under the cards */}
            <View style={styles.logoutContainer}>
                <Button title="Wyloguj się" onPress={logout} style={{ backgroundColor: colors.icon }} />
            </View>

        </ScrollView>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    contentContainer: {
        paddingHorizontal: THEME.spacing.m,
        paddingTop: THEME.spacing.l,
        paddingBottom: THEME.spacing.xl,
    },
    sectionHeader: {
        marginBottom: 8,
        marginLeft: 4,
        marginTop: THEME.spacing.m,
    },
    sectionTitle: {
        fontSize: 13,
        fontWeight: "600",
        color: "#888888",
        textTransform: "uppercase",
        letterSpacing: 0.5,
    },
    card: {
        borderRadius: 12,
        overflow: "hidden",
        marginBottom: THEME.spacing.m,
        borderWidth: 1,
    },
    row: {
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        paddingVertical: 14,
        paddingHorizontal: 16,
        borderBottomColor: 'rgba(150, 150, 150, 0.2)',
    },
    text: {
        ...THEME.typography.text,
    },
    logoutContainer: {
        marginTop: THEME.spacing.xl * 1.5,
        alignItems: "center",
        width: "100%",
    }
});

export default SettingsScreen;
