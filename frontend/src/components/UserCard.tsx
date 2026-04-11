
import React, { useMemo } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useTheme } from "../contexts/ThemeContext";
import Avatar from "./Avatar";
import { THEME } from "../utils/constants";
import SvgSpriteIcon from "./SvgSpriteIcon";

type UserCardProps = {
    creatorDisplayName: string;
    createdAtDisplay?: string;
    avatarUri?: string;
    showCreatedAt?: boolean;
    showMetaIcon?: boolean;
    showMetaRow?: boolean;
    showUsernameIcon?: boolean;
    metaPrefix?: string;
    avatarSize?: number;
    onMetaIconPress?: (event: any) => void;
    onUsernameIconPress?: () => void;
    metaTextColor?: string;
};

const BASE_TILE_SIZE = 30;
const META_ICON_SIZE = 18;
const USERNAME_ICON_SIZE = 22;
const USERNAME_ICON_OFFSET = { x: -BASE_TILE_SIZE * 2, y: -BASE_TILE_SIZE };

const UserCard = ({
    creatorDisplayName,
    createdAtDisplay,
    avatarUri,
    showCreatedAt = true,
    showMetaIcon = true,
    showMetaRow = true,
    showUsernameIcon = true,
    metaPrefix = "wydział • kierunek",
    avatarSize = 55,
    onMetaIconPress,
    onUsernameIconPress,
    metaTextColor,
}: UserCardProps) => {
    const { colors } = useTheme();
    const styles = useMemo(() => getStyles(colors), [colors]);
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
                        <Text style={[THEME.typography.eventTitle, { color: colors.text }]}>{creatorDisplayName}</Text>
                        {showUsernameIcon && (
                            <TouchableOpacity
                                style={styles.usernameIconContainer}
                                onPress={onUsernameIconPress}
                                disabled={!onUsernameIconPress}
                                activeOpacity={0.8}
                            >
                                <SvgSpriteIcon set={1} size={USERNAME_ICON_SIZE} offsetX={USERNAME_ICON_OFFSET.x} offsetY={USERNAME_ICON_OFFSET.y} />
                            </TouchableOpacity>
                        )}
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
                                    <SvgSpriteIcon set={2} size={META_ICON_SIZE} />
                                </TouchableOpacity>
                            )}
                        </View>
                    )}
                </View>
            </View>
        </View>
    );
};

const getStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({
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
        marginLeft: 6,
        marginTop: -2,
    },

    authorMetaRow: {
        flexDirection: "row",
        alignItems: "center",
        justifyContent: "space-between",
        width: "100%",
    },

    authorMetaText: {
        ...THEME.typography.text,
        color: colors.icon,
        flex: 1,
        minWidth: 0,
    },

    metaIconContainer: {
        width: META_ICON_SIZE,
        height: META_ICON_SIZE,
        marginLeft: 8,
    },
});

export default UserCard;