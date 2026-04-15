import {
  Camera,
  MapView,
  MarkerView,
  UserLocation,
} from "@maplibre/maplibre-react-native";
import { useNavigation, useRoute } from "@react-navigation/native";
import Constants from "expo-constants";
import React, { useEffect, useMemo, useState } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import {
  DEFAULT_LOCATION_COORDINATES,
  formatLocationCoordinates,
  normalizeLocationCoordinates,
  type LocationCoordinates,
} from "../../utils/locationCoordinates";
import { THEME } from "../../utils/constants";
import { getEvents } from "../../services/events";
import { Event } from "../../types";

interface SelectedLocation {
  coordinates: LocationCoordinates;
  address?: string;
  timestamp: number;
}

interface EventDot {
  id: string;
  coordinates: LocationCoordinates;
  event: Event;
}

const DEFAULT_CAMERA = {
  centerCoordinate: DEFAULT_LOCATION_COORDINATES,
  zoomLevel: 17.5,
  heading: 13,
};

export default function EventMap() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const isPickerMode = Boolean(route?.params?.pickLocation);
  const returnToScreen = route?.params?.returnTo as string | undefined;
  const returnParams = route?.params?.returnParams as Record<string, unknown> | undefined;
  const initialCoordinates = useMemo(
    () => normalizeLocationCoordinates(route?.params?.initialCoordinates),
    [route?.params?.initialCoordinates],
  );

  const [cameraPosition, setCameraPosition] = useState(
    initialCoordinates
      ? { ...DEFAULT_CAMERA, centerCoordinate: initialCoordinates }
      : DEFAULT_CAMERA,
  );
  const [selectedLocation, setSelectedLocation] = useState<SelectedLocation | null>(
    initialCoordinates
      ? {
          coordinates: initialCoordinates,
          timestamp: Date.now(),
        }
      : null,
  );
  const [eventDots, setEventDots] = useState<EventDot[]>([]);

  const retryDelay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

  const getEventsPageWithRetry = async (page: number, limit = 20, attempts = 2) => {
    let lastError: unknown = null;

    for (let attempt = 1; attempt <= attempts; attempt += 1) {
      try {
        return await getEvents(page, limit);
      } catch (error) {
        lastError = error;
        if (attempt < attempts) {
          await retryDelay(300 * attempt);
        }
      }
    }

    throw lastError;
  };

  const parseEventDateTime = (event: Event): Date | null => {
    if (!event?.date || !event?.time) {
      return null;
    }

    const [day, month, year] = event.date.split(".").map(Number);
    const [hours, minutes] = event.time.split(":").map(Number);

    if ([day, month, year, hours, minutes].some(Number.isNaN)) {
      return null;
    }

    return new Date(year, month - 1, day, hours, minutes, 0, 0);
  };

  useEffect(() => {
    if (!initialCoordinates) {
      return;
    }

    setCameraPosition((prev) => ({
      ...prev,
      centerCoordinate: initialCoordinates,
    }));
    setSelectedLocation({
      coordinates: initialCoordinates,
      timestamp: Date.now(),
    });
  }, [initialCoordinates]);

  const MAPTILER_KEY = Constants.expoConfig?.extra?.MAPTILER_KEY || "";

  useEffect(() => {
    if (isPickerMode) {
      return;
    }

    let isMounted = true;

    const loadFutureEventDots = async () => {
      try {
        const firstPage = await getEventsPageWithRetry(1, 20, 3);
        const allEvents: Event[] = [...(firstPage.data || [])];
        const totalPages = Number(firstPage?.pagination?.pages || 1);
        const pageLimit = Number(firstPage?.pagination?.limit || 20);

        if (totalPages > 1) {
          for (let page = 2; page <= totalPages; page += 1) {
            try {
              const response = await getEventsPageWithRetry(page, pageLimit, 2);
              allEvents.push(...(response.data || []));
            } catch (pageError) {
              console.warn(`Failed to load map events page ${page}:`, pageError);
            }
          }
        }

        const now = new Date();
        const dots = allEvents
          .filter((event) => {
            const eventDateTime = parseEventDateTime(event);
            return Boolean(eventDateTime && eventDateTime > now);
          })
          .map((event) => {
            const coordinates = normalizeLocationCoordinates(event.location);
            if (!coordinates) {
              return null;
            }

            return {
              id: String(event.id),
              coordinates,
              event,
            };
          })
          .filter((dot): dot is EventDot => Boolean(dot));

        if (isMounted) {
          setEventDots(dots);
        }
      } catch (error) {
        if (isMounted) {
          setEventDots([]);
        }
        const message = error instanceof Error ? error.message : String(error);
        if (message.toLowerCase().includes("session expired")) {
          console.warn("Map dots skipped: session expired while loading events");
        } else {
          console.error("Failed to load map event dots:", error);
        }
      }
    };

    loadFutureEventDots();

    return () => {
      isMounted = false;
    };
  }, [isPickerMode]);

  const mapStyle = React.useMemo(
    () =>
      `https://api.maptiler.com/maps/streets-v4/style.json?key=${MAPTILER_KEY}`,
    [MAPTILER_KEY],
  );

  // map tap to select location
  const handleMapPress = async (e: any) => {
    try {
      const { geometry } = e;
      const coordinates: [number, number] = [
        geometry.coordinates[0],
        geometry.coordinates[1],
      ];

      setSelectedLocation({
        coordinates,
        timestamp: Date.now(),
      });

      const [lng, lat] = coordinates;
      console.log(lng, lat);

    } catch (error) {
      console.error("Error selecting location:", error);
    }
  };

  // use selected location
  const handleUseLocation = () => {
    if (!isPickerMode || !selectedLocation || !returnToScreen) {
      return;
    }

    navigation.navigate({
      name: returnToScreen,
      params: {
        ...(returnParams || {}),
        locationCoordinates: selectedLocation.coordinates,
      },
      merge: true,
    } as any);
  };

  const openEventPreview = (event: Event, locationCoordinates: LocationCoordinates) => {
    navigation.navigate("SingleEventPreview", {
      event,
      screenTitle: "Podgląd wydarzenia",
      allowEdit: false,
      fromMap: true,
      locationCoordinates,
    });
  };

  return (
    <View style={styles.container}>
      <View style={styles.mapContainer}>
        <MapView
          style={styles.map}
          mapStyle={mapStyle}
          logoEnabled={false}
          attributionPosition={{ bottom: 8, right: 8 }}
          onPress={isPickerMode ? handleMapPress : undefined}
        >
          <Camera
            zoomLevel={cameraPosition.zoomLevel}
            centerCoordinate={cameraPosition.centerCoordinate}
            animationMode="flyTo"
            animationDuration={1500}
            heading={cameraPosition.heading}
            minZoomLevel={16.5}
          />

          <UserLocation animated visible showsUserHeadingIndicator />

          {!isPickerMode && eventDots.map((dot) => (
            <MarkerView key={dot.id} coordinate={dot.coordinates}>
              <TouchableOpacity
                style={styles.eventDotPressable}
                onPress={() => openEventPreview(dot.event, dot.coordinates)}
                activeOpacity={0.8}
              >
                <View style={styles.eventDot} />
              </TouchableOpacity>
            </MarkerView>
          ))}

          {/* location marker */}
          {selectedLocation && (
            <MarkerView coordinate={selectedLocation.coordinates}>
              <View style={styles.markerContainer}>
                <Text style={styles.markerText}>{"📍\n"}</Text>
              </View>
            </MarkerView>
          )}
        </MapView>

        {isPickerMode && (
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={() => navigation.goBack()}
            >
              <Text style={styles.cancelButtonText}>Anuluj</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.confirmButton]}
              onPress={handleUseLocation}
              activeOpacity={0.7}
              disabled={!selectedLocation}
            >
              <Text style={styles.confirmButtonText}>
                {selectedLocation
                  ? "Zatwierdź"
                  : "Kliknij na mapę"}
              </Text>
            </TouchableOpacity>
          </View>
        )}
      </View>
    </View>
  );
}

// needs unified styles
const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  mapContainer: {
    flex: 1,
    position: "relative",
  },
  map: {
    flex: 1,
  },
  actionButtons: {
    position: "absolute",
    bottom: 20,
    left: 16,
    right: 16,
    flexDirection: "row",
    gap: 12,
    zIndex: 9,
  },
  button: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  cancelButton: {
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: "#e0e0e0",
  },
  cancelButtonText: {
    color: "#333",
    fontWeight: "600",
    fontSize: 14,
  },
  confirmButton: {
    backgroundColor: THEME.colors.light.transparentHighlight,
  },
  confirmButtonText: {
    color: "white",
    fontWeight: "600",
    fontSize: 14,
  },
  markerContainer: {
    alignItems: "center",
    justifyContent: "center",
  },
  markerText: {
    fontSize: 50,
  },
  eventDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: THEME.colors.light.transparentHighlight,
    borderWidth: 2,
    borderColor: THEME.colors.light.border,
  },
  eventDotPressable: {
    padding: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  loadingContainer: {
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: 40,
  },
});
