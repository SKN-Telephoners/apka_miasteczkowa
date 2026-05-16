import React from "react";
import { SafeAreaView, ScrollView, StyleSheet, Text, TouchableOpacity, View, ActivityIndicator } from "react-native";
import { useRoute, useNavigation } from "@react-navigation/native";
import EventCard from "../../components/EventCard";
import { THEME } from "../../utils/constants";
import { Event } from "../../types";
import { useTheme } from "../../contexts/ThemeContext";
import AppIcon from "../../components/AppIcon";
const META_ICON_SIZE = 18;

const EventPreviewScreen = () => {
    const { colors } = useTheme();
    const styles = createStyles(colors);
    const route = useRoute<any>();
    const navigation = useNavigation<any>();
    const [event, setEvent] = React.useState<Event | undefined>(route?.params?.event);
    const [isLoading, setIsLoading] = React.useState<boolean>(false);
    const [errorMsg, setErrorMsg] = React.useState<string | null>(null);

    const eventId = route?.params?.event_id;
    const screenTitle = route?.params?.screenTitle || "Podgląd wydarzenia";
    const allowEdit = Boolean(route?.params?.allowEdit);

    React.useEffect(() => {
        if (!event && eventId) {
            let isMounted = true;
            setIsLoading(true);

            import("../../services/events").then(({ getEventById }) => {
                getEventById(eventId)
                    .then(data => {
                        if (isMounted) setEvent(data);
                    })
                    .catch(err => {
                        console.error("Błąd podczas pobierania wydarzenia:", err);
                        if (isMounted) setErrorMsg("Nie udało się załadować wydarzenia.");
                    })
                    .finally(() => {
                        if (isMounted) setIsLoading(false);
                    });
            });

            return () => {
                isMounted = false;
            };
        }
    }, [event, eventId]);

    React.useLayoutEffect(() => {
        navigation.setOptions?.({
            title: event?.name || screenTitle,
            headerStyle: { backgroundColor: colors.background },
            headerTintColor: colors.text,
            headerTitleStyle: { color: colors.text },
            headerRight:
                allowEdit && event
                    ? () => (
                        <TouchableOpacity
                            onPress={() => navigation.navigate("EditEvent", { event })}
                            style={{ marginRight: 16, width: META_ICON_SIZE, height: META_ICON_SIZE, overflow: "hidden" }}
                            activeOpacity={0.8}
                            accessibilityLabel="Edytuj wydarzenie"
                        >
                            <AppIcon name="Edit" size={META_ICON_SIZE} />
                        </TouchableOpacity>
                    )
                    : undefined,
        });
    }, [navigation, colors.background, colors.text, screenTitle, allowEdit, event]);

    if (isLoading) {
        return (
            <SafeAreaView style={styles.screen}>
                <View style={styles.emptyState}>
                    <ActivityIndicator size="large" color={colors.primary} />
                    <Text style={[styles.emptySubtitle, { marginTop: 12 }]}>Ładowanie wydarzenia...</Text>
                </View>
            </SafeAreaView>
        );
    }

    if (!event) {
        return (
            <SafeAreaView style={styles.screen}>
                <View style={styles.emptyState}>
                    <Text style={styles.emptyTitle}>Brak danych podglądu</Text>
                    <Text style={styles.emptySubtitle}>{errorMsg || "Wróć do ekranu głównego i spróbuj ponownie."}</Text>
                </View>
            </SafeAreaView>
        );
    }

    return (
        <SafeAreaView style={styles.screen}>
            <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
                <EventCard item={event} showActions={false} />
            </ScrollView>
        </SafeAreaView>
    );
};

const createStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({
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
    },
    emptySubtitle: {
        ...THEME.typography.text,
        color: colors.icon,
        textAlign: "center",
    },
});

export default EventPreviewScreen;