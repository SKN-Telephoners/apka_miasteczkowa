import React, { useState, useEffect } from "react";
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    Alert,
    SafeAreaView,
    ActivityIndicator
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { FlatList, TextInput } from "react-native-gesture-handler";
import { Event } from "../../types";
// TODO: mock data to use untill there is an api endpoint for getting events 

const filterFields = ['name', 'description', 'location']

const DATA: Partial<Event>[] = [
    {
        event_id: '1',
        name: 'First Item',
        date_and_time: '10-03-2025',
        description: 'Lorem ipsum',
        location: 'place1',
    },
    {
        event_id: '2',
        name: 'Second Item',
        date_and_time: '10-02-2025',
        description: 'Lorem ipsum',
        location: 'place2',
    },
    {
        event_id: '3',
        name: 'Third Item',
        date_and_time: '10-02-2025',
        description: 'Lorem ipsum',
        location: 'place3',
    },
    {
        event_id: '4',
        name: 'First Item',
        date_and_time: '10-02-2025',
        description: 'Lorem ipsum',
        location: 'place1',
    },
    {
        event_id: '5',
        name: 'another Second Item',
        date_and_time: '10-02-2025',
        description: 'Lorem ipsum',
        location: 'place2',
    },
    {
        event_id: '6',
        name: 'Third Item',
        date_and_time: '10-02-2025',
        description: 'Lorem ipsum',
        location: 'place3',
    },
    {
        event_id: '7',
        name: 'First Item',
        date_and_time: '10-02-2025',
        description: 'Lorem ipsum',
        location: 'place1',
    },
    {
        event_id: '8',
        name: 'Second Item',
        date_and_time: '10-02-2025',
        description: 'Lorem ipsum',
        location: 'place2',
    },
    {
        event_id: '9',
        name: 'Third Item',
        date_and_time: '10-02-2025',
        description: 'Lorem ipsum',
        location: 'place3',
    },
];

const EventScreen = () => {

    const [searchQuery, setSearchQuery] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [data, setData] = useState(DATA);
    const [error, setError] = useState(null);
    // TODO: full data is gonna be used with api endpoint 
    // const [fullData, setFullData] = useState([]);


    const handleSearch = (query: string) => {
        setSearchQuery(query);
        const lowerCaseQuery = query.toLowerCase().trim();
        if (lowerCaseQuery === "") {
            setData(DATA);
            return
        }


        const filteredData = DATA.filter((event) => {

            const { name, location, description } = event
            return name?.toLowerCase().includes(lowerCaseQuery) ||
                location?.toLowerCase().includes(lowerCaseQuery) ||
                description?.toLowerCase().includes(lowerCaseQuery)

        })
        setData(filteredData)
    }


    if (isLoading) {
        return (
            <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
                <ActivityIndicator size="large" />
            </View>
        );
    }

    if (error) {
        return (
            <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
                <Text>Wystąpił błąd podczas pobierania wydarzeń</Text>
            </View>
        );
    }

    return (
        <SafeAreaView style={{ flex: 1, marginHorizontal: 20 }}>
            <View>
                <TextInput
                    placeholder="Szukaj"
                    clearButtonMode="always"
                    autoCapitalize="none"
                    onChangeText={(query) => handleSearch(query)}
                    value={searchQuery}
                    style={styles.searchBox}
                />

            </View>
            <FlatList
                data={data}
                renderItem={EventCard}
                keyExtractor={item => item.event_id!}

            />

        </SafeAreaView>
    );
}

const EventCard = ({ item }: { item: Partial<Event> }) => {
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


export default EventScreen;