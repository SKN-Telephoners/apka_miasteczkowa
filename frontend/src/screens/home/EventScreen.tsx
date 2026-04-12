import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
    View,
    Text,
    SafeAreaView,
    ActivityIndicator,
    FlatList,
    RefreshControl,
    TouchableOpacity,
    StyleSheet,
} from "react-native";
import EventCard from "../../components/EventCard"
import { DEFAULT_EVENT_FILTERS, Event, EventFilterState } from "../../types";
import InputField from "../../components/InputField";
import { getEvents } from "../../services/events";
import { useFocusEffect, useNavigation, useRoute } from "@react-navigation/native";
import { THEME } from "../../utils/constants";
import ItemSeparator from "../../components/ItemSeparator"
import { useInfiniteQuery } from "@tanstack/react-query"
import SvgSpriteIcon from "../../components/SvgSpriteIcon";
import { useTheme } from "../../contexts/ThemeContext";

const BASE_TILE_SIZE = 30;
const FILTER_ICON_SIZE = 30;
const FILTER_ICON_OFFSET = { x: -BASE_TILE_SIZE, y: 0 };
const PAGE_SIZE = 20;

const mergeUniqueEventsById = (events: Event[]): Event[] => {
    const uniqueEvents = new Map<string, Event>();
    for (const event of events) {
        if (!event?.id) continue;
        uniqueEvents.set(event.id, event);
    }
    return Array.from(uniqueEvents.values());
};

const EventScreen = () => {

    const [searchQuery, setSearchQuery] = useState("");
    const [debouncedSearchQuery, setDebouncedSearchQuery] = useState("");
    const [canLoadMore, setCanLoadMore] = useState(false);
    const [filters, setFilters] = useState<EventFilterState>(DEFAULT_EVENT_FILTERS);
    const { colors } = useTheme();

    const navigation = useNavigation<any>();
    const route = useRoute<any>();

    useEffect(() => {
        const timeout = setTimeout(() => {
            setDebouncedSearchQuery(searchQuery.trim());
        }, 350);

        return () => clearTimeout(timeout);
    }, [searchQuery]);

    const feedParams = useMemo(
        () => ({
            q: debouncedSearchQuery || undefined,
            visibility: filters.visibility,
            participation: filters.participation,
            created_window: filters.createdAtWindow,
            sort_mode: filters.sortMode,
            creator_source: filters.creatorSource,
        }),
        [debouncedSearchQuery, filters.createdAtWindow, filters.participation, filters.sortMode, filters.visibility, filters.creatorSource],
    );

    const {
        data,
        error,
        isPending,
        isRefetching,
        isFetchingNextPage,
        hasNextPage,
        fetchNextPage,
        refetch,
    } = useInfiniteQuery({
        queryKey: ["events-feed", PAGE_SIZE, feedParams],
        queryFn: ({ pageParam }) => getEvents(pageParam, PAGE_SIZE, feedParams),
        initialPageParam: 1,
        getNextPageParam: (lastPage) => {
            const nextPage = lastPage.pagination.page + 1;
            return nextPage <= lastPage.pagination.pages ? nextPage : undefined;
        },
        refetchOnMount: true,
    });

    const allEvents = useMemo(() => {
        const mergedPages = data?.pages.flatMap((page) => page.data) ?? [];
        return mergeUniqueEventsById(mergedPages);
    }, [data]);

    useFocusEffect(
        useCallback(() => {
            refetch();
        }, [refetch]),
    );

    useEffect(() => {
        if (!route?.params?.eventFilters) return;
        setFilters(route.params.eventFilters as EventFilterState);
    }, [route?.params?.eventFilters]);

    const handleRefresh = useCallback(() => {
        refetch();
    }, [refetch]);

    const loadMore = () => {
        if (!canLoadMore) return;
        if (hasNextPage && !isFetchingNextPage && !isRefetching) {
            setCanLoadMore(false);
            fetchNextPage();
        }
    };


    const handleSearch = (query: string) => {
        setSearchQuery(query);
    }

    const renderFooter = () => {
        if (!isFetchingNextPage) return null;

        return (
            <View style={{
                padding: 20,
                justifyContent: 'center',
                alignItems: 'center'
            }}>
                <ActivityIndicator size="large" color={colors.transparentHighlight} />
            </View>
        );
    };


    if (isPending && !isRefetching) {
        return (
            <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.background }}>
                <ActivityIndicator size="large" />
            </View>
        );
    }

    if (error) {
        return (
            <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: colors.background}}>
                <Text style={{ color: colors.text }}>Wystąpił błąd podczas pobierania wydarzeń</Text>
                <TouchableOpacity
                    onPress={() => {
                        refetch();
                    }}
                >
                    <Text style={{ color: colors.transparentHighlight, fontWeight: 'bold' }}>Spróbuj ponownie</Text>
                </TouchableOpacity>
            </View>
        );
    }

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: colors.background }}>
            <View style={styles.searchRowContainer}>
                <View style={styles.searchInputContainer}>
                    <InputField
                        placeholder="Szukaj wydarzeń"
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
                        <SvgSpriteIcon set={1} size={FILTER_ICON_SIZE} offsetX={FILTER_ICON_OFFSET.x} offsetY={FILTER_ICON_OFFSET.y} />
                    </View>
                </TouchableOpacity>
            </View>


            <FlatList
                data={allEvents}
                renderItem={({ item }) => <EventCard item={item} />}
                keyExtractor={(item: Event, index) => item.id || `${item.name}-${index}`}
                refreshControl={
                    <RefreshControl refreshing={isRefetching && !isFetchingNextPage} onRefresh={handleRefresh} />
                }
                ListFooterComponent={renderFooter}
                onEndReached={loadMore}
                onEndReachedThreshold={0.5}
                onMomentumScrollBegin={() => setCanLoadMore(true)}
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
    },
});



export default EventScreen;