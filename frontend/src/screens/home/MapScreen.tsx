import MapLibreRN from "@maplibre/maplibre-react-native";
import React from "react";
import { StyleSheet, Text, View } from "react-native";

const MapScreen = () => {
  return (
    <View style={styles.container}>
      <MapLibreRN.MapView
        style={styles.map}
        // This styleURL defines the "Look and Feel" (e.g., Streets, Satellite, Dark Mode)
        // It points to vector data hosted by MapTiler (OSM data)
        styleURL="https://api.maptiler.com/maps/streets/style.json?key=6TeNoAO6gd5SoLzdLgGf"
        // Optional: Start at a specific location
        logoEnabled={false} // Disable default logo (check attribution rules)
      >
        <MapLibreRN.Camera
          zoomLevel={14}
          centerCoordinate={[19.9449, 50.0647]} // Longitude, Latitude (Example: Kraków)
          animationMode="flyTo"
          animationDuration={2000}
        />

        {/* Example Marker */}
        <MapLibreRN.PointAnnotation
          id="marker-1"
          coordinate={[19.9449, 50.0647]}
        >
          <View style={styles.marker}>
            <Text style={styles.markerText}>📍</Text>
          </View>
        </MapLibreRN.PointAnnotation>
      </MapLibreRN.MapView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
  marker: {
    width: 40,
    height: 40,
    justifyContent: "center",
    alignItems: "center",
  },
  markerText: {
    fontSize: 20,
  },
});

export default MapScreen;
