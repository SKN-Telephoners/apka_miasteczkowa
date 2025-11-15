import React, { useState, useEffect } from "react";
import {
    View,
    Text,
    SafeAreaView,
    ActivityIndicator
} from "react-native";
import EventCard from "../../components/EventCard"
import { FlatList } from "react-native-gesture-handler";
import { Event } from "../../types";
import InputField from "../../components/InputField";
// TODO: mock data to use untill there is an api endpoint for getting events 


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
        <SafeAreaView style={{ flex: 1, marginHorizontal: 10 }}>
            <View style={{ marginVertical: 10 }}>
                <InputField
                    icon="search"
                    placeholder="Szukaj"
                    onChangeText={(query) => handleSearch(query)}
                    value={searchQuery}
                />

            </View>
            <FlatList
                data={data}
                renderItem={({ item }) => <EventCard item={item} />}
                keyExtractor={item => item.event_id!}

            />

        </SafeAreaView>
    );
}



export default EventScreen;