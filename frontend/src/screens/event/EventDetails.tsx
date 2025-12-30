import React from "react";
import {
  View, Text, TouchableOpacity, Alert, FlatList, StyleSheet,
  Keyboard, TouchableWithoutFeedback
} from "react-native";
import { useRoute } from "@react-navigation/native";
import { tokenStorage } from "../../utils/storage";
import { useState, useEffect, useRef } from "react";
import { deleteEvent } from "../../services/events";
import { getComments, createComment, replyToComment } from "../../services/comments";
import { useNavigation } from "@react-navigation/native";
import { Comment } from "../../types/comment";
import CommentCard from "../../components/CommentCard";
import { Ionicons } from "@expo/vector-icons";
import { TextInput } from "react-native-gesture-handler";


const EventDetails = () => {
  const route = useRoute<any>();

  const { event } = route.params;

  const [userID, setUserID] = useState('');
  const [isOwner, setIsOwner] = useState(false);
  const [comments, setComments] = useState([]);

  const [commentValue, setCommentValue] = useState("");

  const [replyTo, setReplyTo] = useState<Comment | null>(null);
  const inputRef = useRef<TextInput>(null);


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

  const refreshComments = async () => {
    const data = await getComments(event.id);
    setComments(data.comments);
  };

  const handleAddComment = async () => {
    if (!commentValue.trim()) {
      Alert.alert("Komentarz nie może być pusty");
      return;
    }

    try {
      if (replyTo) {
        await replyToComment(replyTo.comment_id, commentValue);
      } else {
        await createComment(event.id, commentValue);
      }

      setCommentValue("");
      setReplyTo(null);
      refreshComments();
    } catch (err: any) {
      Alert.alert("Błąd", err.message);
    }
  }

  useEffect(() => {
    const sub = Keyboard.addListener("keyboardDidHide", () => {
      setReplyTo(null);
    });

    return () => sub.remove();
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
      <TouchableWithoutFeedback onPress={Keyboard.dismiss} accessible={false}>
        <FlatList
          data={comments}
          keyExtractor={(item: Comment) => item.comment_id}
          renderItem={({ item }) => {
            return (
              <CommentCard
                item={item}
                userID={userID}
                onDeleted={refreshComments}
                onReply={(comment) => {
                  setReplyTo(comment);
                  inputRef.current?.focus();
                }}
              />);
          }}
          removeClippedSubviews
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{ paddingBottom: 90 }}
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
                {comments.length === 0 && (
                  <Text style={{ fontSize: 14, color: '#919191ff', textAlign: 'center', marginBottom: 40 }}>Brak komentarzy</Text>
                )}
              </View>

            </View>
          }
        />
      </TouchableWithoutFeedback>

      {replyTo && (
        <View style={styles.replyBanner}>
          <Text style={styles.replyText}>
            Odpowiadasz na komentarz
          </Text>

          <TouchableOpacity
            onPress={() => {
              setReplyTo(null);
              setCommentValue("");
            }}
          >
            <Ionicons name="close" size={18} color="#d71010ff" />
          </TouchableOpacity>
        </View>
      )}



      <View style={styles.commentBar}>

        <TextInput
          ref={inputRef}
          placeholder={
            replyTo
              ? "Odpowiedz"
              : "Skomentuj"
          }
          value={commentValue}
          style={styles.commentInput}
          onChangeText={setCommentValue}
          multiline
        />


        <TouchableOpacity
          onPress={handleAddComment}
          style={styles.sendButton}
        >
          <Ionicons
            name={replyTo ? "return-up-forward" : "add"}
            size={20}
            color="#fff"
          />
        </TouchableOpacity>


      </View>

    </View>

  );
};

const styles = StyleSheet.create({
  commentBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 12,
    paddingVertical: 10,
    backgroundColor: "#fff",
    borderTopWidth: 1,
    borderColor: "#eee",
  },

  commentInput: {
    flex: 1,
    backgroundColor: "#f2f2f2",
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
    fontSize: 14,
    maxHeight: 100,
  },

  sendButton: {
    marginLeft: 10,
    backgroundColor: "#045ddaff",
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },

  replyBanner: {
    position: "absolute",
    bottom: 60,
    left: 0,
    right: 0,
    backgroundColor: "#f2f2f2",
    paddingHorizontal: 12,
    paddingVertical: 8,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    borderTopWidth: 1,
    borderColor: "#ddd",
  },

  replyText: {
    fontSize: 12,
    color: "#59595aff",
  },


})

export default EventDetails;
