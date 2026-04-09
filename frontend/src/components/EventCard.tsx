import { TouchableOpacity, Text, View, StyleSheet, Alert, Image } from "react-native";
import React, { useEffect, useState } from "react";
import { Event } from "../types";
import { useNavigation } from "@react-navigation/native";
import { THEME } from '../utils/constants';
import Button from "./Button";
import { tokenStorage } from "../utils/storage";
import { joinEvent, leaveEvent } from "../services/events";
import UserCard from "./UserCard";

const parseEventDateTime = (event: Event): Date | null => {
    if (!event?.date || !event?.time) return null;

    const [day, month, year] = event.date.split('.').map(Number);
    const [hours, minutes] = event.time.split(':').map(Number);

    if ([day, month, year, hours, minutes].some(Number.isNaN)) {
        return null;
    }

    return new Date(year, month - 1, day, hours, minutes, 0, 0);
};

const formatCreatedAt = (createdAt?: string): string => {
    if (!createdAt) return "brak daty dodania";

    const date = new Date(createdAt);
    if (Number.isNaN(date.getTime())) {
        return "brak daty dodania";
    }

    const diffMs = Date.now() - date.getTime();
    if (diffMs <= 0) return "chwilę temu";

    const minutes = Math.floor(diffMs / (1000 * 60));
    const hours = Math.floor(diffMs / (1000 * 60 * 60));
    const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const weeks = Math.floor(days / 7);
    const months = Math.floor(days / 30);
    const years = Math.floor(days / 365);

    if (minutes < 60) return "chwilę temu";

    if (hours === 1) return "godzinę temu";
    if (hours < 24) {
        if (hours >= 2 && hours <= 4) return `${hours} godziny temu`;
        return `${hours} godzin temu`;
    }

    if (days === 1) return "1 dzień temu";
    if (days < 7) return `${days} dni temu`;

    if (weeks === 1) return "tydzień temu";
    if (weeks < 5) {
        if (weeks >= 2 && weeks <= 4) return `${weeks} tygodnie temu`;
        return `${weeks} tygodni temu`;
    }

    if (months === 1) return "miesiąc temu";
    if (months < 12) {
        if (months >= 2 && months <= 4) return `${months} miesiące temu`;
        return `${months} miesięcy temu`;
    }

    if (years === 1) return "rok temu";
    if (years >= 2 && years <= 4) return `${years} lata temu`;
    return `${years} lat temu`;
};

const BASE_TILE_SIZE = 30;
const META_ICON_SIZE = 18;
const META_SPRITE_WIDTH = 90;
const META_SPRITE_HEIGHT = 90;
const META_SPRITE_SCALE = META_ICON_SIZE / BASE_TILE_SIZE;
const USERNAME_ICON_SIZE = 22;
const USERNAME_SPRITE_SCALE = USERNAME_ICON_SIZE / BASE_TILE_SIZE;
const USERNAME_ICON_OFFSET = { x: -BASE_TILE_SIZE * 2, y: -BASE_TILE_SIZE };
const MAP_INLINE_ICON_SIZE = 14;
const MAP_INLINE_SPRITE_SCALE = MAP_INLINE_ICON_SIZE / BASE_TILE_SIZE;
const MAP_INLINE_ICON_OFFSET = { x: 0, y: -BASE_TILE_SIZE };
const TRAILING_ICON_SIZE = 24;
const TRAILING_SPRITE_SCALE = TRAILING_ICON_SIZE / BASE_TILE_SIZE;
const HEART_ICON_OFFSET = { x: 0, y: -BASE_TILE_SIZE * 2 };
const COMMENT_ICON_OFFSET = { x: -BASE_TILE_SIZE, y: -BASE_TILE_SIZE * 2 };
const SHARE_ICON_OFFSET = { x: -BASE_TILE_SIZE * 2, y: -BASE_TILE_SIZE * 2 };
const EDIT_MENU_ICON_OFFSET = { x: -BASE_TILE_SIZE * 2, y: -BASE_TILE_SIZE };


const EventCard = ({ item, showActions = true }: { item: Event; showActions?: boolean }) => {
    const navigation = useNavigation<any>();
    const eventDateTime = parseEventDateTime(item);
    const isPastEvent = eventDateTime ? eventDateTime.getTime() < Date.now() : false;
    const [userID, setUserID] = useState('');
    const [isOwner, setIsOwner] = useState(false);
    const [isParticipating, setIsParticipating] = useState(Boolean(item?.is_participating));
    const [isParticipationLoading, setIsParticipationLoading] = useState(false);
    const [participantCount, setParticipantCount] = useState<number>(Number(item?.participant_count ?? 0));

    const isPrivateEvent =
        item?.is_private === true ||
        String(item?.is_private).toLowerCase() === "true";
    const creatorDisplayName = item.creator_username?.trim() || "nieznany użytkownik";
    const createdAtDisplay = formatCreatedAt(item.created_at);

    useEffect(() => {
        const fetchUserID = async () => {
            const id = await tokenStorage.getUserId();
            setUserID(id);
        };

        fetchUserID();
    }, []);

    useEffect(() => {
        setIsOwner(Boolean(userID) && item.creator_id === userID);
    }, [userID, item.creator_id]);

    useEffect(() => {
        setParticipantCount(Number(item?.participant_count ?? 0));
        setIsParticipating(Boolean(item?.is_participating));
    }, [item.participant_count, item.is_participating]);

    const handleJoinEvent = async () => {
        if (isParticipationLoading) return;

        try {
            setIsParticipationLoading(true);

            if (isParticipating) {
                await leaveEvent(item.id);
                setIsParticipating(false);
                setParticipantCount((prev) => Math.max(prev - 1, 0));
            } else {
                await joinEvent(item.id);
                setIsParticipating(true);
                setParticipantCount((prev) => prev + 1);
            }
        } catch (err: any) {
            Alert.alert("Błąd", err?.message || "Nie udało się zaktualizować udziału w wydarzeniu.");
        } finally {
            setIsParticipationLoading(false);
        }
    };

    return (
        <View key={item.id} style={[styles.container, isPastEvent && styles.pastContainer]}>
            <View>
                <View style={styles.eventHeaderRow}>
                    <Text style={[styles.title, styles.eventTitle, isPastEvent && styles.pastTextColor]}>{item.name}</Text>
                    {showActions && isOwner && (
                        <TouchableOpacity
                            onPress={() => navigation.navigate("EditEvent", { event: item })}
                            style={styles.eventMenuButton}
                            activeOpacity={0.8}
                        >
                            <View style={styles.metaIconContainer}>
                                <Image
                                    source={require("../../assets/iconset2.jpg")}
                                    style={[
                                        styles.metaIconImage,
                                        {
                                            transform: [
                                                { translateX: EDIT_MENU_ICON_OFFSET.x * META_SPRITE_SCALE },
                                                { translateY: EDIT_MENU_ICON_OFFSET.y * META_SPRITE_SCALE },
                                            ],
                                        },
                                    ]}
                                    resizeMode="cover"
                                />
                            </View>
                        </TouchableOpacity>
                    )}
                </View>

                {item.pictures?.[0]?.url ? (
                    <Image
                        source={{ uri: item.pictures[0].url }}
                        style={styles.eventImage}
                        resizeMode="cover"
                    />
                ) : null}

                {item.description?.trim() ? (
                    <View style = {styles.description}>
                    <Text style={[styles.text, isPastEvent && styles.pastTextColor]}>
                        {item.description}
                    </Text>
                    </View>
                ) : null}

                <Text style={[styles.textMuted, isPastEvent && styles.pastMetaText]}>• {item.date} • {item.time} </Text>
                <View style={{ flexDirection: "row" }}>
                    <Text style={[styles.textMuted, isPastEvent && styles.pastMetaText]}>• {item.location}</Text>
                    <View style={styles.mapLabelRow}>
                        <Text style={[styles.textHighlight, isPastEvent && styles.pastMetaText]}>• MAPA</Text>
                        <View style={styles.mapInlineIconContainer}>
                            <Image
                                source={require("../../assets/iconset1.jpg")}
                                style={styles.mapInlineIconImage}
                                resizeMode="cover"
                            />
                        </View>
                    </View>
                </View>
                <Text style={[styles.textMuted, isPastEvent && styles.pastMetaText]}>• placeholder_kierunek </Text>

                <View style={{ paddingBottom: 10, paddingTop: 20 }}>
                    <UserCard
                        creatorDisplayName={creatorDisplayName}
                        createdAtDisplay={createdAtDisplay}
                        metaTextColor={isPastEvent ? THEME.colors.lm_txt : undefined}
                    />

                    {showActions && !isOwner && !isPrivateEvent && !isPastEvent && (
                        <View style={styles.joinButtonContainer}>
                            <Button
                                title={isParticipating ? "Opuść wydarzenie" : "Dołącz"}
                                onPress={handleJoinEvent}
                                loading={isParticipationLoading}
                                type={isParticipating ? "secondary" : "primary"}
                            />
                        </View>
                    )}
                    {showActions && (
                    <View style={styles.trailingIconsRow}>
                        <View style={styles.trailingActionItem}>
                            <View style={styles.trailingIconContainer}>
                                <Image
                                    source={require("../../assets/iconset1.jpg")}
                                    style={[
                                        styles.trailingIconImage,
                                        {
                                            transform: [
                                                { translateX: HEART_ICON_OFFSET.x * TRAILING_SPRITE_SCALE },
                                                { translateY: HEART_ICON_OFFSET.y * TRAILING_SPRITE_SCALE },
                                            ],
                                        },
                                    ]}
                                    resizeMode="cover"
                                />
                            </View>
                            <Text style={styles.trailingCountText}>{participantCount}</Text>
                        </View>
                        <TouchableOpacity
                            style={styles.trailingActionItem}
                            onPress={() => navigation.navigate("EventComments", { event: item })}
                            activeOpacity={0.8}
                        >
                            <View style={styles.trailingIconContainer}>
                                <Image
                                    source={require("../../assets/iconset1.jpg")}
                                    style={[
                                        styles.trailingIconImage,
                                        {
                                            transform: [
                                                { translateX: COMMENT_ICON_OFFSET.x * TRAILING_SPRITE_SCALE },
                                                { translateY: COMMENT_ICON_OFFSET.y * TRAILING_SPRITE_SCALE },
                                            ],
                                        },
                                    ]}
                                    resizeMode="cover"
                                />
                            </View>
                            <Text style={styles.trailingCountText}>{Number(item.comment_count ?? 0)}</Text>
                        </TouchableOpacity>
                        <View style={styles.trailingActionItem}>
                            <View style={styles.trailingIconContainer}>
                                <Image
                                    source={require("../../assets/iconset1.jpg")}
                                    style={[
                                        styles.trailingIconImage,
                                        {
                                            transform: [
                                                { translateX: SHARE_ICON_OFFSET.x * TRAILING_SPRITE_SCALE },
                                                { translateY: SHARE_ICON_OFFSET.y * TRAILING_SPRITE_SCALE - 2 },
                                            ],
                                        },
                                    ]}
                                    resizeMode="cover"
                                />
                            </View>
                            <Text style={styles.trailingCountText}>0</Text>
                        </View>
                    </View>
                    )}
                </View>
            </View >
        </View>
    )
}

const styles = StyleSheet.create({

    container: {
        backgroundColor: THEME.colors.lm_bg,
        padding: 20,

    },

    pastContainer: {
        backgroundColor: THEME.colors.lm_ico,
    },

    title: THEME.typography.eventTitle,

    eventHeaderRow: {
        paddingBottom: 10,
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
    },

    eventTitle: {
        flex: 1,
        minWidth: 0,
        paddingRight: 8,
    },

    eventMenuButton: {
        alignItems: "center",
        justifyContent: "center",
        marginLeft: 8,
    },

    description: {
        paddingVertical: 10,
        paddingHorizontal: 5,
    },

    text: THEME.typography.text,

    eventImage: {
        width: "100%",
        height: 220,
        borderRadius: 14,
        marginTop: 8,
        marginBottom: 10,
    },

    textMuted: {
        ...THEME.typography.text,
        color: THEME.colors.lm_ico
    },

    textHighlight: {
        ...THEME.typography.text,
        color: THEME.colors.lm_highlight
    },

    pastTextColor: {
        color: THEME.colors.lm_txt,
    },

    pastMetaText: {
        color: THEME.colors.lm_txt,
    },

    location: {
        fontSize: 18,
        bottom: 2,
        fontWeight: "bold",
        color: THEME.colors.lm_highlight,
    },

    pastLocation: {
        color: THEME.colors.lm_txt,
    },

    joinButtonContainer: {
        paddingTop: 10,
        paddingHorizontal: 60,
    },

    authorInfoContainer: {
        paddingHorizontal: 10,
        flex: 1,
        minWidth: 0,
    },

    authorMetaRow: {
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        width: "100%",
    },

    usernameRow: {
        flexDirection: "row",
        alignItems: "center",
    },

    usernameIconContainer: {
        width: USERNAME_ICON_SIZE,
        height: USERNAME_ICON_SIZE,
        overflow: "hidden",
        marginLeft: 6,
        marginTop: -2,
    },

    usernameIconImage: {
        width: META_SPRITE_WIDTH * USERNAME_SPRITE_SCALE,
        height: META_SPRITE_HEIGHT * USERNAME_SPRITE_SCALE,
        transform: [
            { translateX: USERNAME_ICON_OFFSET.x * USERNAME_SPRITE_SCALE },
            { translateY: USERNAME_ICON_OFFSET.y * USERNAME_SPRITE_SCALE },
        ],
    },

    authorMetaText: {
        flex: 1,
        minWidth: 0,
    },

    metaIconContainer: {
        width: META_ICON_SIZE,
        height: META_ICON_SIZE,
        overflow: "hidden",
        marginLeft: 8,
    },

    metaIconImage: {
        width: META_SPRITE_WIDTH * META_SPRITE_SCALE,
        height: META_SPRITE_HEIGHT * META_SPRITE_SCALE,
        transform: [{ translateX: 0 }, { translateY: 0 }],
    },

    mapLabelRow: {
        flexDirection: "row",
        alignItems: "center",
    },

    mapInlineIconContainer: {
        width: MAP_INLINE_ICON_SIZE,
        height: MAP_INLINE_ICON_SIZE,
        overflow: "hidden",
        marginLeft: 4,
    },

    mapInlineIconImage: {
        width: META_SPRITE_WIDTH * MAP_INLINE_SPRITE_SCALE,
        height: META_SPRITE_HEIGHT * MAP_INLINE_SPRITE_SCALE,
        transform: [
            { translateX: MAP_INLINE_ICON_OFFSET.x * MAP_INLINE_SPRITE_SCALE },
            { translateY: MAP_INLINE_ICON_OFFSET.y * MAP_INLINE_SPRITE_SCALE },
        ],
    },

    trailingIconsRow: {
        flexDirection: "row",
        justifyContent: "flex-start",
        alignSelf: "flex-start",
        marginTop: 20,
    },

    trailingActionItem: {
        flexDirection: "row",
        alignItems: "center",
        marginRight: 16,
    },

    trailingIconContainer: {
        width: TRAILING_ICON_SIZE,
        height: TRAILING_ICON_SIZE,
        overflow: "hidden",
    },

    trailingIconImage: {
        width: META_SPRITE_WIDTH * TRAILING_SPRITE_SCALE,
        height: META_SPRITE_HEIGHT * TRAILING_SPRITE_SCALE,
    },

    trailingCountText: {
        ...THEME.typography.text,
        color: THEME.colors.lm_ico,
        marginLeft: 6,
    },

});

export default EventCard;
