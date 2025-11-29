import React from "react";
import { View, Text, TouchableOpacity, Alert } from "react-native";
import { useRoute } from "@react-navigation/native";
import { tokenStorage } from "../../utils/storage";
import { useState, useEffect } from "react";
import { deleteEvent } from "../../services/events";
import { useNavigation } from "@react-navigation/native";


const EventDetails = () => {
  const route = useRoute<any>();

  const { event } = route.params;

  const [userID, setUserID] = useState(null);
  const [isOwner, setIsOwner] = useState(false);

  const navigation = useNavigation<any>();

  useEffect(() => {
    const fetchUserID = async () => {
      const id = await tokenStorage.getUserId();
      setUserID(id);
    };

    fetchUserID();
  }, []);

  useEffect(() => {
    if (userID && event.creator_id === userID) {
      setIsOwner(true);
    } else {
      setIsOwner(false);
    }
  }, [userID, event.creator_id]);

  const deleteGoBack = async () => {
    try {
      await deleteEvent(event.id);
    } catch (error: any) {
      Alert.alert(
        "Błąd usuwania wydarzenia",
        "Wystąpił nieoczekiwany błąd. Spróbuj ponownie."
      );
    } finally {
      navigation.goBack();
    }
  }

  const createTwoButtonAlert = () =>
    Alert.alert('Usunąć wydarzenie?', 'Wydarzenie zostanie usunięte', [
      {
        text: 'Usuń',
        onPress: () => deleteGoBack(),
        style: 'cancel',
      },
      { text: 'Anuluj' },
    ]);

  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
      <Text style={{ fontSize: 28, fontWeight: "bold" }}>{event.name}</Text>
      <Text style={{ fontSize: 18, marginVertical: 10 }}>Lokalizacja: {event.location}</Text>
      <Text style={{ fontSize: 18, marginVertical: 10 }}>Data: {event.date}</Text>
      <Text style={{ fontSize: 18, marginVertical: 10 }}>Godzina: {event.time}</Text>
      <Text style={{ fontSize: 16, marginVertical: 10 }}>{event.description}</Text>
      {isOwner && (<View style={{ flexDirection: "row", marginVertical: 10 }}>
        <View style={{ marginHorizontal: 10 }}>
          <TouchableOpacity style={{ backgroundColor: '#045ddaff', paddingVertical: 10, borderRadius: 25, paddingHorizontal: 20 }}>
            <Text style={{ color: '#ffffff' }}>Edytuj wydarzenie</Text>
          </TouchableOpacity>
        </View>
        <View style={{ marginHorizontal: 10 }}>
          <TouchableOpacity onPress={() => createTwoButtonAlert()} style={{ backgroundColor: '#d71010ff', paddingVertical: 10, borderRadius: 25, paddingHorizontal: 20 }}>
            <Text style={{ color: '#ffffff' }}>Usuń wydarzenie</Text>
          </TouchableOpacity>
        </View>
      </View>)}
    </View>
  );
};

export default EventDetails;
