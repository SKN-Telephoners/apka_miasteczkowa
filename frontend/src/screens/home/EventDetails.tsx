import React from "react";
import { View, Text } from "react-native";
import { useRoute } from "@react-navigation/native";


const EventDetails = () => {
  const route = useRoute<any>();

  const { event } = route.params;

  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
      <Text style={{ fontSize: 28, fontWeight: "bold" }}>{event.name}</Text>
      <Text style={{ fontSize: 18, marginVertical: 10 }}>Lokalizacja: {event.location}</Text>
      <Text style={{ fontSize: 18, marginVertical: 10 }}>Data: {event.date}</Text>
      <Text style={{ fontSize: 18, marginVertical: 10 }}>Godzina: {event.time}</Text>
      <Text style={{ fontSize: 16, marginVertical: 10 }}>{event.description}</Text>
    </View>
  );
};

export default EventDetails;
