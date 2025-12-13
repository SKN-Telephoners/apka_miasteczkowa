import MapLibreGL from "@maplibre/maplibre-react-native";
import React from "react";
import { StyleSheet, Text, View } from "react-native";

const MapScreen = () => {
  return (
    <View>
      <MapLibreGL.MapView
        // This styleURL defines the "Look and Feel" (e.g., Streets, Satellite, Dark Mode)
        // It points to vector data hosted by MapTiler (OSM data)
        styleURL="https://api.maptiler.com/maps/streets/style.json?key=YOUR_MAPTILER_KEY"
        // Optional: Start at a specific location
        logoEnabled={false} // Disable default logo (check attribution rules)
      >
        <MapLibreGL.Camera
          zoomLevel={14}
          centerCoordinate={[19.9449, 50.0647]} // Longitude, Latitude (Example: Kraków)
          animationMode="flyTo"
          animationDuration={2000}
        />

        {/* Example Marker */}
        <MapLibreGL.PointAnnotation
          id="marker-1"
          coordinate={[19.9449, 50.0647]}
        >
          <View style={styles.marker} />
        </MapLibreGL.PointAnnotation>
      </MapLibreGL.MapView>
    </View>
  );
};

export default MapScreen;
