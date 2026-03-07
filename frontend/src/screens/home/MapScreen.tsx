import {
  Camera,
  MapView,
  RasterLayer,
  RasterSource,
  setAccessToken,
} from "@maplibre/maplibre-react-native";
import React from "react";
import { StyleSheet, View } from "react-native";

setAccessToken(null);

const MapScreen = () => {
  return (
    <View style={styles.page}>
      {/*target implementation - vector rendering */}
      {/* <MapView
        style={styles.map}
        styleURL="https://api.maptiler.com/maps/streets/style.json?key=MAPTILER_KEY"
        logoEnabled={false}
      >
        <Camera
          zoomLevel={14}
          centerCoordinate={[19.9449, 50.0647]}
          animationMode="flyTo"
          animationDuration={2000}
        />
      </MapView> */}

      {/*OpenStreetMap Tiles via RasterSource and RasterLayer for development*/}
      <MapView style={styles.map} logoEnabled={false}>
        <Camera
          zoomLevel={14}
          centerCoordinate={[19.9449, 50.0647]}
          animationMode="moveTo"
        />

        {/* OpenStreetMap Images */}
        <RasterSource
          id="osmSource"
          tileUrlTemplates={[
            "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
          ]}
          tileSize={256}
        />

        <RasterLayer
          id="osmLayer"
          sourceID="osmSource"
          style={{ rasterOpacity: 1 }}
        />
      </MapView>
    </View>
  );
};

const styles = StyleSheet.create({
  page: { flex: 1 },
  map: { flex: 1 },
});

export default MapScreen;
