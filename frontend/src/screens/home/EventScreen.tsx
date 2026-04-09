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
import { DEFAULT_EVENT_FILTERS, Event, EventCreatedAtFilter, EventFilterState } from "../../types";
import InputField from "../../components/InputField";
import { getEvents } from "../../services/events";
import { useNavigation, useRoute } from "@react-navigation/native";
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

const mergeUniqueEventsById = (events: Event[]): Event[] => {
    const uniqueEvents = new Map<string, Event>();
    for (const event of events) {
        if (!event?.id) continue;
        uniqueEvents.set(event.id, event);
    }
    return Array.from(uniqueEvents.values());
};

const parseCreatedAt = (createdAt?: string): Date | null => {
    if (!createdAt) return null;
    const parsed = new Date(createdAt);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const isPrivateEvent = (event: Event): boolean => {
    return event?.is_private === true || String(event?.is_private).toLowerCase() === "true";
};

const startOfToday = (now: Date): Date => {
    return new Date(now.getFullYear(), now.getMonth(), now.getDate());
};

const startOfWeek = (now: Date): Date => {
    const today = startOfToday(now);
    const day = today.getDay();
    const diff = day === 0 ? 6 : day - 1;
    today.setDate(today.getDate() - diff);
    return today;
};

const startOfMonth = (now: Date): Date => {
    return new Date(now.getFullYear(), now.getMonth(), 1);
};

const startOfYear = (now: Date): Date => {
    return new Date(now.getFullYear(), 0, 1);
};

const matchesAddedWindow = (event: Event, mode: EventCreatedAtFilter, now: Date): boolean => {
    const createdAt = parseCreatedAt(event.created_at);
    if (!createdAt) return false;

    const today = startOfToday(now);
    const week = startOfWeek(now);
    const month = startOfMonth(now);
    const year = startOfYear(now);

    if (mode === "all") return true;
    if (mode === "today") return createdAt >= today;
    if (mode === "week") return createdAt >= week;
    if (mode === "month") return createdAt >= month;
    if (mode === "year") return createdAt >= year;
    if (mode === "older") return createdAt < year;

    return true;
};

const sortFutureEvents = (events: Event[], mode: EventFilterState["sortMode"]): Event[] => {
    const sorted = [...events];

    if (mode === "members_desc") {
        sorted.sort((a, b) => Number(b.participant_count ?? 0) - Number(a.participant_count ?? 0));
        return sorted;
    }

    if (mode === "members_asc") {
        sorted.sort((a, b) => Number(a.participant_count ?? 0) - Number(b.participant_count ?? 0));
        return sorted;
    }

    if (mode === "comments_desc") {
        sorted.sort((a, b) => Number(b.comment_count ?? 0) - Number(a.comment_count ?? 0));
        return sorted;
    }

    if (mode === "comments_asc") {
        sorted.sort((a, b) => Number(a.comment_count ?? 0) - Number(b.comment_count ?? 0));
        return sorted;
    }

    sorted.sort((a, b) => {
        const aTime = parseEventDateTime(a)?.getTime() ?? Number.MAX_SAFE_INTEGER;
        const bTime = parseEventDateTime(b)?.getTime() ?? Number.MAX_SAFE_INTEGER;
        return aTime - bTime;
    });

    return sorted;
};

const applyFiltersAndSort = (events: Event[], query: string, filters: EventFilterState): Event[] => {
    const lowerCaseQuery = query.toLowerCase().trim();
    const now = new Date();

    let result = [...events];

    if (lowerCaseQuery) {
        result = result.filter((event) => {
            const { name, location, description } = event;
            return name?.toLowerCase().includes(lowerCaseQuery) ||
                location?.toLowerCase().includes(lowerCaseQuery) ||
                description?.toLowerCase().includes(lowerCaseQuery);
        });
    }

    if (filters.visibility === "public") {
        result = result.filter((event) => !isPrivateEvent(event));
    }

    if (filters.visibility === "private") {
        result = result.filter((event) => isPrivateEvent(event));
    }

    if (filters.createdAtWindow !== "all") {
        result = result.filter((event) => matchesAddedWindow(event, filters.createdAtWindow, now));
    }

    const futureEvents: Event[] = [];
    const pastEvents: Event[] = [];

    for (const event of result) {
        const eventDateTime = parseEventDateTime(event);
        if (eventDateTime && eventDateTime >= now) {
            futureEvents.push(event);
        } else {
            pastEvents.push(event);
        }
    }

    const sortedFuture = sortFutureEvents(futureEvents, filters.sortMode);
    const sortedPast = [...pastEvents].sort((a, b) => {
        const aTime = parseEventDateTime(a)?.getTime() ?? 0;
        const bTime = parseEventDateTime(b)?.getTime() ?? 0;
        return bTime - aTime;
    });

    return [...sortedFuture, ...sortedPast];
};

const EventScreen = () => {

    const [searchQuery, setSearchQuery] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [allEvents, setAllEvents] = useState<Event[]>([]);
    const [data, setData] = useState<Event[]>([]);
    const [error, setError] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [refreshing, setRefreshing] = useState(false);
    const [loadingMore, setLoadingMore] = useState(false);
    const [hasMore, setHasMore] = useState(true);
    const [filters, setFilters] = useState<EventFilterState>(DEFAULT_EVENT_FILTERS);

    const navigation = useNavigation<any>();
    const route = useRoute<any>();

    const loadEvents = async (p = currentPage, isLoadMore: boolean = false) => {
        try {
            if (isLoadMore) {
                setLoadingMore(true);
            } else {
                if (p === 1) setIsLoading(true);
            }

            const response = await getEvents(p, 20);
            const mergedEvents = isLoadMore
                ? mergeUniqueEventsById([...allEvents, ...response.data])
                : mergeUniqueEventsById(response.data);

            setAllEvents(mergedEvents);

            setData(applyFiltersAndSort(mergedEvents, searchQuery, filters));

            setCurrentPage(response.pagination.page);
            setTotalPages(response.pagination.pages)
            setHasMore(response.pagination.page < response.pagination.pages);

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
        // Refresh feed whenever screen regains focus (e.g. after creating event).
        const unsubscribe = navigation.addListener('focus', () => {
            setError(false);
            setHasMore(true);
            loadEvents(1, false);
        });
        return unsubscribe;
    }, [navigation]);

    useEffect(() => {
        if (!route?.params?.eventFilters) return;
        setFilters(route.params.eventFilters as EventFilterState);
    }, [route?.params?.eventFilters]);

    useEffect(() => {
        setData(applyFiltersAndSort(allEvents, searchQuery, filters));
    }, [allEvents, searchQuery, filters]);

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
                        showFloatingLabel={false}
                        reserveErrorSpace={false}
                    />
                </View>
                <TouchableOpacity
                    onPress={() => navigation.navigate("EventFilters", { initialFilters: filters })}
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