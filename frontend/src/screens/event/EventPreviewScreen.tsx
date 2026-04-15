import React from "react";
import { SafeAreaView, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useRoute, useNavigation } from "@react-navigation/native";
import EventCard from "../../components/EventCard";
import { THEME } from "../../utils/constants";
import { Event } from "../../types";
import { useTheme } from "../../contexts/ThemeContext";
import SvgSpriteIcon from "../../components/SvgSpriteIcon";

const BASE_TILE_SIZE = 30;
const META_ICON_SIZE = 18;
const EDIT_MENU_ICON_OFFSET = { x: -BASE_TILE_SIZE * 2, y: -BASE_TILE_SIZE };

const EventPreviewScreen = () => {
    const { colors } = useTheme();
    const styles = createStyles(colors);
    const route = useRoute<any>();
    const navigation = useNavigation<any>();
    const event = route?.params?.event as Event | undefined;
    const screenTitle = route?.params?.screenTitle || "Podgląd wydarzenia";
    const allowEdit = Boolean(route?.params?.allowEdit);

    React.useLayoutEffect(() => {
        navigation.setOptions?.({
            title: screenTitle,
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
                            <SvgSpriteIcon set={2} size={META_ICON_SIZE} offsetX={EDIT_MENU_ICON_OFFSET.x} offsetY={EDIT_MENU_ICON_OFFSET.y} />
                        </TouchableOpacity>
                    )
                    : undefined,
        });
    }, [navigation, colors.background, colors.text, colors.highlight, screenTitle, allowEdit, event]);

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