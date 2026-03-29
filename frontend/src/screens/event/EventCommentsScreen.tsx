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
  Image,
} from "react-native";
import { useNavigation, useRoute } from "@react-navigation/native";
import { tokenStorage } from "../../utils/storage";
import { getComments, createComment, replyToComment } from "../../services/comments";
import { Comment } from "../../types/comment";
import CommentCard from "../../components/CommentCard";
import { TextInput } from "react-native-gesture-handler";
import { THEME } from "../../utils/constants";

const BASE_TILE_SIZE = 30;
const FILTER_ICON_SIZE = 30;
const FILTER_SPRITE_WIDTH = 90;
const FILTER_SPRITE_HEIGHT = 90;
const FILTER_SPRITE_SCALE = FILTER_ICON_SIZE / BASE_TILE_SIZE;
const FILTER_ICON_OFFSET = { x: -BASE_TILE_SIZE, y: 0 };
const SEND_ICON_SIZE = 28;
const SEND_SPRITE_WIDTH = 90;
const SEND_SPRITE_HEIGHT = 90;
const SEND_SPRITE_SCALE = SEND_ICON_SIZE / BASE_TILE_SIZE;
const SEND_ICON_OFFSET = { x: -BASE_TILE_SIZE * 2, y: 0 };

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
      headerRight: () => (
        <TouchableOpacity
          onPress={() => navigation.navigate("CommentFilters", { event })}
          style={styles.headerFilterButton}
          activeOpacity={0.8}
        >
          <View style={styles.headerFilterIconContainer}>
            <Image
              source={require("../../../assets/iconset1.jpg")}
              style={styles.headerFilterIconImage}
              resizeMode="cover"
            />
          </View>
        </TouchableOpacity>
      ),
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
    <View style={styles.screen}>
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
          <View style={styles.replyIndicatorContent}>
            <View style={styles.replyIndicatorLine} />
            <View style={styles.replyTextContainer}>
              <Text style={styles.replyText}>Odpowiadasz: {replyTo.username || "użytkownik"}</Text>
              <Text style={styles.replyPreviewText} numberOfLines={1}>
                {replyTo.content}
              </Text>
            </View>
          </View>
          <TouchableOpacity
            onPress={() => {
              setReplyTo(null);
              setCommentValue("");
            }}
          >
            <Text style={styles.cancelReplyText}>Anuluj</Text>
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
          <View style={styles.sendIconContainer}>
            <Image
              source={require("../../../assets/iconset2.jpg")}
              style={styles.sendIconImage}
              resizeMode="cover"
            />
          </View>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: THEME.colors.lm_bg,
  },
  headerContainer: {
    alignItems: "center",
    paddingTop: 12,
    paddingBottom: 4,
  },
  headerTitle: {
    fontSize: 16,
    marginVertical: 10,
    fontWeight: "bold",
    color: THEME.colors.lm_txt,
  },
  emptyState: {
    fontSize: 14,
    color: THEME.colors.lm_ico,
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
    backgroundColor: THEME.colors.lm_bg,
    borderTopWidth: 1,
    borderColor: THEME.colors.lm_src_br,
  },
  commentInput: {
    flex: 1,
    backgroundColor: THEME.colors.lm_src_br,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
    fontSize: 14,
    maxHeight: 100,
  },
  sendButton: {
    marginLeft: 10,
    width: 40,
    height: 40,
    alignItems: "center",
    justifyContent: "center",
  },
  sendIconContainer: {
    width: SEND_ICON_SIZE,
    height: SEND_ICON_SIZE,
    overflow: "hidden",
  },
  sendIconImage: {
    width: SEND_SPRITE_WIDTH * SEND_SPRITE_SCALE,
    height: SEND_SPRITE_HEIGHT * SEND_SPRITE_SCALE,
    transform: [
      { translateX: SEND_ICON_OFFSET.x * SEND_SPRITE_SCALE },
      { translateY: SEND_ICON_OFFSET.y * SEND_SPRITE_SCALE },
    ],
  },
  replyBanner: {
    position: "absolute",
    bottom: 60,
    left: 0,
    right: 0,
    backgroundColor: THEME.colors.lm_src_br,
    paddingHorizontal: 12,
    paddingVertical: 8,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    borderTopWidth: 1,
    borderColor: THEME.colors.lm_src_br,
  },
  replyIndicatorContent: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
    marginRight: 8,
  },
  replyIndicatorLine: {
    width: 5,
    height: 40,
    borderRadius: 2,
    backgroundColor: THEME.colors.lm_highlight,
    marginRight: 8,
  },
  replyTextContainer: {
    flex: 1,
  },
  replyText: {
    fontSize: 12,
    color: THEME.colors.lm_ico,
  },
  cancelReplyText: {
    fontSize: 13,
    fontWeight: "600",
    color: THEME.colors.agh_red,
  },
  replyPreviewText: {
    ...THEME.typography.text,
    color: THEME.colors.lm_txt,
    fontSize: 13,
  },
  headerFilterButton: {
    marginRight: 12,
  },
  headerFilterIconContainer: {
    width: FILTER_ICON_SIZE,
    height: FILTER_ICON_SIZE,
    overflow: "hidden",
  },
  headerFilterIconImage: {
    width: FILTER_SPRITE_WIDTH * FILTER_SPRITE_SCALE,
    height: FILTER_SPRITE_HEIGHT * FILTER_SPRITE_SCALE,
    transform: [
      { translateX: FILTER_ICON_OFFSET.x * FILTER_SPRITE_SCALE },
      { translateY: FILTER_ICON_OFFSET.y * FILTER_SPRITE_SCALE },
    ],
  },
});

export default EventCommentsScreen;
