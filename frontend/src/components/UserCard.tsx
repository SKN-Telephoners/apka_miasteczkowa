
import React from "react";
import { Image, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import Avatar from "./Avatar";
import { THEME } from "../utils/constants";

type UserCardProps = {
    creatorDisplayName: string;
    createdAtDisplay?: string;
    avatarUri?: string;
    showCreatedAt?: boolean;
    showMetaIcon?: boolean;
    showMetaRow?: boolean;
    metaPrefix?: string;
    avatarSize?: number;
    onMetaIconPress?: (event: any) => void;
    metaTextColor?: string;
};

const BASE_TILE_SIZE = 30;
const META_ICON_SIZE = 18;
const META_SPRITE_WIDTH = 90;
const META_SPRITE_HEIGHT = 90;
const META_SPRITE_SCALE = META_ICON_SIZE / BASE_TILE_SIZE;
const USERNAME_ICON_SIZE = 22;
const USERNAME_SPRITE_SCALE = USERNAME_ICON_SIZE / BASE_TILE_SIZE;
const USERNAME_ICON_OFFSET = { x: -BASE_TILE_SIZE * 2, y: -BASE_TILE_SIZE };

const UserCard = ({
    creatorDisplayName,
    createdAtDisplay,
    avatarUri,
    showCreatedAt = true,
    showMetaIcon = true,
    showMetaRow = true,
    metaPrefix = "wydział • kierunek",
    avatarSize = 55,
    onMetaIconPress,
    metaTextColor,
}: UserCardProps) => {
    const metaText = showCreatedAt && createdAtDisplay
        ? `${metaPrefix} • ${createdAtDisplay}`
        : metaPrefix;

    return (
        <View style={styles.container}>
            <Avatar
                size={avatarSize}
                uri={
                    avatarUri ||
                    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80"
                }
            />
            <View style={styles.authorInfoContainer}>
                <View>
                    <View style={styles.usernameRow}>
                        <Text style={THEME.typography.eventTitle}>{creatorDisplayName}</Text>
                        <View style={styles.usernameIconContainer}>
                            <Image
                                source={require("../../assets/iconset1.jpg")}
                                style={styles.usernameIconImage}
                                resizeMode="cover"
                            />
                        </View>
                    </View>
                    {showMetaRow && (
                        <View style={styles.authorMetaRow}>
                            <Text style={[styles.authorMetaText, metaTextColor ? { color: metaTextColor } : null]}>{metaText}</Text>
                            {showMetaIcon && (
                                <TouchableOpacity
                                    style={styles.metaIconContainer}
                                    onPress={onMetaIconPress}
                                    disabled={!onMetaIconPress}
                                    activeOpacity={0.8}
                                >
                                    <Image
                                        source={require("../../assets/iconset2.jpg")}
                                        style={styles.metaIconImage}
                                        resizeMode="cover"
                                    />
                                </TouchableOpacity>
                            )}
                        </View>
                    )}
                </View>
            </View>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flexDirection: "row",
    },

    authorInfoContainer: {
        paddingHorizontal: 10,
        flex: 1,
        minWidth: 0,
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

    authorMetaRow: {
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        width: "100%",
    },

    authorMetaText: {
        ...THEME.typography.text,
        color: THEME.colors.lm_ico,
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
});

export default UserCard;