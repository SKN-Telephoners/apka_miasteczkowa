import React from "react";
import { SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";
import { useNavigation, useRoute } from "@react-navigation/native";
import EventCard from "../../components/EventCard";
import { Event } from "../../types";
import { useTheme } from "../../contexts/ThemeContext";
import { THEME } from "../../utils/constants";

const EventDetailsScreen = () => {
    const { colors } = useTheme();
    const styles = React.useMemo(() => createStyles(colors), [colors]);
    const navigation = useNavigation<any>();
    const route = useRoute<any>();
    const event = route.params?.event as Event | undefined;

    React.useLayoutEffect(() => {
        navigation.setOptions?.({
            title: event?.name || "Szczegóły wydarzenia",
            headerStyle: { backgroundColor: colors.background },
            headerTintColor: colors.text,
            headerTitleStyle: { color: colors.text },
        });
    }, [navigation, colors.background, colors.text, event?.name]);

    if (!event) {
        return (
            <SafeAreaView style={styles.screen}>
                <View style={styles.emptyState}>
                    <Text style={styles.emptyTitle}>Brak danych wydarzenia</Text>
                    <Text style={styles.emptySubtitle}>Wróć do mapy i wybierz inne wydarzenie.</Text>
                </View>
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView style={[styles.screen, { backgroundColor: colors.background }]}>
            <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
                <EventCard item={event} showActions={false} showMapLabel={false} />
            </ScrollView>
        </SafeAreaView>
    );
};

const createStyles = (colors: typeof THEME.colors.light) =>
    StyleSheet.create({
        screen: {
            flex: 1,
            backgroundColor: colors.background,
        },
        content: {
            padding: 12,
        },
        emptyState: {
            flex: 1,
            justifyContent: "center",
            alignItems: "center",
            paddingHorizontal: 24,
        },
        emptyTitle: {
            ...THEME.typography.eventTitle,
            textAlign: "center",
            marginBottom: 8,
            color: colors.text,
        },
        emptySubtitle: {
            ...THEME.typography.text,
            textAlign: "center",
            color: colors.icon,
        },
    });

export default EventDetailsScreen;