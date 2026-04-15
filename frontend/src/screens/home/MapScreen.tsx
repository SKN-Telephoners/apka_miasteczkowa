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
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { useEvents } from "../../contexts/EventContext";
import { Event } from "../../types";

const DEFAULT_CAMERA = {
  centerCoordinate: [19.9061, 50.0686] as [number, number],
  zoomLevel: 17.5,
  heading: 13,
};

export default function MapScreen() {
  const [cameraPosition, setCameraPosition] = useState(DEFAULT_CAMERA);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [showEventsList, setShowEventsList] = useState(false);
  const { events, isLoading, fetchEvents } = useEvents();
  const MAPTILER_KEY = Constants.expoConfig?.extra?.MAPTILER_KEY || "";

  useEffect(() => {
    if (events.length === 0) {
      fetchEvents();
    }
  }, []);

  const mapStyle = useMemo(
    () =>
      `https://api.maptiler.com/maps/streets-v4/style.json?key=${MAPTILER_KEY}`,
    [MAPTILER_KEY],
  );

  const resetCamera = () => {
    setCameraPosition(DEFAULT_CAMERA);
  };

  const handleEventSelect = (event: Event) => {
    setSelectedEventId(event.id);
    const coords = JSON.parse(event.location) as [number, number];
    setCameraPosition({
      ...cameraPosition,
      centerCoordinate: coords,
      zoomLevel: 20,
    });
  };

  const eventsGeoJSON = useMemo(
    () => ({
      type: "FeatureCollection" as const,
      features: events
        .filter((event) => event.location)
        .map((event) => ({
          type: "Feature" as const,
          geometry: {
            type: "Point" as const,
            coordinates: JSON.parse(event.location) as [number, number],
          },
          properties: {
            id: event.id,
            name: event.name,
          },
        })),
    }),
    [events],
  );

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
            zoomLevel={cameraPosition.zoomLevel}
            centerCoordinate={cameraPosition.centerCoordinate}
            animationMode="flyTo"
            animationDuration={1500}
            heading={cameraPosition.heading}
            minZoomLevel={16.5}
          />
          <ShapeSource id="events" shape={eventsGeoJSON}>
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
              <ScrollView style={styles.eventsListContent}>
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
