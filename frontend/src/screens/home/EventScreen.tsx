import React, { useState, useEffect, useCallback } from "react";
import {
    View,
    Text,
    SafeAreaView,
    ActivityIndicator,
    FlatList,
    RefreshControl,
    TouchableOpacity,
    Image,
    StyleSheet,
} from "react-native";
import EventCard from "../../components/EventCard"
import { Event } from "../../types";
import InputField from "../../components/InputField";
import { getEvents } from "../../services/events";
import { useNavigation } from "@react-navigation/native";
import { THEME } from "../../utils/constants";
import ItemSeparator from "../../components/ItemSeparator"

const BASE_TILE_SIZE = 30;
const FILTER_ICON_SIZE = 30;
const FILTER_SPRITE_WIDTH = 90;
const FILTER_SPRITE_HEIGHT = 90;
const FILTER_SPRITE_SCALE = FILTER_ICON_SIZE / BASE_TILE_SIZE;
const FILTER_ICON_OFFSET = { x: -BASE_TILE_SIZE, y: 0 };

const parseEventDateTime = (event: Event): Date | null => {
    if (!event?.date || !event?.time) return null;

    const [day, month, year] = event.date.split('.').map(Number);
    const [hours, minutes] = event.time.split(':').map(Number);

    if ([day, month, year, hours, minutes].some(Number.isNaN)) {
        return null;
    }

    return new Date(year, month - 1, day, hours, minutes, 0, 0);
};

const sortEventsByTime = (events: Event[]): Event[] => {
    const now = new Date();
    const upcoming: Event[] = [];
    const past: Event[] = [];

    for (const event of events) {
        const dateTime = parseEventDateTime(event);
        if (dateTime && dateTime >= now) {
            upcoming.push(event);
        } else {
            past.push(event);
        }
    }

    upcoming.sort((a, b) => {
        const aTime = parseEventDateTime(a)?.getTime() ?? Number.MAX_SAFE_INTEGER;
        const bTime = parseEventDateTime(b)?.getTime() ?? Number.MAX_SAFE_INTEGER;
        return aTime - bTime;
    });

    past.sort((a, b) => {
        const aTime = parseEventDateTime(a)?.getTime() ?? 0;
        const bTime = parseEventDateTime(b)?.getTime() ?? 0;
        return bTime - aTime;
    });

    return [...upcoming, ...past];
};

const EventScreen = () => {

    const [searchQuery, setSearchQuery] = useState("");
    const [isLoading, setIsLoading] = useState(false);
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
                setData(prevData => sortEventsByTime([...prevData, ...response.data]));
            } else {
                setData(sortEventsByTime(response.data));
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
        // Listen for screen focus to lazy-load events
        const unsubscribe = navigation.addListener('focus', () => {
            if (data.length === 0 && !error) {
                loadEvents(1, false);
            }
        });
        return unsubscribe;
    }, [navigation, data.length, error]);

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
        setData(sortEventsByTime(filteredData))
    }

    const renderFooter = () => {
        if (!loadingMore) return null;

        return (
            <View style={{
                padding: 20,
                justifyContent: 'center',
                alignItems: 'center'
            }}>
                <ActivityIndicator size="large" color={THEME.colors.transparentOrange} />
            </View>
        );
    };


    if (isLoading && !refreshing) {
        return (
            <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: THEME.colors.lm_bg }}>
                <ActivityIndicator size="large" />
            </View>
        );
    }

    if (error) {
        return (
            <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: THEME.colors.lm_bg }}>
                <Text>Wystąpił błąd podczas pobierania wydarzeń</Text>
                <TouchableOpacity
                    onPress={() => {
                        setError(false);
                        setIsLoading(true);
                        loadEvents(1, false);
                    }}
                >
                    <Text style={{ color: THEME.colors.transparentOrange, fontWeight: 'bold' }}>Spróbuj ponownie</Text>
                </TouchableOpacity>
            </View>
        );
    }

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: THEME.colors.lm_bg }}>
            <View style={styles.searchRowContainer}>
                <View style={styles.searchInputContainer}>
                    <InputField
                        placeholder="Szukaj"
                        onChangeText={(query) => handleSearch(query)}
                        value={searchQuery}
                        showSearchSpriteIcon
                        reserveErrorSpace={false}
                    />
                </View>
                <TouchableOpacity
                    onPress={() => navigation.navigate("EventFilters")}
                    style={styles.filterButton}
                    activeOpacity={0.8}
                >
                    <View style={styles.filterIconContainer}>
                        <Image
                            source={require("../../../assets/iconset1.jpg")}
                            style={styles.filterIconImage}
                            resizeMode="cover"
                        />
                    </View>
                </TouchableOpacity>
            </View>


            <FlatList
                data={data}
                renderItem={({ item }) => <EventCard item={item} />}
                keyExtractor={(item: Event) => item.id!}
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
                ItemSeparatorComponent={ItemSeparator}

            />

        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    searchRowContainer: {
        marginHorizontal: 10,
        marginTop: 5,
        flexDirection: "row",
        alignItems: "center",
    },
    searchInputContainer: {
        flex: 1,
    },
    filterButton: {
        marginLeft: 10,
        width: 38,
        height: 38,
        borderRadius: 19,
        alignItems: "center",
        justifyContent: "center",
    },
    filterIconContainer: {
        width: FILTER_ICON_SIZE,
        height: FILTER_ICON_SIZE,
        overflow: "hidden",
    },
    filterIconImage: {
        width: FILTER_SPRITE_WIDTH * FILTER_SPRITE_SCALE,
        height: FILTER_SPRITE_HEIGHT * FILTER_SPRITE_SCALE,
        transform: [
            { translateX: FILTER_ICON_OFFSET.x * FILTER_SPRITE_SCALE },
            { translateY: FILTER_ICON_OFFSET.y * FILTER_SPRITE_SCALE },
        ],
    },
});



export default EventScreen;