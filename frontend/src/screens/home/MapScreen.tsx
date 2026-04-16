import {
  Camera,
  CircleLayer,
  MapView,
  ShapeSource,
} from "@maplibre/maplibre-react-native";
import Constants from "expo-constants";
import { useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useFocusEffect, useNavigation } from "@react-navigation/native";
import { getMapEvents } from "../../services/events";
import { Event } from "../../types";
import { useCallback, useRef } from "react";

const DEFAULT_CAMERA = {
  centerCoordinate: [19.9061, 50.0686] as [number, number],
  zoomLevel: 17.5,
  heading: 13,
};

const MAP_REFRESH_COOLDOWN_MS = 30_000;

export default function MapScreen() {
  const navigation = useNavigation<any>();
  const cameraRef = useRef<any>(null);
  const [cameraPosition, setCameraPosition] = useState(DEFAULT_CAMERA);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [showEventsList, setShowEventsList] = useState(false);
  const [events, setEvents] = useState<Event[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const MAPTILER_KEY = Constants.expoConfig?.extra?.MAPTILER_KEY || "";
  const hasLoadedOnceRef = useRef(false);
  const lastFetchedAtRef = useRef(0);
  const inFlightRef = useRef<Promise<void> | null>(null);

  const fetchMapEvents = useCallback(
    async ({ force = false, userInitiated = false }: { force?: boolean; userInitiated?: boolean } = {}) => {
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
      // Silent refresh on focus with a cooldown to avoid unnecessary network calls.
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

  const handleEventSelect = (event: Event) => {
    setSelectedEventId(event.id);
    try {
      const coords = JSON.parse(event.location) as [number, number];
      setCameraPosition((prev) => ({
        ...prev,
        centerCoordinate: coords,
        zoomLevel: 20,
      }));
    } catch (error) {
      console.error("Error parsing event location:", error);
    }
  };

  const openEventDetails = (event: Event) => {
    setSelectedEventId(event.id);
    navigation.navigate("EventDetails", { event });
  };

  const eventsGeoJSON = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: events
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
        .filter((feature): feature is NonNullable<typeof feature> => Boolean(feature)),
    }),
    [events],
  );

  const handleShapePress = (event: any) => {
    const feature = event?.features?.[0] ?? event?.nativeEvent?.payload?.features?.[0];
    const eventId = feature?.properties?.id;

    if (!eventId) {
      return;
    }

    const clickedEvent = events.find((item) => item.id === eventId);
    if (clickedEvent) {
      openEventDetails(clickedEvent);
    }
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
          />
          <ShapeSource id="events" shape={eventsGeoJSON} onPress={handleShapePress}>
            <CircleLayer
              id="event-circles"
              style={{
                circleRadius: 5,
                circleColor: "#007AFF",
              }}
            />
          </ShapeSource>
        </MapView>

        {/* Events List Panel */}
        {showEventsList && (
          <View style={styles.eventsPanel}>
            <View style={styles.eventsPanelHeader}>
              <Text style={styles.eventsPanelTitle}>Events</Text>
              <TouchableOpacity onPress={() => setShowEventsList(false)}>
                <Text style={styles.closePanelButton}>✕</Text>
              </TouchableOpacity>
            </View>
            {isLoading && events.length === 0 ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#007AFF" />
              </View>
            ) : (
              <ScrollView
                style={styles.eventsListContent}
                refreshControl={
                  <RefreshControl
                    refreshing={isRefreshing}
                    onRefresh={() => fetchMapEvents({ force: true, userInitiated: true })}
                    tintColor="#007AFF"
                  />
                }
              >
                {events.length === 0 ? (
                  <View style={styles.emptyState}>
                    <Text style={styles.emptyStateText}>
                      No events available
                    </Text>
                  </View>
                ) : (
                  events.map((event) => (
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
          <TouchableOpacity
            style={styles.toggleListButton}
            onPress={() => setShowEventsList(true)}
          >
            <Text style={styles.toggleListButtonText}>☰</Text>
          </TouchableOpacity>
        )}

        <TouchableOpacity style={styles.resetButton} onPress={resetCamera}>
          <Text style={styles.resetButtonText}>Reset Location</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

// needs unified styles
const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", alignItems: "center" },
  mapcontainer: { width: "100%", height: "100%", position: "relative" },
  map: { flex: 1 },
  resetButton: {
    position: "absolute",
    bottom: 20,
    right: 5,
    backgroundColor: "#007AFF",
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: 8,
  },
  resetButtonText: {
    color: "#fff",
    fontSize: 14,
    fontWeight: "600",
  },
  eventsPanel: {
    position: "absolute",
    left: 0,
    top: 0,
    bottom: 0,
    width: 280,
    backgroundColor: "#fff",
    borderRightWidth: 1,
    borderRightColor: "#e0e0e0",
  },
  eventsPanelHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 15,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#e0e0e0",
    backgroundColor: "#f5f5f5",
  },
  eventsPanelTitle: {
    fontSize: 16,
    fontWeight: "700",
  },
  closePanelButton: {
    fontSize: 20,
    fontWeight: "bold",
  },
  eventsListContent: {
    flex: 1,
  },
  eventListItem: {
    paddingHorizontal: 15,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#f0f0f0",
  },
  eventListItemSelected: {
    backgroundColor: "#e3f2fd",
    borderLeftWidth: 4,
    borderLeftColor: "#007AFF",
    paddingLeft: 11,
  },
  eventListItemName: {
    fontSize: 13,
    fontWeight: "600",
    color: "#333",
    marginBottom: 4,
  },
  eventListItemNameSelected: {
    color: "#007AFF",
  },
  eventListItemTime: {
    fontSize: 12,
    color: "#999",
  },
  toggleListButton: {
    position: "absolute",
    left: 10,
    top: 10,
    width: 40,
    height: 40,
    backgroundColor: "#007AFF",
    justifyContent: "center",
    alignItems: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 3,
    elevation: 5,
  },
  toggleListButtonText: {
    fontSize: 20,
    color: "#fff",
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
    color: "#999",
    textAlign: "center",
  },
});
