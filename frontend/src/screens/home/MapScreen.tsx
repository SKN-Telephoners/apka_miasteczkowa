import {
  Camera,
  MapView,
} from "@maplibre/maplibre-react-native";
import Constants from "expo-constants";
import { useMemo } from "react";
import { StyleSheet, View } from "react-native";

export default function MapScreen() {
  const MAPTILER_KEY = Constants.expoConfig?.extra?.MAPTILER_KEY || "";

  const mapStyle = useMemo(
    () =>
      `https://api.maptiler.com/maps/streets-v4/style.json?key=${MAPTILER_KEY}`,
    [MAPTILER_KEY],
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
            zoomLevel={17}
            centerCoordinate={[19.906, 50.0685]}
            animationMode="flyTo"
            animationDuration={1500}
          />
        </MapView>
      </View>    
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", alignItems: "center" },
  mapcontainer: { width: "100%", height: "100%" },
  map: { flex: 1 },
});
