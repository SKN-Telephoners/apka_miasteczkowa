import React from "react";
import { StyleSheet, View } from "react-native";
import { MapView, Camera, setAccessToken } from "@maplibre/maplibre-react-native";

setAccessToken(null);

export default function MapScreen() {
  return (
    <View style={styles.page}>
      <MapView
        style={styles.map}
        // Use the vector style. Note: "streets" (no version) is safest.
        styleURL="https://api.maptiler.com/maps/streets/style.json?key=6TeNoAO6gd5SoLzdLgGf"
        logoEnabled={false}
      >
        <Camera
          zoomLevel={14}
          centerCoordinate={[19.9449, 50.0647]}
          animationMode="flyTo"
          animationDuration={2000}
        />
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1 },
  map: { flex: 1 },
});