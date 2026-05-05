
import React, { useMemo } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useTheme } from "../contexts/ThemeContext";
import Avatar from "./Avatar";
import { THEME } from "../utils/constants";
import AppIcon from "./AppIcon";

type UserCardProps = {
    creatorDisplayName: string;
    createdAtDisplay?: string;
    avatarUri?: string;
    subtitle?: string;
    showCreatedAt?: boolean;
    showMetaIcon?: boolean;
    showMetaRow?: boolean;
    showUsernameIcon?: boolean;
    uniName?: string;
    majorName?: string;
    yearOfStudy?: number | null;
    avatarSize?: number;
    onMetaIconPress?: (event: any) => void;
    onUsernameIconPress?: () => void;
    metaTextColor?: string;
};

const META_ICON_SIZE = 18;
const USERNAME_ICON_SIZE = 22;

const UserCard = ({
    creatorDisplayName,
    createdAtDisplay,
    avatarUri,
    subtitle,
    showCreatedAt = true,
    showMetaIcon = true,
    showMetaRow = true,
    showUsernameIcon = true,
    uniName,
    majorName,
    yearOfStudy,
    avatarSize = 55,
    onMetaIconPress,
    onUsernameIconPress,
    metaTextColor,
}: UserCardProps) => {
    const { colors } = useTheme();
    const styles = useMemo(() => getStyles(colors), [colors]);
    const compact = avatarSize <= 44;

    const firstLineSegments: string[] = [];
    if (uniName) {
        firstLineSegments.push(uniName);
    }
    if (majorName) {
        firstLineSegments.push(majorName);
    }

    const secondLineSegments: string[] = [];
    if (yearOfStudy !== undefined && yearOfStudy !== null) {
        secondLineSegments.push(`${yearOfStudy} rok`);
    }
    
    if (showCreatedAt && createdAtDisplay) {
        secondLineSegments.push(createdAtDisplay);
    }

    const firstLineText = firstLineSegments.join(" • ");
    const secondLineText = secondLineSegments.join(" • ");

    return (
        <View style={[styles.container, compact ? styles.compactContainer : null]}>
            <Avatar size={avatarSize} uri={avatarUri} />
            <View style={styles.authorInfoContainer}>
                <View>
                    <View style={styles.usernameRow}>
                        <Text style={[styles.displayName, { color: colors.text }]} numberOfLines={1}>{creatorDisplayName}</Text>
                        {showUsernameIcon && (
                            <TouchableOpacity
                                style={styles.usernameIconContainer}
                                onPress={onUsernameIconPress}
                                disabled={!onUsernameIconPress}
                                activeOpacity={0.8}
                            >
                                <AppIcon name="AddUser" size={USERNAME_ICON_SIZE} />
                            </TouchableOpacity>
                        )}
                    </View>
                    {showMetaRow && (
                        <View style={styles.authorMetaRow}>
                            <View style={styles.metaTextColumn}>
                                {subtitle ? (
                                    <Text
                                        style={[styles.authorMetaText, metaTextColor ? { color: metaTextColor } : null]}
                                        numberOfLines={compact ? 1 : 2}
                                    >
                                        {subtitle}
                                    </Text>
                                ) : (
                                    <>
                                        {(firstLineText || secondLineText) ? (
                                            <Text
                                                style={[styles.authorMetaText, metaTextColor ? { color: metaTextColor } : null]}
                                                numberOfLines={1}
                                            >
                                                {firstLineText || secondLineText}
                                            </Text>
                                        ) : null}
                                        {secondLineText && firstLineText ? (
                                            <Text
                                                style={[styles.authorMetaText, metaTextColor ? { color: metaTextColor } : null]}
                                                numberOfLines={1}
                                            >
                                                {secondLineText}
                                            </Text>
                                        ) : null}
                                    </>
                                )}
                            </View>
                            {showMetaIcon && (
                                <TouchableOpacity
                                    style={styles.metaIconContainer}
                                    onPress={onMetaIconPress}
                                    disabled={!onMetaIconPress}
                                    activeOpacity={0.8}
                                >
                                    <AppIcon name="MoreVertical" size={META_ICON_SIZE} />
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
        alignItems: "center",
    },

    compactContainer: {
        paddingVertical: 2,
    },

    authorInfoContainer: {
        paddingHorizontal: 10,
        flex: 1,
        minWidth: 0,
    },

    displayName: {
        ...THEME.typography.eventTitle,
        lineHeight: 20,
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
        alignItems: "flex-start",
        justifyContent: "space-between",
        width: "100%",
    },

    metaTextColumn: {
        flex: 1,
        minWidth: 0,
    },

    authorMetaText: {
        ...THEME.typography.text,
        color: colors.icon,
        flex: 1,
        minWidth: 0,
        fontSize: 13,
        lineHeight: 18,
    },

    metaIconContainer: {
        width: META_ICON_SIZE,
        height: META_ICON_SIZE,
        marginLeft: 8,
    },
});

export default UserCard;