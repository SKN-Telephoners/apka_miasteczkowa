import React, { useEffect, useMemo, useState } from "react";
import { Alert, SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRoute } from "@react-navigation/native";
import { useTheme } from "../../contexts/ThemeContext";
import { useFriends } from "../../contexts/FriendsContext";
import { useUser } from "../../contexts/UserContext";
import { deleteInviteToEvent, getSentInvitesForEvent, inviteToEvent } from "../../services/events";
import { Event } from "../../types";
import { THEME } from "../../utils/constants";
import InputField from "../../components/InputField";
import UserCard from "../../components/UserCard";
import Button from "../../components/Button";

type EventInviteRouteParams = {
  event?: Event;
};

const EventInviteUsersScreen = () => {
  const route = useRoute<any>();
  const { event } = (route.params || {}) as EventInviteRouteParams;

  const { colors } = useTheme();
  const { user } = useUser();
  const { friends, fetchFriends } = useFriends();
  const styles = useMemo(() => getStyles(colors), [colors]);

  const [searchQuery, setSearchQuery] = useState("");
  const [invitedFriendIds, setInvitedFriendIds] = useState<Record<string, boolean>>({});

  const isPrivateEvent =
    event?.is_private === true ||
    String(event?.is_private).toLowerCase() === "true";
  const isOwner = Boolean(user?.user_id) && event?.creator_id === user?.user_id;
  const canInvite = Boolean(event?.id) && (!isPrivateEvent || isOwner);

  useEffect(() => {
    fetchFriends();
  }, [fetchFriends]);

  useEffect(() => {
    let mounted = true;

    const loadSentInvites = async () => {
      const eventId = String(event?.id || "");
      if (!eventId) {
        return;
      }

      try {
        const invitedIds = await getSentInvitesForEvent(eventId);
        if (!mounted) {
          return;
        }

        const nextState: Record<string, boolean> = {};
        invitedIds.forEach((id) => {
          nextState[String(id)] = true;
        });
        setInvitedFriendIds(nextState);
      } catch (error) {
        console.error("Failed to load sent invites:", error);
      }
    };

    loadSentInvites();

    return () => {
      mounted = false;
    };
  }, [event?.id]);

  const filteredFriends = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return friends;
    }

    return friends.filter((friend) =>
      (friend.username || "").toLowerCase().includes(normalizedQuery)
    );
  }, [friends, searchQuery]);

  const handleInviteToggle = async (friendId: string) => {
    const eventId = String(event?.id || "");
    const isInvited = Boolean(invitedFriendIds[friendId]);

    if (!canInvite || !eventId || !friendId) {
      Alert.alert("Błąd", "Nie można wysłać zaproszenia dla tego wydarzenia.");
      return;
    }

    setInvitedFriendIds((prev) => ({ ...prev, [friendId]: !isInvited }));

    try {
      if (isInvited) {
        await deleteInviteToEvent(eventId, friendId);
      } else {
        await inviteToEvent(eventId, friendId);
      }
    } catch (error: any) {
      setInvitedFriendIds((prev) => ({ ...prev, [friendId]: isInvited }));
      Alert.alert("Błąd zaproszenia", error?.message || "Nie udało się zaktualizować zaproszenia.");
    }
  };

  if (!event?.id) {
    return (
      <SafeAreaView style={styles.screen}>
        <View style={styles.stateWrap}>
          <Text style={styles.stateText}>Brak danych wydarzenia.</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.screen}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.container}>
          <InputField
            placeholder="Szukaj znajomych..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            showSearchSpriteIcon
            showFloatingLabel={false}
            reserveErrorSpace={false}
          />

          {!canInvite ? (
            <Text style={styles.infoText}>Zaproszenia do tego prywatnego wydarzenia może wysyłać tylko właściciel.</Text>
          ) : filteredFriends.length > 0 ? (
            filteredFriends.map((friend) => {
              const friendId = String(friend?.id || "");
              const isInvited = Boolean(invitedFriendIds[friendId]);

              return (
                <View key={friend.id} style={[styles.listItem, styles.friendRow, { borderColor: colors.border }]}> 
                  <View style={styles.friendInfo}>
                    <UserCard
                      creatorDisplayName={friend.username}
                      avatarUri={friend?.profile_picture?.url || friend?.avatarUrl || (typeof friend?.profile_picture === "string" ? friend?.profile_picture : undefined)}
                      createdAtDisplay=""
                      showCreatedAt={false}
                      showMetaIcon={false}
                      showUsernameIcon={false}
                      metaPrefix={`${friend?.academy || "wydział"} • ${friend?.course || "kierunek"}`}
                      avatarSize={40}
                    />
                  </View>
                  <Button
                    title={isInvited ? "Wysłano" : "Zaproś"}
                    onPress={() => handleInviteToggle(friendId)}
                    style={styles.inviteButton}
                    textStyle={styles.inviteButtonText}
                  />
                </View>
              );
            })
          ) : searchQuery.trim().length > 0 ? (
            <Text style={styles.infoText}>Brak znajomych pasujących do wyszukiwania</Text>
          ) : (
            <Text style={styles.infoText}>Brak znajomych na liście</Text>
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const getStyles = (colors: typeof THEME.colors.light) =>
  StyleSheet.create({
    screen: {
      flex: 1,
      backgroundColor: colors.background,
    },
    scrollView: {
      flex: 1,
      backgroundColor: colors.background,
    },
    scrollContent: {
      paddingBottom: 24,
      backgroundColor: colors.background,
    },
    container: {
      paddingHorizontal: 16,
      paddingTop: 12,
      paddingBottom: 20,
      backgroundColor: colors.background,
    },
    infoText: {
      ...THEME.typography.text,
      color: colors.icon,
      fontStyle: "italic",
      textAlign: "center",
      padding: THEME.spacing.m,
    },
    listItem: {
      width: "100%",
      paddingVertical: THEME.spacing.s,
      borderBottomWidth: 1,
    },
    friendRow: {
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "space-between",
      gap: 10,
    },
    friendInfo: {
      flex: 1,
    },
    inviteButton: {
      width: "auto",
      marginVertical: 0,
      paddingHorizontal: 14,
      paddingVertical: 8,
      minHeight: 40,
    },
    inviteButtonText: {
      fontWeight: "700",
    },
    stateWrap: {
      flex: 1,
      justifyContent: "center",
      alignItems: "center",
      padding: 20,
    },
    stateText: {
      ...THEME.typography.text,
      color: colors.text,
      textAlign: "center",
    },
  });

export default EventInviteUsersScreen;
