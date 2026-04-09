import React from "react";
import { SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRoute, useNavigation } from "@react-navigation/native";
import EventCard from "../../components/EventCard";
import { THEME } from "../../utils/constants";
import { Event } from "../../types";

const EventPreviewScreen = () => {
    const route = useRoute<any>();
    const navigation = useNavigation<any>();
    const event = route?.params?.event as Event | undefined;

    React.useLayoutEffect(() => {
        navigation.setOptions?.({ title: "Podgląd wydarzenia" });
    }, [navigation]);

    if (!event) {
        return (
            <SafeAreaView style={styles.screen}>
                <View style={styles.emptyState}>
                    <Text style={styles.emptyTitle}>Brak danych podglądu</Text>
                    <Text style={styles.emptySubtitle}>Wróć do edycji i spróbuj ponownie.</Text>
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

const styles = StyleSheet.create({
    screen: {
        flex: 1,
        backgroundColor: THEME.colors.lm_bg,
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
        color: THEME.colors.lm_ico,
        textAlign: "center",
    },
});

export default EventPreviewScreen;