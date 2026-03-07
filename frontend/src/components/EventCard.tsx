import { TouchableOpacity, Text, View, StyleSheet } from "react-native";
import React from "react";
import { Event } from "../types";
import { useNavigation } from "@react-navigation/native";


const EventCard = ({ item }: {item: Event}) => {
    const navigation = useNavigation<any>();
    return (
        <View key={item.id}>
            <TouchableOpacity onPress={() => {
                navigation.navigate('EventDetails', {
                    event: item
                });
            }}>
                <View style={styles.container}>
                    <Text style={styles.title}>{item.name}</Text>
                    <View style={{ flexDirection: "row" }}>
                        <Text style={{ fontSize: 16, marginRight: 10 }}>{item.date}</Text>
                        <Text style={styles.location}>{item.location}</Text>
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

});

export default EventCard;
