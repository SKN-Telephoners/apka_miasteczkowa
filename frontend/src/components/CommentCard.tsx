import { Text, View, StyleSheet } from "react-native";
import { useState, useEffect } from "react";
import React from "react";
import { Comment } from "../types/comment";


const CommentCard = ({ item }: { item: Comment }) => {
    
    const date = new Date(item.created_at);

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
            <View style={styles.container}>
                <Text style={styles.username}>{item.user_id}</Text>
                <View style={{ flexDirection: "row" }}>
                    <Text style={{ fontSize: 18, marginRight: 10 }}>{formatDate(date) + " " + formatTime(date)}</Text>
                    {item.edited && <Text style={styles.edited}>Edytowano</Text>}
                </View>
                <Text style={{ fontSize: 16 }}>{item.content}</Text>
            </View>
        </View >
    )
}

const styles = StyleSheet.create({

    container: {
        backgroundColor: '#fdfafaff',
        padding: 10,
        marginVertical: 5,
        borderRadius: 25,

    },

    username: {
        fontSize: 24,
        fontWeight: "bold",
    },


    edited: {
        fontSize: 18,
        fontStyle: "italic",
    },

});

export default CommentCard;
