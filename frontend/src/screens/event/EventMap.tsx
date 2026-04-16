import {
  Camera,
  MapView,
  MarkerView,
  UserLocation,
} from "@maplibre/maplibre-react-native";
import { CommonActions, useNavigation, useRoute } from "@react-navigation/native";
import Constants from "expo-constants";
import React, { useRef, useState } from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";

interface SelectedLocation {
  coordinates: [number, number];
  address?: string;
  timestamp: number;
}

const DEFAULT_CAMERA = {
  centerCoordinate: [19.9061, 50.0686] as [number, number],
  zoomLevel: 17.5,
  heading: 13,
};

export default function EventMap() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const mapRef = useRef<any>(null);
  const cameraRef = useRef<any>(null);

  const [cameraPosition, setCameraPosition] = useState(DEFAULT_CAMERA);
  const [selectedLocation, setSelectedLocation] =
    useState<SelectedLocation | null>(null);

  const MAPTILER_KEY = Constants.expoConfig?.extra?.MAPTILER_KEY || "";

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
    if (!selectedLocation) {
      return;
    }

    const selectedLocationPayload = {
      coordinates: selectedLocation.coordinates,
      lat: selectedLocation.coordinates[1],
      lng: selectedLocation.coordinates[0],
      timestamp: selectedLocation.timestamp,
    };

    const sourceRouteKey = route.params?.sourceRouteKey as string | undefined;
    if (sourceRouteKey) {
      navigation.dispatch({
        ...CommonActions.setParams({ selectedLocation: selectedLocationPayload }),
        source: sourceRouteKey,
      });
      navigation.goBack();
      return;
    }

    const returnTo = route.params?.returnTo || "AddEvent";
    navigation.navigate(returnTo, {
      selectedLocation: selectedLocationPayload,
    });
  };

  return (
    <View style={styles.container}>
      <View style={styles.mapContainer}>
        <MapView
          ref={mapRef}
          style={styles.map}
          mapStyle={mapStyle}
          logoEnabled={false}
          attributionPosition={{ bottom: 8, right: 8 }}
          onPress={handleMapPress}
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

          <UserLocation animated visible showsUserHeadingIndicator />

          {/* location marker */}
          {selectedLocation && (
            <MarkerView coordinate={selectedLocation.coordinates}>
              <View style={styles.markerContainer}>
                <Text style={styles.markerText}>{"📍\n"}</Text>
              </View>
            </MarkerView>
          )}
        </MapView>

        {selectedLocation && (
          <View style={styles.actionButtons}>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={() => {
                setSelectedLocation(null);
              }}
            >
              <Text style={styles.cancelButtonText}>Anuluj</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.confirmButton]}
              onPress={handleUseLocation}
              activeOpacity={0.7}
            >
              <Text style={styles.confirmButtonText}>Użyj lokalizacji</Text>
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
    backgroundColor: "#CF6F02",
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
  loadingContainer: {
    justifyContent: "center",
    alignItems: "center",
    paddingVertical: 40,
  },
});
