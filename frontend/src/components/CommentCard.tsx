import {
    Text, View, StyleSheet,
    TouchableOpacity, Alert,
    TextInput, Modal, Pressable,
    UIManager, findNodeHandle
} from "react-native";
import { useState, useRef } from "react";
import { Ionicons } from "@expo/vector-icons";
import React from "react";
import { Comment } from "../types/comment";
import { editComment, deleteComment, replyToComment } from "../services/comments";



const CommentCard = ({
    item,
    level = 0,
    userID,
    onDeleted,
    onReply,
}: {
    item: Comment;
    level?: number;
    userID: string;
    onDeleted: () => void;
    onReply: (comment: Comment) => void;
}) => {


    const date = new Date(item.created_at);
    const [showReplies, setShowReplies] = useState(false);

    const [commentValue, setCommentValue] = useState(item.content);
    const [isEditing, setIsEditing] = useState(false);
    const [isEdited, setIsEdited] = useState(item.edited);
    const [menuVisible, setMenuVisible] = useState(false);

    const [displayContent, setDisplayContent] = useState(item.content);

    const menuButtonRef = useRef<View>(null);

    const [menuPosition, setMenuPosition] = useState({
        x: 0,
        y: 0,
    });


    const formatTime = (timeObj: Date): string => {
        const hours = String(timeObj.getHours()).padStart(2, '0');
        const minutes = String(timeObj.getMinutes()).padStart(2, '0');
        return hours + ':' + minutes;
    };

    const formatDate = (dateObj: Date): string => {
        const day = String(dateObj.getDate()).padStart(2, '0');
        const month = String(dateObj.getMonth() + 1).padStart(2, '0');
        const year = dateObj.getFullYear();
        return day + '.' + month + '.' + year;
    };


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
            <View style={[styles.container, { marginLeft: item.parent_comment_id ? level * 16 : 0 }]}>
                <View style={styles.header}>
                    <View style={{ flexDirection: "row", alignItems: "baseline" }}>
                        <Text style={styles.username}>mock username</Text>
                        <Text style={{ fontSize: 14 }}>
                            {formatDate(date)} {formatTime(date)}
                        </Text>
                    </View>

                    {item.user_id === userID && (
                        <TouchableOpacity
                            ref={menuButtonRef}
                            onPress={() => {
                                if (!menuButtonRef.current) return;

                                const handle = findNodeHandle(menuButtonRef.current);
                                if (!handle) return;

                                UIManager.measureInWindow(
                                    handle,
                                    (x, y, width, height) => {
                                        setMenuPosition({
                                            x: x + width,
                                            y: y + height,
                                        });
                                        setMenuVisible(true);
                                    }
                                );
                            }}
                        >
                            <Ionicons name="ellipsis-vertical" size={18} color="#59595aff" />
                        </TouchableOpacity>

                    )}
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
                    <Text style={{ fontSize: 14, marginHorizontal: 10, marginTop: 10 }}>
                        {displayContent}
                    </Text>
                )}

                <TouchableOpacity onPress={() => {
                    setIsEditing(false);
                    onReply(item);
                }}>
                    <Text style={{ fontSize: 12, marginHorizontal: 10, marginTop: 10, color: '#59595aff' }}>
                        <Ionicons name="return-down-forward-sharp" size={10} /> Odpowiedz
                    </Text>
                </TouchableOpacity>


                {item.replies?.length > 0 && (
                    <>
                        <TouchableOpacity
                            style={[styles.numOfResponses, { flexDirection: 'row', alignItems: 'center' }]}
                            onPress={() => setShowReplies(!showReplies)}
                        >
                            <Text style={{ color: "#045ddaff", fontSize: 14 }}>
                                {item.replies.length} odpowiedzi{" "}
                                <Text><Ionicons name={showReplies ? "chevron-up" : "chevron-down"} size={12} color="#045ddaff" />
                                </Text>
                            </Text>
                        </TouchableOpacity>

                        {showReplies &&
                            item.replies.map(reply => (
                                <CommentCard
                                    key={reply.comment_id}
                                    item={reply}
                                    level={level + 1}
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
                    <Pressable
                        style={styles.menuBackdrop}
                        onPress={() => setMenuVisible(false)}
                    >
                        <View
                            style={[
                                styles.menu,
                                {
                                    top: menuPosition.y,
                                    left: menuPosition.x - 120,
                                },
                            ]}
                        >
                            <TouchableOpacity
                                style={styles.menuItem}
                                onPress={() => {
                                    setMenuVisible(false);
                                    setIsEditing(true);
                                }}
                            >
                                <Ionicons name="pencil" size={14} color="#045ddaff" />
                                <Text style={styles.menuEdit}>Edytuj</Text>
                            </TouchableOpacity>

                            <TouchableOpacity
                                style={styles.menuItem}
                                onPress={() => {
                                    setMenuVisible(false);
                                    handleDeleteComment();
                                }}
                            >
                                <Ionicons name="trash" size={14} color="#d71010ff" />
                                <Text style={styles.menuDelete}>Usuń</Text>
                            </TouchableOpacity>
                        </View>
                    </Pressable>
                </Modal>




            </View>
        </View>
    );
}

const styles = StyleSheet.create({

    container: {
        backgroundColor: '#fdfafaff',
        padding: 15,
        marginVertical: 5,
        borderRadius: 25,

    },

    username: {
        fontSize: 18,
        fontWeight: "bold",
        marginHorizontal: 10,
    },


    edited: {
        fontSize: 12,
        fontStyle: "italic",
        color: '#59595aff',
        marginHorizontal: 10,
    },

    replies: {
        marginTop: 4,
    },

    numOfResponses: {
        marginTop: 5,
        marginHorizontal: 15,
        padding: 5
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
        backgroundColor: "#fff",
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


    menuEdit: {
        fontSize: 14,
        color: "#045ddaff",
    },

    menuDelete: {
        fontSize: 14,
        color: "#d71010ff",
    },


});

export default CommentCard;
