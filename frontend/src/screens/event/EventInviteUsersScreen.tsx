import React, { useEffect, useMemo, useState } from "react";
import { ToastAndroid, SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";
import { useRoute } from "@react-navigation/native";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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

const sentInvitesQueryKey = (eventId: string) => ["sent-invites", eventId] as const;

const EventInviteUsersScreen = () => {
  const route = useRoute<any>();
  const { event } = (route.params || {}) as EventInviteRouteParams;
  const eventId = String(event?.id || "");

  const { colors } = useTheme();
  const { user } = useUser();
  const { friends, fetchFriends } = useFriends();
  const queryClient = useQueryClient();
  const styles = useMemo(() => getStyles(colors), [colors]);

  const [searchQuery, setSearchQuery] = useState("");

  const isPrivateEvent =
    event?.is_private === true ||
    String(event?.is_private).toLowerCase() === "true";
  const isOwner = Boolean(user?.user_id) && event?.creator_id === user?.user_id;
  const canInvite = Boolean(event?.id) && (!isPrivateEvent || isOwner);

  useEffect(() => {
    fetchFriends();
  }, [fetchFriends]);

  const { data: invitedIds = [] } = useQuery({
    queryKey: sentInvitesQueryKey(eventId),
    queryFn: () => getSentInvitesForEvent(eventId),
    enabled: Boolean(eventId),
  });

  const invitedFriendIds = useMemo(() => new Set(invitedIds.map(String)), [invitedIds]);

  const filteredFriends = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return friends;
    }

    return friends.filter((friend) =>
      (friend.username || "").toLowerCase().includes(normalizedQuery)
    );
  }, [friends, searchQuery]);

  const toggleInviteMutation = useMutation({
    mutationFn: ({ friendId, isInvited }: { friendId: string; isInvited: boolean }) =>
      isInvited ? deleteInviteToEvent(eventId, friendId) : inviteToEvent(eventId, friendId),
    onMutate: async ({ friendId, isInvited }) => {
      await queryClient.cancelQueries({ queryKey: sentInvitesQueryKey(eventId) });
      const previous = queryClient.getQueryData<string[]>(sentInvitesQueryKey(eventId)) ?? [];
      const next = isInvited
        ? previous.filter((id) => String(id) !== friendId)
        : [...previous, friendId];
      queryClient.setQueryData(sentInvitesQueryKey(eventId), next);
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) {
        queryClient.setQueryData(sentInvitesQueryKey(eventId), context.previous);
      }
      ToastAndroid.show("Wystąpił problem. Spróbuj ponownie.", ToastAndroid.SHORT);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: sentInvitesQueryKey(eventId) });
    },
  });

  const handleInviteToggle = (friendId: string) => {
    const isInvited = invitedFriendIds.has(friendId);

    if (!canInvite || !eventId || !friendId) {
      ToastAndroid.show("Wystąpił problem. Spróbuj ponownie.", ToastAndroid.SHORT);
      return;
    }

    toggleInviteMutation.mutate({ friendId, isInvited });
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
              const isInvited = invitedFriendIds.has(friendId);

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
                      uniName={friend?.academy || undefined}
                      majorName={friend?.course || undefined}
                      yearOfStudy={friend?.year ?? undefined}
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
