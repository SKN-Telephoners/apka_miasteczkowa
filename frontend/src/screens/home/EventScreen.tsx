import React, { useState, useEffect, useCallback } from "react";
import {
    View,
    Text,
    SafeAreaView,
    ActivityIndicator,
    FlatList,
    RefreshControl,
    TouchableOpacity,
} from "react-native";
import EventCard from "../../components/EventCard"
import { Event } from "../../types";
import InputField from "../../components/InputField";
import { deleteEvent, getEvents, createEvent } from "../../services/events";
import { useNavigation } from "@react-navigation/native";

const EventScreen = () => {

    const [searchQuery, setSearchQuery] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [data, setData] = useState<Event[]>([]);
    const [error, setError] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [refreshing, setRefreshing] = useState(false);
    const [loadingMore, setLoadingMore] = useState(false);
    const [hasMore, setHasMore] = useState(true);

    const navigation = useNavigation<any>();

    const loadEvents = async (p = currentPage, isLoadMore: boolean = false) => {
        try {
            if (isLoadMore) {
                setLoadingMore(true);
            } else {
                if (p === 1) setIsLoading(true);
            }

            const response = await getEvents(p, 20);

            if (isLoadMore) {
                setData(prevData => [...prevData, ...response.data]);
            } else {
                setData(response.data);
            }

            setCurrentPage(response.pagination.page);
            setTotalPages(response.pagination.pages)

        } catch (error) {
            console.error('Failed to load events:', error);
            setError(true);
        } finally {
            setIsLoading(false);
            setRefreshing(false);
            setLoadingMore(false);
        }
    }

    useEffect(() => {
        loadEvents(1, false);
    }, []);

    const handleRefresh = useCallback(() => {
        setRefreshing(true);
        setHasMore(true);
        loadEvents(1);
    }, []);

    const loadMore = () => {
        if (!loadingMore && hasMore && currentPage < totalPages) {
            loadEvents(currentPage + 1, true);
        }
    };


    const handleSearch = (query: string) => {
        setSearchQuery(query);
        const lowerCaseQuery = query.toLowerCase().trim();
        if (lowerCaseQuery === "") {
            loadEvents(1, false);
            return
        }


        const filteredData = data.filter((event: Event) => {

            const { name, location, description } = event;
            return name?.toLowerCase().includes(lowerCaseQuery) ||
                location?.toLowerCase().includes(lowerCaseQuery) ||
                description?.toLowerCase().includes(lowerCaseQuery)

        })
        setData(filteredData)
    }

    const renderFooter = () => {
        if (!loadingMore) return null;

        return (
            <View style={{
                padding: 20,
                justifyContent: 'center',
                alignItems: 'center'
            }}>
                <ActivityIndicator size="large" color="#0000ff" />
            </View>
        );
    };


    if (isLoading && !refreshing) {
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
                <TouchableOpacity
                    onPress={() => {
                        setError(false);
                        setIsLoading(true);
                        loadEvents(1, false);
                    }}
                >
                    <Text style={{ color: '#0000ff', fontWeight: 'bold' }}>Spróbuj ponownie</Text>
                </TouchableOpacity>
            </View>
        );
    }

    return (
        <SafeAreaView style={{ flex: 1, marginHorizontal: 10 }}>
            <View style={{ marginVertical: 10 }}>
                <InputField
                    placeholder="Szukaj"
                    onChangeText={(query) => handleSearch(query)}
                    value={searchQuery}
                />
                <TouchableOpacity onPress={() => navigation.navigate('AddEvent')} style={{ backgroundColor: '#045ddaff', alignItems: 'center', padding: 10, borderRadius: 25 }} >
                    <Text style={{color: '#ffffff'}}>Dodaj wydarzenie</Text>
                </TouchableOpacity>

            </View>


            <FlatList
                data={data}
                renderItem={({ item }) => <EventCard item={item} />}
                keyExtractor={(item: Event) => item.event_id!}
                refreshControl={
                    <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
                }
                ListFooterComponent={renderFooter}
                onEndReached={loadMore}
                onEndReachedThreshold={0.5}
                initialNumToRender={10}
                maxToRenderPerBatch={10}
                windowSize={10}
                removeClippedSubviews={true}

            />

        </SafeAreaView>
    );
}



export default EventScreen;