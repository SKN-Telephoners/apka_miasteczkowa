import React, { useEffect, useRef, useState } from "react";
import {
  View,
  Text,
  Alert,
  FlatList,
  StyleSheet,
  Keyboard,
  TouchableWithoutFeedback,
  TouchableOpacity,
} from "react-native";
import { useNavigation, useRoute } from "@react-navigation/native";
import { tokenStorage } from "../../utils/storage";
import { getComments, createComment, replyToComment } from "../../services/comments";
import { Comment } from "../../types/comment";
import CommentCard from "../../components/CommentCard";
import { Ionicons } from "@expo/vector-icons";
import { TextInput } from "react-native-gesture-handler";

const EventCommentsScreen = () => {
  const route = useRoute<any>();
  const navigation = useNavigation<any>();
  const { event } = route.params;

  const [userID, setUserID] = useState("");
  const [commentCount, setCommentCount] = useState<number>(Number(event?.comment_count ?? 0));
  const [comments, setComments] = useState<Comment[]>([]);
  const [commentValue, setCommentValue] = useState("");
  const [replyTo, setReplyTo] = useState<Comment | null>(null);
  const inputRef = useRef<TextInput>(null);

  useEffect(() => {
    const fetchUserID = async () => {
      const id = await tokenStorage.getUserId();
      setUserID(id);
    };

    fetchUserID();
  }, []);

  useEffect(() => {
    navigation.setOptions({
      title: event?.name || "Komentarze",
    });
  }, [navigation, event?.name]);

  const refreshComments = async () => {
    const data = await getComments(event.id);
    setComments(data.comments);
    if (typeof data.comment_count === "number") {
      setCommentCount(data.comment_count);
    }
  };

  useEffect(() => {
    refreshComments();
  }, [event.id]);

  const handleCommentDeleted = async () => {
    setCommentCount((prev) => Math.max(prev - 1, 0));
    await refreshComments();
  };

  const handleAddComment = async () => {
    if (!commentValue.trim()) {
      Alert.alert("Komentarz nie może być pusty");
      return;
    }

    try {
      if (replyTo) {
        await replyToComment(replyTo.comment_id, event.id, commentValue);
      } else {
        await createComment(event.id, commentValue);
      }

      setCommentCount((prev) => prev + 1);
      setCommentValue("");
      setReplyTo(null);
      await refreshComments();
    } catch (err: any) {
      Alert.alert("Błąd", err.message);
    }
  };

  useEffect(() => {
    const sub = Keyboard.addListener("keyboardDidHide", () => {
      setReplyTo(null);
    });

    return () => sub.remove();
  }, []);

  return (
    <View style={{ flex: 1 }}>
      <TouchableWithoutFeedback onPress={Keyboard.dismiss} accessible={false}>
        <FlatList
          data={comments}
          keyExtractor={(item: Comment) => item.comment_id}
          renderItem={({ item }) => (
            <CommentCard
              item={item}
              userID={userID}
              onDeleted={handleCommentDeleted}
              onReply={(comment) => {
                setReplyTo(comment);
                inputRef.current?.focus();
              }}
            />
          )}
          removeClippedSubviews
          keyboardShouldPersistTaps="handled"
          contentContainerStyle={{ paddingBottom: 90 }}
          ListHeaderComponent={
            <View style={styles.headerContainer}>
              <Text style={styles.headerTitle}>Komentarze ({commentCount})</Text>
              {comments.length === 0 && (
                <Text style={styles.emptyState}>Brak komentarzy</Text>
              )}
            </View>
          }
        />
      </TouchableWithoutFeedback>

      {replyTo && (
        <View style={styles.replyBanner}>
          <Text style={styles.replyText}>Odpowiadasz na komentarz</Text>
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
          placeholder={replyTo ? "Odpowiedz" : "Skomentuj"}
          value={commentValue}
          style={styles.commentInput}
          onChangeText={setCommentValue}
          multiline
        />

        <TouchableOpacity onPress={handleAddComment} style={styles.sendButton}>
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
  headerContainer: {
    alignItems: "center",
    paddingTop: 12,
    paddingBottom: 4,
  },
  headerTitle: {
    fontSize: 16,
    marginVertical: 10,
    fontWeight: "bold",
  },
  emptyState: {
    fontSize: 14,
    color: "#919191ff",
    textAlign: "center",
    marginBottom: 20,
  },
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
});

export default EventCommentsScreen;
