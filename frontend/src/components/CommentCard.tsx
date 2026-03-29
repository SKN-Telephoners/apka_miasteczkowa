import {
    Text, View, StyleSheet,
    TouchableOpacity, Alert,
    TextInput, Modal, Pressable, Image,
} from "react-native";
import { useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import React from "react";
import { Comment } from "../types/comment";
import { editComment, deleteComment, replyToComment } from "../services/comments";
import UserCard from "./UserCard";
import { THEME } from "../utils/constants";

const BASE_TILE_SIZE = 30;
const ACTION_ICON_SIZE = 16;
const ACTION_SPRITE_WIDTH = 90;
const ACTION_SPRITE_HEIGHT = 90;
const ACTION_SPRITE_SCALE = ACTION_ICON_SIZE / BASE_TILE_SIZE;
const HEART_ICON_OFFSET = { x: 0, y: -BASE_TILE_SIZE * 2 };
const COMMENT_ICON_OFFSET = { x: -BASE_TILE_SIZE, y: -BASE_TILE_SIZE * 2 };
const REPLY_INDENT = 12;
const MENU_ICON_SIZE = 14;
const MENU_ICON_SCALE = MENU_ICON_SIZE / BASE_TILE_SIZE;
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


    const [showReplies, setShowReplies] = useState(false);

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
                    <View style={styles.headerUserCardContainer}>
                        <UserCard
                            creatorDisplayName={item.username || "nieznany użytkownik"}
                            createdAtDisplay={createdAtDisplay}
                            showMetaRow={true}
                            showMetaIcon={item.user_id === userID}
                            showCreatedAt={true}
                            avatarSize={42}
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
                                borderColor: '#59595aff',
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
                            <Text style={{ color: "#045ddaff", fontSize: 14 }}>
                                {isEditing ? "Zapisz" : "Edytuj"}
                            </Text>
                            <Ionicons
                                name={"pencil"}
                                size={12}
                                color="#045ddaff"
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
                            <Image
                                source={require("../../assets/iconset1.jpg")}
                                style={[
                                    styles.actionIconImage,
                                    {
                                        transform: [
                                            { translateX: HEART_ICON_OFFSET.x * ACTION_SPRITE_SCALE },
                                            { translateY: HEART_ICON_OFFSET.y * ACTION_SPRITE_SCALE },
                                        ],
                                    },
                                ]}
                                resizeMode="cover"
                            />
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
                            <Image
                                source={require("../../assets/iconset1.jpg")}
                                style={[
                                    styles.actionIconImage,
                                    {
                                        transform: [
                                            { translateX: COMMENT_ICON_OFFSET.x * ACTION_SPRITE_SCALE },
                                            { translateY: COMMENT_ICON_OFFSET.y * ACTION_SPRITE_SCALE },
                                        ],
                                    },
                                ]}
                                resizeMode="cover"
                            />
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
                                    <Image
                                        source={require("../../assets/iconset2.jpg")}
                                        style={[
                                            styles.menuIconImage,
                                            {
                                                transform: [
                                                    { translateX: MENU_EDIT_ICON_OFFSET.x * MENU_ICON_SCALE },
                                                    { translateY: MENU_EDIT_ICON_OFFSET.y * MENU_ICON_SCALE },
                                                ],
                                            },
                                        ]}
                                        resizeMode="cover"
                                    />
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
                                    <Image
                                        source={require("../../assets/iconset2.jpg")}
                                        style={[
                                            styles.menuIconImage,
                                            {
                                                transform: [
                                                    { translateX: MENU_DELETE_ICON_OFFSET.x * MENU_ICON_SCALE },
                                                    { translateY: MENU_DELETE_ICON_OFFSET.y * MENU_ICON_SCALE },
                                                ],
                                            },
                                        ]}
                                        resizeMode="cover"
                                    />
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

const styles = StyleSheet.create({

    container: {
        backgroundColor: THEME.colors.lm_bg,
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
        backgroundColor: THEME.colors.lm_ico,
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
        color: THEME.colors.lm_ico,
        marginHorizontal: 10,
        marginVertical: 5,
    },

    commentContent: {
        ...THEME.typography.text,
        color: THEME.colors.lm_txt,
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
        color: THEME.colors.lm_ico,
        marginLeft: 4,
    },

    actionIconContainer: {
        width: ACTION_ICON_SIZE,
        height: ACTION_ICON_SIZE,
        overflow: "hidden",
    },

    actionIconImage: {
        width: ACTION_SPRITE_WIDTH * ACTION_SPRITE_SCALE,
        height: ACTION_SPRITE_HEIGHT * ACTION_SPRITE_SCALE,
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
        color: THEME.colors.lm_highlight,
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
        backgroundColor: THEME.colors.lm_bg,
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

    menuIconImage: {
        width: ACTION_SPRITE_WIDTH * MENU_ICON_SCALE,
        height: ACTION_SPRITE_HEIGHT * MENU_ICON_SCALE,
    },


    menuEdit: {
        fontSize: 14,
        color: THEME.colors.lm_highlight,
    },

    menuDelete: {
        fontSize: 14,
        color: THEME.colors.agh_red,
    },


});

export default CommentCard;
