import { TouchableOpacity, Text, View, Alert, StyleSheet } from "react-native";
import React from "react";
import { Event } from "../types";

interface EventCard {
    item: Partial<Event>
}

const EventCard: React.FC<EventCard> = ({ item }: { item: Partial<Event> }) => {
    return (
        <TouchableOpacity onPress={() => Alert.alert("Hello")}>
            <View style={styles.container}>
                <Text style={styles.title}>{item.name}</Text>
                <View style={{ flexDirection: "row" }}>
                    <Text style={{ fontSize: 16, marginRight: 10 }}>{item.date_and_time}</Text>
                    <Text style={styles.location}>{item.location}</Text>
                </View>
            </View>
        </TouchableOpacity>
    )
}

const styles = StyleSheet.create({

    container: {
        backgroundColor: '#fdfafaff',
        padding: 20,
        marginVertical: 5,
        borderRadius: 25,

    },

    title: {
        fontSize: 24,
        marginBottom: 90,
        fontWeight: "bold",
    },


    location: {
        fontSize: 18,
        bottom: 2,
        fontWeight: "bold",
        color: "#045ddaff",
    },

    searchBox: {
        paddingHorizontal: 20,
        paddingVertical: 10,
        marginVertical: 10,
        backgroundColor: "#fdfafaff",
        borderColor: "#ccc",
        borderWidth: 1,
        borderRadius: 25,
    },

    filterButton: {
        padding: 10,
        marginRight: 260,
        backgroundColor: "#fdfafaff",
        borderRadius: 25,
        flexDirection: "row",
        alignItems: "center",
    },
});

export default EventCard;
