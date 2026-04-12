import { Camera, MapView, ShapeSource, CircleLayer } from "@maplibre/maplibre-react-native";
import Constants from "expo-constants";
import { useMemo, useState } from "react";
import { StyleSheet, View, TouchableOpacity, Text, ScrollView, Animated } from "react-native";
import { Event } from "../../types";

const DEFAULT_CAMERA = {
  centerCoordinate: [19.9061, 50.0686] as [number, number],
  zoomLevel: 18,
  heading: 13,
};

const MOCK_EVENTS: Event[] = [
  {
    id: "1",
    name: "Concert in the Park",
    description: "Live music performance",
    date: "2026-04-15",
    time: "18:00",
    location: "[19.9068, 50.0686]",
    creator_id: "user1",
    created_at: "2026-04-11T10:00:00Z",
    updated_at: "2026-04-11T10:00:00Z",
  },
  {
    id: "2",
    name: "Street Art Exhibition",
    description: "Local art showcase",
    date: "2026-04-16",
    time: "14:00",
    location: "[19.9057, 50.0689]",
    creator_id: "user2",
    created_at: "2026-04-11T10:00:00Z",
    updated_at: "2026-04-11T10:00:00Z",
  },
  {
    id: "3",
    name: "Food Festival",
    description: "Local food vendors and cooking competitions",
    date: "2026-04-17",
    time: "12:00",
    location: "[19.9061, 50.0691]",
    creator_id: "user3",
    created_at: "2026-04-11T10:00:00Z",
    updated_at: "2026-04-11T10:00:00Z",
  },
  {
    id: "4",
    name: "Book Club Meeting",
    description: "Monthly book discussion",
    date: "2026-04-18",
    time: "16:00",
    location: "[19.9058, 50.0688]",
    creator_id: "user4",
    created_at: "2026-04-11T10:00:00Z",
    updated_at: "2026-04-11T10:00:00Z",
  },
  {
    id: "5",
    name: "Running Club",
    description: "5K run through the city",
    date: "2026-04-19",
    time: "07:00",
    location: "[19.9054, 50.0686]",
    creator_id: "user5",
    created_at: "2026-04-11T10:00:00Z",
    updated_at: "2026-04-11T10:00:00Z",
  },
  {
    id: "6",
    name: "Yoga Sessions",
    description: "Morning yoga in the city center",
    date: "2026-04-20",
    time: "08:00",
    location: "[19.9063, 50.0682]",
    creator_id: "user6",
    created_at: "2026-04-11T10:00:00Z",
    updated_at: "2026-04-11T10:00:00Z",
  },
  {
    id: "7",
    name: "Photography Walk",
    description: "Guided photo tour of historic sites",
    date: "2026-04-21",
    time: "10:00",
    location: "[19.9061, 50.0681]",
    creator_id: "user7",
    created_at: "2026-04-11T10:00:00Z",
    updated_at: "2026-04-11T10:00:00Z",
  },
  {
    id: "8",
    name: "Jazz Night",
    description: "Live jazz music performance",
    date: "2026-04-22",
    time: "20:00",
    location: "[19.9062, 50.0689]",
    creator_id: "user8",
    created_at: "2026-04-11T10:00:00Z",
    updated_at: "2026-04-11T10:00:00Z",
  },
  {
    id: "9",
    name: "Craft Fair",
    description: "Local artisans and handmade goods",
    date: "2026-04-23",
    time: "09:00",
    location: "[19.9065, 50.0683]",
    creator_id: "user9",
    created_at: "2026-04-11T10:00:00Z",
    updated_at: "2026-04-11T10:00:00Z",
  },
  {
    id: "10",
    name: "Networking Brunch",
    description: "Business networking event",
    date: "2026-04-24",
    time: "11:00",
    location: "[19.9059, 50.0683]",
    creator_id: "user10",
    created_at: "2026-04-11T10:00:00Z",
    updated_at: "2026-04-11T10:00:00Z",
  },
];

export default function MapScreen() {
  const [cameraPosition, setCameraPosition] = useState(DEFAULT_CAMERA);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [showEventsList, setShowEventsList] = useState(true);
  const MAPTILER_KEY = Constants.expoConfig?.extra?.MAPTILER_KEY || "";

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
      features: MOCK_EVENTS.filter((event) => event.location).map((event) => ({
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
    []
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
                circleColor: "#007AFF"
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
            <ScrollView style={styles.eventsListContent}>
              {MOCK_EVENTS.map((event) => (
                <TouchableOpacity
                  key={event.id}
                  style={[
                    styles.eventListItem,
                    selectedEventId === event.id && styles.eventListItemSelected,
                  ]}
                  onPress={() => handleEventSelect(event)}
                >
                  <Text
                    style={[
                      styles.eventListItemName,
                      selectedEventId === event.id && styles.eventListItemNameSelected,
                    ]}
                  >
                    {event.name}
                  </Text>
                  <Text style={styles.eventListItemTime}>
                    {event.date} {event.time}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
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
    borderRadius: 8,
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
});
