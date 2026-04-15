import { TouchableOpacity, Text, View, StyleSheet, Alert, Image } from "react-native";
import React, { useEffect, useMemo, useState } from "react";
import { Event } from "../types";
import { useNavigation } from "@react-navigation/native";
import { THEME } from '../utils/constants';
import Button from "./Button";
import { tokenStorage } from "../utils/storage";
import { joinEvent, leaveEvent } from "../services/events";
import UserCard from "./UserCard";
import SvgSpriteIcon from "./SvgSpriteIcon";
import { useTheme } from "../contexts/ThemeContext";
import { useFriends } from "../contexts/FriendsContext";

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
const USERNAME_ICON_SIZE = 22;
const USERNAME_ICON_OFFSET = { x: -BASE_TILE_SIZE * 2, y: -BASE_TILE_SIZE };
const MAP_INLINE_ICON_SIZE = 14;
const MAP_INLINE_ICON_OFFSET = { x: 0, y: -BASE_TILE_SIZE };
const TRAILING_ICON_SIZE = 24;
const HEART_ICON_OFFSET = { x: 0, y: -BASE_TILE_SIZE * 2 };
const COMMENT_ICON_OFFSET = { x: -BASE_TILE_SIZE, y: -BASE_TILE_SIZE * 2 };
const SHARE_ICON_OFFSET = { x: -BASE_TILE_SIZE * 2, y: -BASE_TILE_SIZE * 2 };
const EDIT_MENU_ICON_OFFSET = { x: -BASE_TILE_SIZE * 2, y: -BASE_TILE_SIZE };


const EventCard = ({ item, showActions = true }: { item: Event; showActions?: boolean }) => {
    const navigation = useNavigation<any>();
    const { colors } = useTheme();
    const { friends, sendFriendRequest } = useFriends();
    const styles = useMemo(() => getStyles(colors), [colors]);
    const eventDateTime = parseEventDateTime(item);
    const isPastEvent = eventDateTime ? eventDateTime.getTime() < Date.now() : false;
    const [userID, setUserID] = useState('');
    const [isOwner, setIsOwner] = useState(false);
    const [isParticipating, setIsParticipating] = useState(Boolean(item?.is_participating));
    const [isParticipationLoading, setIsParticipationLoading] = useState(false);
    const [participantCount, setParticipantCount] = useState<number>(Number(item?.participant_count ?? 0));
    const [isCreatorFriend, setIsCreatorFriend] = useState(false);

    const isPrivateEvent =
        item?.is_private === true ||
        String(item?.is_private).toLowerCase() === "true";
    const creatorDisplayName = item.creator_username?.trim() || "nieznany użytkownik";
    const createdAtDisplay = formatCreatedAt(item.created_at);
    const creatorFaculty = (item as any)?.creator_faculty as string | undefined;
    const creatorCourse = (item as any)?.creator_course as string | undefined;
    const creatorYear = (item as any)?.creator_year as number | string | undefined;
    const creatorAcademy = (item as any)?.creator_academy as string | undefined;
    const canOpenCreatorProfile = Boolean(item.creator_id) && item.creator_id !== userID;
    const canInviteFromCard = !isPastEvent && (!isPrivateEvent || isOwner);
    const hideInviteAction = isPrivateEvent && !isOwner;

    // Check if creator is a friend
    useEffect(() => {
        if (!isOwner && item.creator_id) {
            const isFriend = friends.some(
                (friend) => friend.id === item.creator_id
            );
            setIsCreatorFriend(isFriend);
        } else {
            setIsCreatorFriend(false);
        }
    }, [friends, isOwner, item.creator_id]);

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

    const handleOpenCreatorProfile = () => {
        if (!canOpenCreatorProfile) {
            return;
        }

        navigation.navigate("UserScreen", {
            visitedUser: {
                id: item.creator_id,
                user_id: item.creator_id,
                username: creatorDisplayName,
                is_friend: false,
            },
        });
    };

    const handleSendFriendRequest = async () => {
        try {
            await sendFriendRequest(item.creator_id);
            Alert.alert("Sukces", "Zaproszenie wysłane");
        } catch (err: any) {
            Alert.alert("Błąd", err?.message || "Nie udało się wysłać zaproszenia");
        }
    };

    const handleJoinEvent = async () => {
        if (isParticipationLoading) return;

        if (isParticipating && isPrivateEvent) {
            Alert.alert(
                "Czy na pewno chcesz opuścić wydarzenie prywatne?",
                "Nie będziesz mógł się na nie zapisać bez zgody autora.",
                [
                    { text: "Anuluj", style: "cancel" },
                    {
                        text: "Opuść",
                        style: "destructive",
                        onPress: async () => {
                            try {
                                setIsParticipationLoading(true);
                                await leaveEvent(item.id);
                                setIsParticipating(false);
                                setParticipantCount((prev) => Math.max(prev - 1, 0));
                            } catch (err: any) {
                                Alert.alert("Błąd", err?.message || "Nie udało się zaktualizować udziału w wydarzeniu.");
                            } finally {
                                setIsParticipationLoading(false);
                            }
                        },
                    },
                ]
            );
            return;
        }

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
                                <SvgSpriteIcon set={2} size={META_ICON_SIZE} offsetX={EDIT_MENU_ICON_OFFSET.x} offsetY={EDIT_MENU_ICON_OFFSET.y} />
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
                            <SvgSpriteIcon set={1} size={MAP_INLINE_ICON_SIZE} offsetX={MAP_INLINE_ICON_OFFSET.x} offsetY={MAP_INLINE_ICON_OFFSET.y} />
                        </View>
                    </View>
                </View>

                <View style={{ paddingBottom: 10, paddingTop: 20 }}>
                    <UserCard
                        creatorDisplayName={creatorDisplayName}
                        createdAtDisplay={createdAtDisplay}
                        avatarUri={item.creator_profile_picture_url || undefined}
                        uniName={creatorAcademy || creatorFaculty || undefined}
                        majorName={creatorCourse || undefined}
                        yearOfStudy={creatorYear !== undefined && creatorYear !== null ? Number(creatorYear) : undefined}
                        showUsernameIcon={canOpenCreatorProfile && !isCreatorFriend}
                        onUsernameIconPress={canOpenCreatorProfile && !isCreatorFriend ? handleSendFriendRequest : undefined}
                        showMetaIcon={canOpenCreatorProfile}
                        onMetaIconPress={canOpenCreatorProfile ? handleOpenCreatorProfile : undefined}
                        metaTextColor={isPastEvent ? colors.text : undefined}
                    />

                    {showActions && !isOwner && !isPastEvent && (!isPrivateEvent || isParticipating) && (
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
                                <SvgSpriteIcon set={1} size={TRAILING_ICON_SIZE} offsetX={HEART_ICON_OFFSET.x} offsetY={HEART_ICON_OFFSET.y} />
                            </View>
                            <Text style={styles.trailingCountText}>{participantCount}</Text>
                        </View>
                        <TouchableOpacity
                            style={styles.trailingActionItem}
                            onPress={() => navigation.navigate("EventComments", { event: item })}
                            activeOpacity={0.8}
                        >
                            <View style={styles.trailingIconContainer}>
                                <SvgSpriteIcon set={1} size={TRAILING_ICON_SIZE} offsetX={COMMENT_ICON_OFFSET.x} offsetY={COMMENT_ICON_OFFSET.y} />
                            </View>
                            <Text style={styles.trailingCountText}>{Number(item.comment_count ?? 0)}</Text>
                        </TouchableOpacity>
                        {!hideInviteAction && (
                            <View style={styles.trailingActionItem}>
                                <TouchableOpacity
                                    style={styles.trailingIconContainer}
                                    onPress={() => {
                                        if (!canInviteFromCard) {
                                            return;
                                        }
                                        navigation.navigate("EventInviteUsers", { event: item });
                                    }}
                                    disabled={!canInviteFromCard}
                                    activeOpacity={0.8}
                                >
                                    <SvgSpriteIcon set={1} size={TRAILING_ICON_SIZE} offsetX={SHARE_ICON_OFFSET.x} offsetY={SHARE_ICON_OFFSET.y} />
                                </TouchableOpacity>
                            </View>
                        )}
                    </View>
                    )}
                </View>
            </View >
        </View>
    )
}

const getStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({

    container: {
        backgroundColor: colors.background,
        padding: 20,

    },

    pastContainer: {
        backgroundColor: colors.border,
    },

    title: {
        ...THEME.typography.eventTitle,
        color: colors.text,
    },

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

    text: {
        ...THEME.typography.text,
        color: colors.text,
    },

    eventImage: {
        width: "100%",
        height: 220,
        borderRadius: 14,
        marginTop: 8,
        marginBottom: 10,
    },

    textMuted: {
        ...THEME.typography.text,
        color: colors.icon
    },

    textHighlight: {
        ...THEME.typography.text,
        color: colors.highlight
    },

    pastTextColor: {
        color: colors.text,
    },

    pastMetaText: {
        color: colors.icon,
    },

    location: {
        fontSize: 18,
        bottom: 2,
        fontWeight: "bold",
        color: colors.transparentHighlight,
    },

    pastLocation: {
        color: colors.text,
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

    trailingCountText: {
        ...THEME.typography.text,
        color: colors.icon,
        marginLeft: 6,
    },

    trailingCountDisabled: {
        opacity: 0.5,
    },

});

export default EventCard;
