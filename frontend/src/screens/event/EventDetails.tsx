import React from "react";
import { View, Text, TouchableOpacity, Alert, FlatList } from "react-native";
import { useRoute } from "@react-navigation/native";
import { tokenStorage } from "../../utils/storage";
import { useState, useEffect } from "react";
import { deleteEvent } from "../../services/events";
import { getComments, createComment } from "../../services/comments";
import { useNavigation } from "@react-navigation/native";
import { Comment } from "../../types/comment";
import CommentCard from "../../components/CommentCard";
import InputField from "../../components/InputField";


const EventDetails = () => {
  const route = useRoute<any>();

  const { event } = route.params;

  const [userID, setUserID] = useState(null);
  const [isOwner, setIsOwner] = useState(false);
  const [comments, setComments] = useState([]);

  const [commentValue, setCommentValue] = useState("");

  const navigation = useNavigation<any>();

  useEffect(() => {
    const fetchUserID = async () => {
      const id = await tokenStorage.getUserId();
      setUserID(id);
    };

    fetchUserID();
  }, []);

  useEffect(() => {
    const fetchComments = async () => {
      const data = await getComments(event.id);
      setComments(data.comments);
    };

    fetchComments();
  }, []);

  const handleAddComment = async () => {
    if (!commentValue) {
      Alert.alert("Komentarz nie może być pusty");
      return;
    }
    try {
      await createComment(event.id, commentValue);
      Alert.alert("Dodano komentarz");
      setCommentValue("");
      const data = await getComments(event.id);
      setComments(data.comments);
    } catch (error: any) {
      Alert.alert("Błąd dodawania komentarza", error.message);
    }
  };


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

  const validateComment = (text: string): string | null => {
    if (!text) {
      return "Komentarz nie może być pusty";
    }
    else if (text.length > 1000) {
      return "Komentarz nie może być dłuższy niż 1000 znaków";
    }

    return null;
  }


  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
      <FlatList
        data={comments}
        keyExtractor={(item: Comment) => item.comment_id}
        renderItem={({ item }) => { return (<CommentCard item={item} />); }}
        removeClippedSubviews
        ListHeaderComponent={
          <View>
            <View style={{ alignItems: "center" }}>
              <Text style={{ fontSize: 28, fontWeight: "bold", marginTop: 10 }}>{event.name}</Text>

              <Text style={{ fontSize: 18, marginVertical: 10 }}>
                Lokalizacja: {event.location}
              </Text>

              <Text style={{ fontSize: 18, marginVertical: 10 }}>
                Data: {event.date}
              </Text>

              <Text style={{ fontSize: 18, marginVertical: 10 }}>
                Godzina: {event.time}
              </Text>

              {isOwner && (<View style={{ flexDirection: "row", marginVertical: 10 }}>
                <View style={{ marginHorizontal: 10 }}>
                  <TouchableOpacity onPress={() => {
                    navigation.navigate("EditEvent", {
                      event: event
                    });
                  }} style={{ backgroundColor: '#045ddaff', paddingVertical: 10, borderRadius: 25, paddingHorizontal: 20 }}>
                    <Text style={{ color: '#ffffff' }}>Edytuj wydarzenie</Text>
                  </TouchableOpacity>
                </View>
                <View style={{ marginHorizontal: 10 }}>
                  <TouchableOpacity onPress={() => createTwoButtonAlert()} style={{ backgroundColor: '#d71010ff', paddingVertical: 10, borderRadius: 25, paddingHorizontal: 20 }}>
                    <Text style={{ color: '#ffffff' }}>Usuń wydarzenie</Text>
                  </TouchableOpacity>
                </View>
              </View>)}
              <Text style={{ fontSize: 16, marginVertical: 10, marginHorizontal: 20 }}>{event.description}</Text>
              <Text style={{ fontSize: 16, marginVertical: 10, fontWeight: "bold" }}>Komentarze</Text>
            </View>
            <View style={{ marginHorizontal: 10 }}>
              <InputField placeholder="Skomentuj"
                value={commentValue}
                onChangeText={(comment) => setCommentValue(comment)}
                validate={validateComment}></InputField>

              <TouchableOpacity onPress={handleAddComment} style={{ backgroundColor: '#045ddaff', alignItems: 'center', padding: 10, borderRadius: 25, marginBottom: 10 }} >
                <Text style={{ color: '#ffffff' }}>Dodaj komentarz</Text>
              </TouchableOpacity>
              {comments.length === 0 && (
                <Text style={{ fontSize: 14, color: '#919191ff', textAlign: 'center', marginBottom: 40 }}>Brak komentarzy</Text>
              )}
            </View>
          </View>
        }
      />

    </View>

  );
};

export default EventDetails;
