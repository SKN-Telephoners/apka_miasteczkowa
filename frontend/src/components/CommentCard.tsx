import React from "react";
import {
    Text, View, StyleSheet,
    TouchableOpacity, Alert,
    TextInput, Modal, Pressable,
} from "react-native";
import { useEffect, useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import { Comment } from "../types/comment";
import { editComment, deleteComment, replyToComment } from "../services/comments";
import UserCard from "./UserCard";
import { THEME } from "../utils/constants";
import SvgSpriteIcon from "./SvgSpriteIcon";
import AppIcon from "./AppIcon";
import { useTheme } from "../contexts/ThemeContext";
import { useMemo } from "react";
import { useNavigation } from "@react-navigation/native";
import { useFriends } from "../contexts/FriendsContext";

const BASE_TILE_SIZE = 30;
const ACTION_ICON_SIZE = 16;
const HEART_ICON_OFFSET = { x: 0, y: -BASE_TILE_SIZE * 2 };
const COMMENT_ICON_OFFSET = { x: -BASE_TILE_SIZE, y: -BASE_TILE_SIZE * 2 };
const REPLY_INDENT = 12;
const MENU_ICON_SIZE = 14;
const MENU_EDIT_ICON_OFFSET = { x: -BASE_TILE_SIZE * 2, y: -BASE_TILE_SIZE };
const MENU_DELETE_ICON_OFFSET = { x: -BASE_TILE_SIZE, y: 0 };

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



const CommentCard = ({
    item,
    level = 0,
    isLastSibling = true,
    userID,
    onDeleted,
    onReply,
}: {
    item: Comment;
    level?: number;
    isLastSibling?: boolean;
    userID: string;
    onDeleted: () => void;
    onReply: (comment: Comment) => void;
}) => {
    const { colors } = useTheme();
    const styles = useMemo(() => getStyles(colors), [colors]);
    const navigation = useNavigation<any>();
    const { friends, sendFriendRequest } = useFriends();

    const [showReplies, setShowReplies] = useState(false);
    const [isCommentAuthorFriend, setIsCommentAuthorFriend] = useState(false);

    const [commentValue, setCommentValue] = useState(item.content);
    const [isEditing, setIsEditing] = useState(false);
    const [isEdited, setIsEdited] = useState(item.edited);
    const [menuVisible, setMenuVisible] = useState(false);

    const [displayContent, setDisplayContent] = useState(item.content);
    const createdAtDisplay = formatCreatedAt(item.created_at);

    const [menuPosition, setMenuPosition] = useState({
        x: 0,
        y: 0,
    });
    const hasParent = Boolean(item.parent_comment_id);
    const canOpenAuthorProfile = Boolean(item.user_id) && item.user_id !== userID;

    // Check if comment author is a friend
    useEffect(() => {
        if (canOpenAuthorProfile && item.user_id) {
            const isFriend = friends.some(
                (friend) => friend.id === item.user_id
            );
            setIsCommentAuthorFriend(isFriend);
        } else {
            setIsCommentAuthorFriend(false);
        }
    }, [friends, canOpenAuthorProfile, item.user_id]);

    const handleOpenAuthorProfile = () => {
        if (!canOpenAuthorProfile) {
            return;
        }

        navigation.navigate("UserScreen", {
            visitedUser: {
                id: item.user_id,
                user_id: item.user_id,
                username: item.username || "nieznany użytkownik",
                is_friend: false,
            },
        });
    };

    const handleSendFriendRequest = async () => {
        try {
            await sendFriendRequest(item.user_id);
            Alert.alert("Sukces", "Zaproszenie wysłane");
        } catch (err: any) {
            Alert.alert("Błąd", err?.message || "Nie udało się wysłać zaproszenia");
        }
    };

    useEffect(() => {
        setDisplayContent(item.content);
        setCommentValue(item.content);
        setIsEdited(item.edited);
    }, [item.content, item.edited]);


    const handleEditComment = async () => {
        if (!commentValue || commentValue.trim() === '') {
            Alert.alert("Komentarz nie może być pusty");
            return;
        }
        try {
            await editComment(item.comment_id, commentValue);
            Alert.alert("Komentarz edytowany");
            setIsEditing(false);
            setDisplayContent(commentValue);
            setIsEdited(true);
        } catch (error: any) {
            Alert.alert("Błąd edytowania komentarza", error.message);
        }
    };

    const handleDeleteComment = async () => {
        try {
            await deleteComment(item.comment_id);
            Alert.alert("Komentarz usunięty");
            onDeleted();
        } catch (error: any) {
            Alert.alert("Błąd usuwania komentarza", error.message);
        }
    };

    return (
        <View key={item.comment_id}>
            <View
                style={[
                    styles.container,
                    hasParent ? styles.replyContainer : styles.rootContainer,
                    { marginLeft: hasParent ? REPLY_INDENT : 0 },
                ]}
            >
                {hasParent && (
                    <View
                        style={[
                            styles.threadLine,
                            isLastSibling ? styles.threadLineLast : styles.threadLineContinue,
                        ]}
                    />
                )}
                <View style={styles.header}>
                    <View style={[styles.headerUserCardContainer]}>
                        <UserCard
                            creatorDisplayName={item.username || "nieznany użytkownik"}
                            createdAtDisplay={createdAtDisplay}
                            avatarUri={item.profile_picture_url || undefined}
                            showMetaRow={true}
                            showMetaIcon={item.user_id === userID || canOpenAuthorProfile}
                            showCreatedAt={true}
                            showUsernameIcon={canOpenAuthorProfile && !isCommentAuthorFriend}
                            uniName={item.academy || undefined}
                            majorName={item.course || undefined}
                            yearOfStudy={item.year ?? undefined}
                            avatarSize={42}
                            onUsernameIconPress={canOpenAuthorProfile && !isCommentAuthorFriend ? handleSendFriendRequest : undefined}
                            onMetaIconPress={
                                item.user_id === userID
                                    ? (event) => {
                                        const { pageX, pageY } = event.nativeEvent;
                                        setMenuPosition({
                                            x: pageX,
                                            y: pageY,
                                        });
                                        requestAnimationFrame(() => setMenuVisible(true));
                                    }
                                    : canOpenAuthorProfile
                                        ? handleOpenAuthorProfile
                                        : undefined
                            }
                        />
                    </View>
                </View>

                {isEdited && <Text style={styles.edited}>Edytowano</Text>}


                {isEditing ? (
                    <View>
                        <TextInput
                            style={{
                                fontSize: 14,
                                marginHorizontal: 10,
                                marginTop: 10,
                                borderBottomWidth: 1,
                                padding: 10,
                                borderColor: colors.icon,
                                marginBottom: 5
                            }}
                            value={commentValue}
                            onChangeText={setCommentValue}
                            multiline
                        />
                        <TouchableOpacity
                            onPress={() => {
                                if (isEditing) {
                                    handleEditComment();
                                } else {
                                    setIsEditing(true);
                                }
                            }}
                            style={{ flexDirection: "row", alignItems: "center", alignSelf: "flex-end" }}
                        >
                            <Text style={{ color: colors.transparentHighlight, fontSize: 14 }}>
                                {isEditing ? "Zapisz" : "Edytuj"}
                            </Text>
                            <AppIcon
                                name="Edit"
                                size={12}
                                color={colors.transparentHighlight}
                                style={{ marginLeft: 2 }}
                            />
                        </TouchableOpacity>
                    </View>
                ) : (
                    <Text style={styles.commentContent}>
                        {displayContent}
                    </Text>
                )}

                <View style={styles.actionsRow}>
                    <View style={styles.actionItem}>
                        <View style={styles.actionIconContainer}>
                            <SvgSpriteIcon set={1} size={ACTION_ICON_SIZE} offsetX={HEART_ICON_OFFSET.x} offsetY={HEART_ICON_OFFSET.y} />
                        </View>
                        <Text style={styles.actionCount}>0</Text>
                    </View>

                    <TouchableOpacity
                        style={styles.actionItem}
                        onPress={() => {
                            setIsEditing(false);
                            onReply(item);
                        }}
                    >
                        <View style={styles.actionIconContainer}>
                            <SvgSpriteIcon set={1} size={ACTION_ICON_SIZE} offsetX={COMMENT_ICON_OFFSET.x} offsetY={COMMENT_ICON_OFFSET.y} />
                        </View>
                        <Text style={styles.actionCount}>{item.replies?.length ?? 0}</Text>
                    </TouchableOpacity>
                </View>


                {item.replies?.length > 0 && (
                    <>
                        <TouchableOpacity style={styles.numOfResponses} onPress={() => setShowReplies(!showReplies)}>
                            <Text style={styles.responsesToggleText}>
                                {showReplies ? "Ukryj odpowiedzi" : "Pokaż odpowiedzi"}
                            </Text>
                        </TouchableOpacity>

                        {showReplies &&
                            item.replies.map((reply, index) => (
                                <CommentCard
                                    key={reply.comment_id}
                                    item={reply}
                                    level={level + 1}
                                    isLastSibling={index === item.replies.length - 1}
                                    userID={userID}
                                    onDeleted={onDeleted}
                                    onReply={onReply} />
                            ))}
                    </>
                )}

                <Modal
                    transparent
                    visible={menuVisible}
                    animationType="fade"
                    onRequestClose={() => setMenuVisible(false)}
                >
                    <Pressable style={styles.menuBackdrop} onPress={() => setMenuVisible(false)}>
                        <Pressable
                            style={[
                                styles.menu,
                                {
                                    top: menuPosition.y + 8,
                                    left: Math.max(menuPosition.x - 120, 8),
                                },
                            ]}
                            onPress={(e) => e.stopPropagation()}
                        >
                            <TouchableOpacity
                                style={styles.menuItem}
                                onPress={() => {
                                    setMenuVisible(false);
                                    setIsEditing(true);
                                }}
                            >
                                <View style={styles.menuIconContainer}>
                                    <SvgSpriteIcon set={2} size={MENU_ICON_SIZE} offsetX={MENU_EDIT_ICON_OFFSET.x} offsetY={MENU_EDIT_ICON_OFFSET.y} />
                                </View>
                                <Text style={styles.menuEdit}>Edytuj</Text>
                            </TouchableOpacity>

                            <TouchableOpacity
                                style={styles.menuItem}
                                onPress={() => {
                                    setMenuVisible(false);
                                    handleDeleteComment();
                                }}
                            >
                                <View style={styles.menuIconContainer}>
                                    <SvgSpriteIcon set={2} size={MENU_ICON_SIZE} offsetX={MENU_DELETE_ICON_OFFSET.x} offsetY={MENU_DELETE_ICON_OFFSET.y} />
                                </View>
                                <Text style={styles.menuDelete}>Usuń</Text>
                            </TouchableOpacity>
                        </Pressable>
                    </Pressable>
                </Modal>




            </View>
        </View>
    );
}

const getStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({

    container: {
        backgroundColor: colors.background,
        paddingVertical: 15,
        marginVertical: 5,
        borderRadius: 0,

    },

    rootContainer: {
        paddingHorizontal: 10,
    },

    replyContainer: {
        paddingLeft: 8,
        paddingRight: 0,
    },

    threadLine: {
        position: "absolute",
        left: 0,
        width: 1,
        backgroundColor: colors.icon,
    },

    threadLineContinue: {
        top: 0,
        bottom: 0,
    },

    threadLineLast: {
        top: 0,
        height: 24,
    },

    headerUserCardContainer: {
        flex: 1,
    },


    edited: {
        fontSize: 12,
        fontStyle: "italic",
        color: colors.icon,
        marginHorizontal: 10,
        marginVertical: 5,
    },

    commentContent: {
        ...THEME.typography.text,
        color: colors.text,
        marginHorizontal: 10,
        marginTop: 10,
    },

    actionsRow: {
        flexDirection: "row",
        alignItems: "center",
        marginHorizontal: 10,
        marginTop: 10,
    },

    actionItem: {
        flexDirection: "row",
        alignItems: "center",
        marginRight: 16,
    },

    actionCount: {
        ...THEME.typography.text,
        color: colors.icon,
        marginLeft: 4,
    },

    actionIconContainer: {
        width: ACTION_ICON_SIZE,
        height: ACTION_ICON_SIZE,
        overflow: "hidden",
    },

    replies: {
        marginTop: 4,
    },

    numOfResponses: {
        marginTop: 5,
        marginHorizontal: 15,
        padding: 5
    },

    responsesToggleText: {
        color: colors.transparentHighlight,
        fontSize: 14,
    },
    header: {
        flexDirection: "row",
        justifyContent: "space-between",
        alignItems: "center",
    },

    menuBackdrop: {
        flex: 1,
    },

    menu: {
        position: "absolute",
        width: 130,
        backgroundColor: colors.background,
        borderRadius: 12,
        paddingVertical: 6,
        paddingHorizontal: 10,
        elevation: 8,
        shadowOpacity: 0.15,
        shadowRadius: 8,
    },

    menuItem: {
        flexDirection: "row",
        alignItems: "center",
        paddingVertical: 8,
        gap: 8,
    },

    menuIconContainer: {
        width: MENU_ICON_SIZE,
        height: MENU_ICON_SIZE,
        overflow: "hidden",
    },


    menuEdit: {
        fontSize: 14,
        color: colors.transparentHighlight,
    },

    menuDelete: {
        fontSize: 14,
        color: colors.aghRed,
    },


});

export default CommentCard;
