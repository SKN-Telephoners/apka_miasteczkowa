import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  View,
  Text,
  Alert,
  FlatList,
  RefreshControl,
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
import { TextInput } from "react-native-gesture-handler";
import { THEME } from "../../utils/constants";
import SvgSpriteIcon from "../../components/SvgSpriteIcon";
import { useTheme } from "../../contexts/ThemeContext";

const BASE_TILE_SIZE = 30;
const FILTER_ICON_SIZE = 30;
const FILTER_ICON_OFFSET = { x: -BASE_TILE_SIZE, y: 0 };
const SEND_ICON_SIZE = 28;
const SEND_ICON_OFFSET = { x: -BASE_TILE_SIZE * 2, y: 0 };

const EventCommentsScreen = () => {
  const route = useRoute<any>();
  const navigation = useNavigation<any>();
  const { event } = route.params;
  const { colors } = useTheme();
  const styles = useMemo(() => getStyles(colors), [colors]);

  const [userID, setUserID] = useState("");
  const [commentCount, setCommentCount] = useState<number>(Number(event?.comment_count ?? 0));
  const [comments, setComments] = useState<Comment[]>([]);
  const [commentValue, setCommentValue] = useState("");
  const [replyTo, setReplyTo] = useState<Comment | null>(null);
  const [refreshing, setRefreshing] = useState(false);
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
            <SvgSpriteIcon set={1} size={FILTER_ICON_SIZE} offsetX={FILTER_ICON_OFFSET.x} offsetY={FILTER_ICON_OFFSET.y} />
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

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refreshComments();
    } finally {
      setRefreshing(false);
    }
  }, [event.id]);

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
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={handleRefresh}
              tintColor={colors.transparentHighlight}
            />
          }
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
          placeholderTextColor={colors.text}
          multiline
        />

        <TouchableOpacity onPress={handleAddComment} style={styles.sendButton}>
          <View style={styles.sendIconContainer}>
            <SvgSpriteIcon set={2} size={SEND_ICON_SIZE} offsetX={SEND_ICON_OFFSET.x} offsetY={SEND_ICON_OFFSET.y} />
          </View>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const getStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: colors.background,
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
    color: colors.text,
  },
  emptyState: {
    fontSize: 14,
    color: colors.icon,
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
    backgroundColor: colors.background,
    borderTopWidth: 1,
    borderColor: colors.border,
  },
  commentInput: {
    flex: 1,
    backgroundColor: colors.background,
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
    fontSize: 14,
    maxHeight: 100,
    color: colors.text,
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
  },
  replyBanner: {
    position: "absolute",
    bottom: 60,
    left: 0,
    right: 0,
    backgroundColor: colors.background,
    paddingHorizontal: 12,
    paddingVertical: 8,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    borderTopWidth: 1,
    borderColor: colors.border,
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
    backgroundColor: colors.transparentHighlight,
    marginRight: 8,
  },
  replyTextContainer: {
    flex: 1,
  },
  replyText: {
    fontSize: 12,
    color: colors.icon,
  },
  cancelReplyText: {
    fontSize: 13,
    fontWeight: "600",
    color: colors.aghRed,
  },
  replyPreviewText: {
    ...THEME.typography.text,
    color: colors.text,
    fontSize: 13,
  },
  headerFilterButton: {
    marginRight: 12,
  },
  headerFilterIconContainer: {
    width: FILTER_ICON_SIZE,
    height: FILTER_ICON_SIZE,
  },
});

export default EventCommentsScreen;
