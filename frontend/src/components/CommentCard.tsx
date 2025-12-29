import { Text, View, StyleSheet, TouchableOpacity } from "react-native";
import { useState } from "react";
import { Ionicons } from "@expo/vector-icons";
import React from "react";
import { Comment } from "../types/comment";



const CommentCard = ({ item, level = 0 }: { item: Comment, level?: number }) => {

    const date = new Date(item.created_at);
    const [showReplies, setShowReplies] = useState(false);

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


    return (
        <View key={item.comment_id}>
            <View style={[styles.container, { marginLeft: item.parent_comment_id ? level * 16 : 0 }]}>
                <View style={{ flexDirection: "row", alignItems: "baseline" }}>
                    <Text style={styles.username}>mock username</Text>
                    <Text style={{ fontSize: 14 }}>
                        {formatDate(date)} {formatTime(date)}
                    </Text>
                </View>

                {item.edited && <Text style={styles.edited}>Edytowano</Text>}

                <Text style={{ fontSize: 14, marginHorizontal: 10, marginTop: 10 }}>{item.content}</Text>

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
                                <CommentCard key={reply.comment_id} item={reply} level={level + 1} />
                            ))}
                    </>
                )}
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

});

export default CommentCard;
