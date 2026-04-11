import React, { useMemo, useState } from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image, ScrollView, TextInput } from "react-native";
import { useAuth } from "../../contexts/AuthContext";
import { useUser } from "../../contexts/UserContext";
import { useFriends } from "../../contexts/FriendsContext";
import { useEvents } from "../../contexts/EventContext";
import { useTheme } from "../../contexts/ThemeContext";
import { useNavigation, useRoute } from "@react-navigation/native";
import { THEME, MOCKS } from "../../utils/constants";
import Button from "../../components/Button";
import CollapsibleSection from "../../components/CollapsibleSection";
import Avatar from "../../components/Avatar";
import { Ionicons } from "@expo/vector-icons";

const UserScreen = () => {
  const { logout } = useAuth();
  const { user: currentUser } = useUser();
  const { friends, searchUsers, sendFriendRequest } = useFriends();
  const { events } = useEvents();
  const { colors } = useTheme();
  const navigation = useNavigation<any>();
  const route = useRoute<any>();

  // Przechwytywanie trybu
  const visitedUser = route.params?.visitedUser;
  const isOwner = !visitedUser || visitedUser.id === currentUser?.user_id || visitedUser.user_id === currentUser?.user_id;
  const profileData = isOwner ? currentUser : visitedUser;

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);

  const styles = useMemo(() => getStyles(colors), [colors]);

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

  const handleSearch = async (text: string) => {
    setSearchQuery(text);
    if(text.trim().length > 0) {
      const results = await searchUsers(text);
      setSearchResults(results);
    } else {
      setSearchResults([]);
    }
  }

  const handleSendRequest = async () => {
    if (profileData?.id || profileData?.user_id) {
      await sendFriendRequest(profileData.id || profileData.user_id);
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
      <View style={styles.headerRow}>
        <Avatar uri={profileData?.profile_picture?.url || profileData?.avatarUrl || profileData?.profile_picture || MOCKS.AVATAR} size={80} style={{ marginRight: THEME.spacing.m }} />

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
            <Ionicons name="settings-outline" size={28} color={colors.text} />
          </TouchableOpacity>
        )}
      </View>

      <Text style={styles.facultyText}>{profileData?.academy || "Brak Uczelni"}</Text>
      {isOwner && (
        <Text style={styles.majorText}>{profileData?.course ? `${profileData.course} ${profileData.year || ""} rok` : "Brak przypisanego kierunku"}</Text>
      )}

      <Text style={styles.userBio}>{profileData?.description || (isOwner ? "Brak opisu" : "")}</Text>

      {isOwner ? (
        <Button
          title="Edytuj profil"
          onPress={gotoEditProfile}
          style={styles.editButton}
        />
      ) : profileData?.is_friend ? (
        <Button
          title="Jesteście znajomymi"
          onPress={() => {}}
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
            <TextInput
              style={[styles.searchInput, { color: colors.text, borderColor: colors.border }]}
              placeholder="Szukaj użytkowników..."
              placeholderTextColor={colors.icon}
              value={searchQuery}
              onChangeText={handleSearch}
            />
            {searchResults.length > 0 ? (
              searchResults.map((resUser) => (
                <TouchableOpacity key={resUser.id} onPress={() => goToFriendProfile(resUser)} style={[styles.listItem, { borderColor: colors.border }]}>
                  <Avatar uri={resUser.avatarUrl || MOCKS.AVATAR} size={40} />
                  <View style={{ marginLeft: THEME.spacing.m, flex: 1 }}>
                    <Text style={[styles.listText, { marginLeft: 0 }]}>{resUser.username}</Text>
                    <Text style={styles.listSubtitle}>{resUser.academy}</Text>
                  </View>
                </TouchableOpacity>
              ))
            ) : (
              <>
                {friends.length > 0 ? (
                  friends.map((friend) => (
                    <TouchableOpacity key={friend.id} onPress={() => goToFriendProfile(friend)} style={[styles.listItem, { borderColor: colors.border }]}>
                      <Avatar uri={MOCKS.AVATAR} size={40} />
                      <Text style={styles.listText}>{friend.username}</Text>
                    </TouchableOpacity>
                  ))
                ) : (
                  <Text style={styles.infoText}>Brak znajomych na liście</Text>
                )}
              </>
            )}
          </CollapsibleSection>

          <CollapsibleSection title="Moje wydarzenia">
            {events.length > 0 ? (
              events.map((event) => (
                <View key={event.id} style={[styles.listItem, { borderColor: colors.border }]}>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.listTitle}>{event.name}</Text>
                    <Text style={styles.listSubtitle}>{event.date} o {event.time} • {event.location}</Text>
                  </View>
                </View>
              ))
            ) : (
              <Text style={styles.infoText}>Nie utworzyłeś jeszcze żadnych wydarzeń</Text>
            )}
          </CollapsibleSection>

          <CollapsibleSection title="Zapisane wydarzenia">
            <Text style={styles.infoText}>Brak zapisanych wydarzeń (Oczekuje na endpoint w backendzie)</Text>
          </CollapsibleSection>

          <CollapsibleSection
            title="Zdjęcia"
            rightActionIcon="add"
            onRightActionPress={handleAddPhoto}
            initialExpanded={true}
          >
            <View style={styles.placeholderBox}>
              <Image
                source={{ uri: "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80" }}
                style={styles.mockPhoto}
              />
            </View>
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
  searchInput: {
    borderWidth: 1,
    borderRadius: THEME.borderRadius.m,
    padding: 10,
    marginBottom: THEME.spacing.s,
  },
  listItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: THEME.spacing.s,
    borderBottomWidth: 1,
  },
  listText: {
    ...THEME.typography.text,
    marginLeft: THEME.spacing.m,
    fontSize: 16,
    fontWeight: "500",
    color: colors.text,
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