import {
  Camera,
  CircleLayer,
  MapView,
  ShapeSource,
  SymbolLayer,
} from "@maplibre/maplibre-react-native";
import {
  useFocusEffect,
  useNavigation,
  useRoute,
} from "@react-navigation/native";
import Constants from "expo-constants";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import AppIcon from "../../components/AppIcon";
import Button from "../../components/Button";
import { useTheme } from "../../contexts/ThemeContext";
import { getMapEvents } from "../../services/events";
import { Event } from "../../types";
import { MESSAGES } from "../../utils/constants";

const DEFAULT_CAMERA = {
  centerCoordinate: [19.9061, 50.0686] as [number, number],
  zoomLevel: 17.5,
  heading: 13,
};

const MAP_REFRESH_COOLDOWN_MS = 60_000;

function useMapStyles() {
  const { colors } = useTheme();

  return useMemo(
    () =>
      StyleSheet.create({
        container: { flex: 1, justifyContent: "center", alignItems: "center" },
        mapcontainer: { width: "100%", height: "100%", position: "relative" },
        map: { flex: 1 },
        resetButton: {
          position: "absolute",
          bottom: 0,
          right: 5,
          maxWidth: 80,
        },
        eventsPanel: {
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: 280,
        },
        eventsPanelHeader: {
          flexDirection: "row",
          justifyContent: "space-between",
          alignItems: "center",
          paddingHorizontal: 15,
          // paddingVertical: 12,
          minHeight: 50,
          borderBottomWidth: 1,
          borderBottomColor: colors.border,
          backgroundColor: colors.highlight,
        },
        eventsPanelTitle: {
          fontSize: 16,
          fontWeight: "700",
          color: colors.textSecondary,
        },
        eventsPanelHeaderButtons: {
          flexDirection: "row",
          gap: 25,
          alignItems: "center",
        },
        closePanelButton: {
          fontSize: 20,
          fontWeight: "bold",
          color: colors.textSecondary,
        },
        filterPanelButton: {
          marginTop: 3,
          backgroundColor: colors.textSecondary,
        },
        eventsListContent: {
          flex: 1,
        },
        eventListItem: {
          paddingHorizontal: 15,
          paddingVertical: 12,
          borderBottomWidth: 1,
          borderBottomColor: colors.border,
        },
        eventListItemSelected: {
          backgroundColor: colors.transparentHighlight,
          borderLeftWidth: 4,
          borderLeftColor: colors.highlight,
          paddingLeft: 11,
        },
        eventListItemName: {
          fontSize: 14,
          fontWeight: "600",
          color: colors.text,
          marginBottom: 4,
        },
        eventListItemNameSelected: {
          color: colors.textSecondary,
        },
        eventListItemTime: {
          fontSize: 12,
          color: colors.searchWord,
        },
        toggleListButton: {
          position: "absolute",
          left: 10,
          top: 10,
          width: 40,
          height: 40,
        },
        toggleListButtonText: {
          fontSize: 20,
          color: colors.textSecondary,
        },
        loadingContainer: {
          flex: 1,
          justifyContent: "center",
          alignItems: "center",
        },
        emptyState: {
          flex: 1,
          justifyContent: "center",
          alignItems: "center",
          paddingHorizontal: 15,
        },
        emptyStateText: {
          fontSize: 14,
          color: colors.searchWord,
          textAlign: "center",
        },
        filterContainer: {
          padding: 15,
          flex: 1,
        },
        filterLabel: {
          fontSize: 14,
          fontWeight: "600",
          color: colors.text,
          marginBottom: 8,
          marginTop: 15,
        },
        filterInput: {
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 8,
          padding: 10,
          color: colors.text,
          backgroundColor: colors.background,
        },
        timeRangeRow: {
          flexDirection: "row",
          gap: 10,
          alignItems: "center",
        },
        timeInput: {
          flex: 1,
        },
        privacyRow: {
          flexDirection: "row",
          gap: 10,
        },
        privacyButton: {
          flex: 1,
          paddingVertical: 8,
          borderWidth: 1,
          borderColor: colors.border,
          borderRadius: 8,
          alignItems: "center",
        },
        privacyButtonActive: {
          backgroundColor: colors.highlight,
          borderColor: colors.highlight,
        },
        privacyButtonText: {
          color: colors.text,
          fontSize: 13,
          fontWeight: "500",
        },
        privacyButtonTextActive: {
          color: colors.textSecondary,
        },
        clearFiltersBtn: {
          marginTop: 30,
        },
      }),
    [colors],
  );
}

export default function MapScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const cameraRef = useRef<any>(null);
  const [cameraPosition, setCameraPosition] = useState(DEFAULT_CAMERA);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [showEventsList, setShowEventsList] = useState(false);
  const [showEventsFilter, setShowEventsFilter] = useState(false);
  const [events, setEvents] = useState<Event[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const [filterAuthor, setFilterAuthor] = useState("");
  const [filterTimeStart, setFilterTimeStart] = useState("");
  const [filterTimeEnd, setFilterTimeEnd] = useState("");
  const [filterPrivacy, setFilterPrivacy] = useState<
    "all" | "public" | "private"
  >("all");

  const MAPTILER_KEY = Constants.expoConfig?.extra?.MAPTILER_KEY || "";
  const hasLoadedOnceRef = useRef(false);
  const lastFetchedAtRef = useRef(0);
  const inFlightRef = useRef<Promise<void> | null>(null);

  const { colors } = useTheme();
  const styles = useMapStyles();

  const fetchMapEvents = useCallback(
    async ({
      force = false,
      userInitiated = false,
    }: { force?: boolean; userInitiated?: boolean } = {}) => {
      if (inFlightRef.current) {
        return inFlightRef.current;
      }

      const now = Date.now();
      const isFresh = now - lastFetchedAtRef.current < MAP_REFRESH_COOLDOWN_MS;
      if (!force && isFresh) {
        return;
      }

      const request = (async () => {
        if (userInitiated) {
          setIsRefreshing(true);
        } else if (!hasLoadedOnceRef.current) {
          setIsLoading(true);
        }

        try {
          const upcomingEvents = await getMapEvents();
          setEvents(upcomingEvents);
          hasLoadedOnceRef.current = true;
          lastFetchedAtRef.current = Date.now();
        } catch (error) {
          console.error("Error fetching map events:", error);
        } finally {
          setIsLoading(false);
          setIsRefreshing(false);
        }
      })();

      inFlightRef.current = request;
      try {
        await request;
      } finally {
        inFlightRef.current = null;
      }
    },
    [],
  );

  useEffect(() => {
    fetchMapEvents({ force: true });
  }, [fetchMapEvents]);

  useFocusEffect(
    useCallback(() => {
      fetchMapEvents();
    }, [fetchMapEvents]),
  );

  const mapStyle = useMemo(
    () =>
      `https://api.maptiler.com/maps/streets-v4/style.json?key=${MAPTILER_KEY}`,
    [MAPTILER_KEY],
  );

  const resetCamera = () => {
    cameraRef.current?.setCamera?.({
      centerCoordinate: DEFAULT_CAMERA.centerCoordinate,
      zoomLevel: DEFAULT_CAMERA.zoomLevel,
      heading: DEFAULT_CAMERA.heading,
      animationDuration: 1200,
      animationMode: "flyTo",
    });
    setCameraPosition(DEFAULT_CAMERA);
  };

  const focusEventOnMap = useCallback(
    (eventId: string, location: string) => {
      try {
        const coords = JSON.parse(location) as [number, number];
        if (!Array.isArray(coords) || coords.length !== 2) {
          return;
        }

        setSelectedEventId(eventId);
        cameraRef.current?.setCamera?.({
          centerCoordinate: coords,
          zoomLevel: 20,
          heading: cameraPosition.heading,
          animationDuration: 1200,
          animationMode: "flyTo",
        });

        setCameraPosition((prev) => ({
          ...prev,
          centerCoordinate: coords,
          zoomLevel: 22,
        }));
      } catch {
        // Ignore invalid location payload.
      }
    },
    [cameraPosition.heading],
  );

  useEffect(() => {
    const focusEvent = route.params?.focusEvent as
      | { id?: string; location?: string }
      | undefined;
    if (!focusEvent?.id || !focusEvent?.location) {
      return;
    }

    focusEventOnMap(focusEvent.id, focusEvent.location);
    navigation.setParams?.({ focusEvent: undefined });
  }, [route.params?.focusEvent, navigation, focusEventOnMap]);

  const handleEventSelect = (event: Event) => {
    focusEventOnMap(event.id, event.location);
  };

  const openEventDetails = (event: Event) => {
    setSelectedEventId(event.id);
    navigation.navigate("EventDetails", { event });
  };

  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      if (filterAuthor) {
        const authorMatch = (event as any).author
          ?.toLowerCase()
          .includes(filterAuthor.toLowerCase());
        if (!authorMatch) {
          return false;
        }
      }

      if (filterPrivacy !== "all") {
        const isEventPrivate = !!(event as any).isPrivate;
        if (filterPrivacy === "public" && isEventPrivate) return false;
        if (filterPrivacy === "private" && !isEventPrivate) return false;
      }

      // filter assumes time is in format "HH:mm"
      if (filterTimeStart && event.time) {
        if (event.time < filterTimeStart) return false;
      }
      if (filterTimeEnd && event.time) {
        if (event.time > filterTimeEnd) return false;
      }

      return true;
    });
  }, [events, filterAuthor, filterPrivacy, filterTimeStart, filterTimeEnd]);

  const eventsGeoJSON = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: filteredEvents
        .map((event) => {
          try {
            const coordinates = JSON.parse(event.location) as [number, number];
            return {
              type: "Feature" as const,
              geometry: {
                type: "Point" as const,
                coordinates,
              },
              properties: {
                id: event.id,
                name: event.name,
              },
            };
          } catch {
            return null;
          }
        })
        .filter((feature): feature is NonNullable<typeof feature> =>
          Boolean(feature),
        ),
    }),
    [filteredEvents],
  );

  const handleShapePress = (event: any) => {
    const feature =
      event?.features?.[0] ?? event?.nativeEvent?.payload?.features?.[0];

    if (!feature) {
      return;
    }

    if (feature.properties?.cluster) {
      const coords = feature.geometry?.coordinates as [number, number];

      const targetZoom = Math.min(cameraPosition.zoomLevel + 3, 22);

      cameraRef.current?.setCamera?.({
        centerCoordinate: coords,
        zoomLevel: targetZoom,
        animationDuration: 400,
        animationMode: "flyTo",
      });

      setCameraPosition((prev) => ({
        ...prev,
        centerCoordinate: coords,
        zoomLevel: targetZoom,
      }));
      return;
    }

    const eventId = feature?.properties?.id;
    if (!eventId) {
      return;
    }

    const clickedEvent = filteredEvents.find((item) => item.id === eventId);
    if (clickedEvent) {
      openEventDetails(clickedEvent);
    }
  };

  const clearFilters = () => {
    setFilterAuthor("");
    setFilterTimeStart("");
    setFilterTimeEnd("");
    setFilterPrivacy("all");
  };

  return (
    <View style={styles.container}>
      <View style={styles.mapcontainer}>
        <MapView
          style={styles.map}
          mapStyle={mapStyle}
          logoEnabled={false}
          attributionPosition={{ bottom: 8, right: 8 }}
        >
          <Camera
            ref={cameraRef}
            zoomLevel={cameraPosition.zoomLevel}
            centerCoordinate={cameraPosition.centerCoordinate}
            animationMode="flyTo"
            animationDuration={1500}
            heading={cameraPosition.heading}
            minZoomLevel={16.5}
            maxZoomLevel={23}
          />
          <ShapeSource
            id="events"
            shape={eventsGeoJSON}
            onPress={handleShapePress}
            cluster={true}
            clusterRadius={35}
            clusterMaxZoomLevel={21}
            maxZoomLevel={24}
          >
            <CircleLayer
              id="clusters"
              filter={["has", "point_count"]}
              style={{
                circleColor: colors.background,
                circleRadius: [
                  "step",
                  ["get", "point_count"],
                  18, // Base radius
                  5, // If 5 or more points
                  22, // Radius becomes 22
                  50, // If 50 or more points
                  28, // Radius becomes 28
                ],
                circleStrokeColor: colors.highlight,
                circleStrokeWidth: 2,
                circleOpacityTransition: { duration: 0, delay: 0 },
              }}
            />
            <SymbolLayer
              id="cluster-count"
              filter={["has", "point_count"]}
              style={{
                textField: "{point_count_abbreviated}",
                textSize: 14,
                textColor: colors.highlight,
                textPitchAlignment: "map",
                textAllowOverlap: true,
                textOpacityTransition: { duration: 0, delay: 0 },
              }}
            />
            <CircleLayer
              id="event-circles"
              filter={["!", ["has", "point_count"]]}
              style={{
                circleRadius: selectedEventId
                  ? [
                      "case",
                      ["==", ["get", "id"], selectedEventId],
                      13, // when selected
                      10, // default
                    ]
                  : 10,
                circleStrokeColor: colors.highlight,
                circleStrokeWidth: 5,
                circleColor: selectedEventId
                  ? [
                      "case",
                      ["==", ["get", "id"], selectedEventId],
                      colors.highlight, // when selected
                      colors.background, // default
                    ]
                  : colors.background,
              }}
            />
          </ShapeSource>
        </MapView>

        {/* Events List Panel */}
        {showEventsList && (
          <View style={styles.eventsPanel}>
            <View style={styles.eventsPanelHeader}>
              <Text style={styles.eventsPanelTitle}>
                {showEventsFilter ? MESSAGES.MAP.FILTERS : MESSAGES.MAP.EVENTS}
              </Text>
              <View style={styles.eventsPanelHeaderButtons}>
                {showEventsFilter ? (
                  <TouchableOpacity onPress={() => setShowEventsFilter(false)}>
                    <Text style={[styles.closePanelButton, { fontSize: 16 }]}>
                      {MESSAGES.UI.DONE}
                    </Text>
                  </TouchableOpacity>
                ) : (
                  <>
                    <TouchableOpacity onPress={() => setShowEventsFilter(true)}>
                      <View style={styles.filterPanelButton}>
                        <AppIcon name="Sliders" size={20} />
                      </View>
                    </TouchableOpacity>
                    <TouchableOpacity onPress={() => setShowEventsList(false)}>
                      <Text style={styles.closePanelButton}>✕</Text>
                    </TouchableOpacity>
                  </>
                )}
              </View>
            </View>

            {showEventsFilter ? (
              <ScrollView style={styles.filterContainer}>
                <Text style={[styles.filterLabel, { marginTop: 5 }]}>
                  {MESSAGES.MAP.AUTHOR}
                </Text>
                <TextInput
                  style={styles.filterInput}
                  placeholder={MESSAGES.PLACEHOLDERS.FILTER_AUTHOR}
                  placeholderTextColor={colors.searchWord}
                  value={filterAuthor}
                  onChangeText={setFilterAuthor}
                />

                <Text style={styles.filterLabel}>
                  {MESSAGES.MAP.TIME_RANGE}
                </Text>
                <View style={styles.timeRangeRow}>
                  <TextInput
                    style={[styles.filterInput, styles.timeInput]}
                    placeholder="Start e.g. 09:00"
                    placeholderTextColor={colors.searchWord}
                    value={filterTimeStart}
                    onChangeText={setFilterTimeStart}
                  />
                  <Text style={{ color: colors.text }}>-</Text>
                  <TextInput
                    style={[styles.filterInput, styles.timeInput]}
                    placeholder="End e.g. 17:00"
                    placeholderTextColor={colors.searchWord}
                    value={filterTimeEnd}
                    onChangeText={setFilterTimeEnd}
                  />
                </View>

                <Text style={styles.filterLabel}>{MESSAGES.MAP.PRIVACY}</Text>
                <View style={styles.privacyRow}>
                  {(["all", "public", "private"] as const).map((type) => (
                    <TouchableOpacity
                      key={type}
                      style={[
                        styles.privacyButton,
                        filterPrivacy === type && styles.privacyButtonActive,
                      ]}
                      onPress={() => setFilterPrivacy(type)}
                    >
                      <Text
                        style={[
                          styles.privacyButtonText,
                          filterPrivacy === type &&
                            styles.privacyButtonTextActive,
                        ]}
                      >
                        {type.charAt(0).toUpperCase() + type.slice(1)}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>

                <Button
                  title={MESSAGES.MAP.CLEAR_FILTERS}
                  onPress={clearFilters}
                  style={styles.clearFiltersBtn}
                />
              </ScrollView>
            ) : isLoading && events.length === 0 ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color={colors.highlight} />
              </View>
            ) : (
              <ScrollView
                style={styles.eventsListContent}
                refreshControl={
                  <RefreshControl
                    refreshing={isRefreshing}
                    onRefresh={() =>
                      fetchMapEvents({ force: true, userInitiated: true })
                    }
                    tintColor={colors.highlight}
                  />
                }
              >
                {filteredEvents.length === 0 ? (
                  <View style={styles.emptyState}>
                    <Text style={styles.emptyStateText}>
                      {events.length > 0
                        ? "No events match your filters."
                        : MESSAGES.MAP.NO_EVENTS}
                    </Text>
                  </View>
                ) : (
                  filteredEvents.map((event) => (
                    <TouchableOpacity
                      key={event.id}
                      style={[
                        styles.eventListItem,
                        selectedEventId === event.id &&
                          styles.eventListItemSelected,
                      ]}
                      onPress={() => handleEventSelect(event)}
                    >
                      <Text
                        style={[
                          styles.eventListItemName,
                          selectedEventId === event.id &&
                            styles.eventListItemNameSelected,
                        ]}
                      >
                        {event.name}
                      </Text>
                      <Text>{event.description}</Text>
                      <Text style={styles.eventListItemTime}>
                        {event.date} {event.time}
                      </Text>
                    </TouchableOpacity>
                  ))
                )}
              </ScrollView>
            )}
          </View>
        )}

        {/* Events List Button */}
        {!showEventsList && (
          <Button
            style={styles.toggleListButton}
            onPress={() => setShowEventsList(true)}
            title="☰"
          />
        )}

        <Button
          style={styles.resetButton}
          onPress={resetCamera}
          title="Reset"
        />
      </View>
    </View>
  );
}
