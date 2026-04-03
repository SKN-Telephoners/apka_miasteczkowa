import { TouchableOpacity, Text, View, StyleSheet } from "react-native";
import React from "react";
import { Event } from "../types";
import { useNavigation } from "@react-navigation/native";

const parseEventDateTime = (event: Event): Date | null => {
    if (!event?.date || !event?.time) return null;

    const [day, month, year] = event.date.split('.').map(Number);
    const [hours, minutes] = event.time.split(':').map(Number);

    if ([day, month, year, hours, minutes].some(Number.isNaN)) {
        return null;
    }

    return new Date(year, month - 1, day, hours, minutes, 0, 0);
};


const EventCard = ({ item }: {item: Event}) => {
    const navigation = useNavigation<any>();
    const eventDateTime = parseEventDateTime(item);
    const isPastEvent = eventDateTime ? eventDateTime.getTime() < Date.now() : false;

    return (
        <View key={item.id}>
            <TouchableOpacity onPress={() => {
                navigation.navigate('EventDetails', {
                    event: item
                });
            }}>
                <View style={[styles.container, isPastEvent && styles.pastContainer]}>
                    <Text style={[styles.title, isPastEvent && styles.pastText]}>{item.name}</Text>
                    <Text style={[styles.creator, isPastEvent && styles.pastText]}>
                        Dodane przez: {item.creator_username || "nieznany użytkownik"}
                    </Text>
                    <View style={{ flexDirection: "row" }}>
                        <Text style={[styles.metaText, isPastEvent && styles.pastText]}>{item.date}</Text>
                        <Text style={[styles.location, isPastEvent && styles.pastLocation]}>{item.location}</Text>
                    </View>
                </View>
            </TouchableOpacity>
        </View >
    )
}

const styles = StyleSheet.create({

    container: {
        backgroundColor: '#fdfafaff',
        padding: 20,
        marginVertical: 5,
        borderRadius: 25,

    },

    pastContainer: {
        backgroundColor: '#ececec',
    },

    title: {
        fontSize: 24,
        marginBottom: 12,
        fontWeight: "bold",
    },

    creator: {
        fontSize: 14,
        color: '#59595aff',
        marginBottom: 70,
    },

    pastText: {
        color: '#7a7a7a',
    },

    metaText: {
        fontSize: 16,
        marginRight: 10,
    },


    location: {
        fontSize: 18,
        bottom: 2,
        fontWeight: "bold",
        color: "#045ddaff",
    },

    pastLocation: {
        color: '#7a7a7a',
    },

});

export default EventCard;
