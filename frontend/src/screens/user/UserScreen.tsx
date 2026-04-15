import React, { useMemo, useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image, ScrollView, Alert } from "react-native";
import { useAuth } from "../../contexts/AuthContext";
import { useUser } from "../../contexts/UserContext";
import { useFriends } from "../../contexts/FriendsContext";
import { useEvents } from "../../contexts/EventContext";
import { useTheme } from "../../contexts/ThemeContext";
import { useNavigation, useRoute, useFocusEffect } from "@react-navigation/native";
import { THEME } from "../../utils/constants";
import Button from "../../components/Button";
import CollapsibleSection from "../../components/CollapsibleSection";
import Avatar from "../../components/Avatar";
import AppIcon from "../../components/AppIcon";
import { useEffect, useCallback } from "react";
import { getPublicUserProfile } from "../../services/users";
import InputField from "../../components/InputField";
import UserCard from "../../components/UserCard";

const UserScreen = () => {
  const { userId } = useAuth();
  const { user: currentUser } = useUser();
  const { friends, sendFriendRequest, removeFriend, fetchFriends } = useFriends();
  const { events } = useEvents();
  const { colors } = useTheme();
  const navigation = useNavigation<any>();
  const route = useRoute<any>();

  // Przechwytywanie trybu
  const visitedUser = route.params?.visitedUser;
  const visitedUserId = visitedUser?.user_id || visitedUser?.id;
  const hasVisitedUser = Boolean(visitedUserId);
  const isOwnerRoute = route.name === "UserProfile";
  const isOwner = hasVisitedUser
    ? String(visitedUserId) === String(userId)
    : isOwnerRoute;
  const [visitedProfileData, setVisitedProfileData] = useState<any | null>(null);
  const profileData = isOwner ? currentUser : (visitedProfileData || visitedUser);

  const [searchQuery, setSearchQuery] = useState("");
  const [isFriend, setIsFriend] = useState(false);

  const styles = useMemo(() => getStyles(colors), [colors]);

  // Refresh friends list when this screen comes into focus
  useFocusEffect(
    useCallback(() => {
      fetchFriends();
    }, [isOwner, fetchFriends])
  );

  useEffect(() => {
    const loadVisitedUser = async () => {
      if (isOwner || !visitedUser) {
        setVisitedProfileData(null);
        return;
      }

      const targetId = visitedUser.user_id || visitedUser.id;
      if (!targetId) {
        setVisitedProfileData(visitedUser);
        return;
      }

      try {
        const fullData = await getPublicUserProfile(targetId);
        setVisitedProfileData(fullData);
      } catch {
        setVisitedProfileData(visitedUser);
      }
    };

    loadVisitedUser();
  }, [isOwner, visitedUser?.id, visitedUser?.user_id]);

  // Check if visitedUser is already a friend (runs whenever friends list updates)
  useEffect(() => {
    if (!isOwner && visitedUser) {
      const userIsFriend = friends.some(
        (friend) =>
          friend.id === visitedUser.id ||
          friend.id === visitedUser.user_id
      );
      setIsFriend(userIsFriend);
    } else {
      setIsFriend(false);
    }
  }, [visitedUser, friends, isOwner]);

  const gotoEditProfile = () => {
    navigation.navigate("EditProfile");
  };

  const gotoSettings = () => {
    navigation.navigate("SettingsScreen");
  }

  const handleAddPhoto = () => {
    console.log("Dodawanie zdjęcia...");
  };

  const goToFriendProfile = (friendData: any) => {
    navigation.push("UserProfile", { visitedUser: friendData });
  };

  const handleSearch = (text: string) => {
    setSearchQuery(text);
  };

  const filteredFriends = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();
    if (!normalizedQuery) {
      return friends;
    }

    return friends.filter((friend) =>
      (friend.username || "").toLowerCase().includes(normalizedQuery)
    );
  }, [friends, searchQuery]);

  const myCreatedEvents = useMemo(() => {
    return events.filter(e => String(e.creator_id) === String(profileData?.id || profileData?.user_id));
  }, [events, profileData]);

  const myJoinedEvents = useMemo(() => {
    // "is_participating" obejmuje też twórcę, więc odrzucamy własne:
    return events.filter(e => e.is_participating && String(e.creator_id) !== String(profileData?.id || profileData?.user_id));
  }, [events, profileData]);

  const handleSendRequest = async () => {
    try {
      if (profileData?.id || profileData?.user_id) {
        await sendFriendRequest(profileData.id || profileData.user_id);
      }
    } catch (err: any) {
      const errorMsg = err?.message || "Nie udało się wysłać zaproszenia";
      Alert.alert("Błąd", errorMsg);
    }
  }

  const handleRemoveFriend = () => {
    Alert.alert(
      "Usunąć ze znajomych",
      "Czy chcesz usunąć tego użytkownika ze znajomych?",
      [
        {
          text: "Anuluj",
          style: "cancel",
        },
        {
          text: "Usuń",
          style: "destructive",
          onPress: async () => {
            try {
              if (visitedUser?.id || visitedUser?.user_id) {
                await removeFriend(visitedUser.id || visitedUser.user_id);
              }
            } catch (err: any) {
              Alert.alert("Błąd", err?.message || "Nie udało się usunąć użytkownika ze znajomych");
            }
          },
        },
      ]
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
      <View style={styles.headerRow}>
        <Avatar uri={profileData?.profile_picture?.url || profileData?.avatarUrl || (typeof profileData?.profile_picture === "string" ? profileData?.profile_picture : undefined)} size={80} style={{ marginRight: THEME.spacing.m }} />

        <View style={styles.headerInfo}>
          <Text style={styles.userName}>{profileData?.username || profileData?.display_name || "Użytkownik"}</Text>
          {isOwner && (
            <>
              <Text style={styles.statsText}>
                Znajomi: <Text style={styles.statsNumber}>{friends.length}</Text>
              </Text>
              <Text style={styles.statsText}>
                Dołączył: <Text style={styles.statsNumber}>{profileData?.joinedDate || "Nieznana"}</Text>
              </Text>
            </>
          )}
        </View>

        {isOwner && (
          <TouchableOpacity onPress={gotoSettings} style={styles.settingsIcon}>
            <AppIcon name="Settings" size={28} color={colors.text} />
          </TouchableOpacity>
        )}
      </View>

      <Text style={styles.facultyText}>{profileData?.academy || "Brak Uczelni"}</Text>
      {profileData?.faculty && profileData?.course && (
        <Text style={styles.majorText}>
          {`${profileData.faculty} • ${profileData.course}${profileData.year ? ` • ${profileData.year} rok` : ""}`}
        </Text>
      )}

      <Text style={styles.userBio}>{profileData?.description || (isOwner ? "Brak opisu" : "")}</Text>

      {isOwner ? (
        <Button
          title="Edytuj profil"
          onPress={gotoEditProfile}
          style={styles.editButton}
        />
      ) : isFriend ? (
        <Button
          title="Usuń ze znajomych"
          onPress={handleRemoveFriend}
          style={[styles.editButton, { backgroundColor: colors.icon }]}
        />
      ) : (
        <Button
          title="Wyślij zaproszenie"
          onPress={handleSendRequest}
          style={styles.editButton}
        />
      )}

      {isOwner && (
        <>
          <CollapsibleSection title="Znajomi">
            <InputField
              placeholder="Szukaj znajomych..."
              value={searchQuery}
              onChangeText={handleSearch}
              showSearchSpriteIcon
              showFloatingLabel={false}
              reserveErrorSpace={false}
            />
            {filteredFriends.length > 0 ? (
              filteredFriends.map((friend) => (
                <TouchableOpacity key={friend.id} onPress={() => goToFriendProfile(friend)} style={[styles.listItem, { borderColor: colors.border }]}>
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
                </TouchableOpacity>
              ))
            ) : searchQuery.trim().length > 0 ? (
              <Text style={styles.infoText}>Brak znajomych pasujących do wyszukiwania</Text>
            ) : (
              <Text style={styles.infoText}>Brak znajomych na liście</Text>
            )}
          </CollapsibleSection>

          <CollapsibleSection title="Moje wydarzenia">
            {myCreatedEvents.length > 0 ? (
              myCreatedEvents.map((event) => (
                <TouchableOpacity
                  key={event.id}
                  style={[styles.listItem, { borderColor: colors.border }]}
                  activeOpacity={0.8}
                  onPress={() => navigation.navigate("MyEventPreview", { event, screenTitle: "Moje wydarzenie", allowEdit: true })}
                >
                  <View style={{ flex: 1 }}>
                    <Text style={styles.listTitle}>{event.name}</Text>
                    <Text style={styles.listSubtitle}>{event.date} o {event.time} • {event.location}</Text>
                  </View>
                </TouchableOpacity>
              ))
            ) : (
              <Text style={styles.infoText}>Nie utworzyłeś jeszcze żadnych wydarzeń</Text>
            )}
          </CollapsibleSection>

          <CollapsibleSection title="Zapisane wydarzenia">
            {myJoinedEvents.length > 0 ? (
              myJoinedEvents.map((event) => (
                <TouchableOpacity
                  key={event.id}
                  style={[styles.listItem, { borderColor: colors.border }]}
                  activeOpacity={0.8}
                  onPress={() => navigation.navigate("MyEventPreview", { event, screenTitle: "Zapisane wydarzenie", allowEdit: false })}
                >
                  <View style={{ flex: 1 }}>
                    <Text style={styles.listTitle}>{event.name}</Text>
                    <Text style={styles.listSubtitle}>{event.date} o {event.time} • {event.location}</Text>
                  </View>
                </TouchableOpacity>
              ))
            ) : (
              <Text style={styles.infoText}>Brak zapisanych wydarzeń</Text>
            )}
          </CollapsibleSection>

        </>
      )}

    </ScrollView>
  );
};

const getStyles = (colors: typeof THEME.colors.light) => StyleSheet.create({
  container: {
    flex: 1,
    padding: THEME.spacing.m,
    backgroundColor: colors.background,
  },
  headerRow: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: THEME.spacing.s,
  },
  headerInfo: {
    flex: 1,
    justifyContent: "center",
  },
  userName: {
    fontFamily: "Roboto",
    fontWeight: "700" as const,
    lineHeight: 20,
    fontSize: 20,
    color: colors.text,
  },
  statsText: {
    ...THEME.typography.text,
    color: colors.text,
  },
  statsNumber: {
    fontWeight: "bold",
  },
  settingsIcon: {
    position: "absolute",
    right: 0,
    padding: 8,
  },
  facultyText: {
    ...THEME.typography.faculty,
    fontSize: 18,
    lineHeight: 20.5,
    color: colors.text,
  },
  majorText: {
    ...THEME.typography.text,
    marginBottom: THEME.spacing.s,
    color: colors.text,
  },
  userBio: {
    ...THEME.typography.text,
    color: colors.text,
    marginBottom: THEME.spacing.m,
  },
  editButton: {
    marginBottom: THEME.spacing.l,
  },
  infoText: {
    ...THEME.typography.text,
    color: colors.icon,
    fontStyle: "italic",
    textAlign: "center",
    padding: THEME.spacing.m,
  },
  placeholderBox: {
    width: '100%',
    aspectRatio: 1,
    borderRadius: THEME.borderRadius.m,
    overflow: 'hidden',
  },
  mockPhoto: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  listItem: {
    width: "100%",
    paddingVertical: THEME.spacing.s,
    borderBottomWidth: 1,
  },
  listTitle: {
    ...THEME.typography.text,
    fontWeight: "bold",
    fontSize: 16,
    color: colors.text,
  },
  listSubtitle: {
    ...THEME.typography.text,
    fontSize: 14,
    color: colors.text,
    marginTop: 2,
  }
});

export default UserScreen;