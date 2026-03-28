import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image, ScrollView } from "react-native";
import { useAuth } from "../../contexts/AuthContext";
import { useUser } from "../../contexts/UserContext";
import { useFriends } from "../../contexts/FriendsContext";
import { useEvents } from "../../contexts/EventContext";
import { useNavigation } from "@react-navigation/native";
import { THEME, MOCKS } from "../../utils/constants";
import Button from "../../components/Button";
import CollapsibleSection from "../../components/CollapsibleSection";
import Avatar from "../../components/Avatar";

// Zapasowe dane, dopóki backend nie ogarnie wydziału i kierunku
const MOCK_EXTRAS = {
  faculty: "WIEiT",
  majorAndYear: "Teleinformatyka 1 rok"
};

const UserScreen = () => {
  const { logout } = useAuth();
  const { user } = useUser();
  const { friends } = useFriends();
  const { events } = useEvents();
  const navigation = useNavigation<any>();

  const gotoEditProfile = () => {
    navigation.navigate("EditProfile");
  };

  const handleAddPhoto = () => {
    console.log("Dodawanie zdjęcia...");
  };

  const goToFriendProfile = (friendName: string) => {
    console.log(`Przejście do profilu: ${friendName}`);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 40 }}>
      {/* 1. Nagłówek: Avatar + Nazwa + Statystyki */}
      <View style={styles.headerRow}>
        <Avatar uri={user?.avatar || MOCKS.AVATAR} size={80} style={{ marginRight: THEME.spacing.m }} />

        <View style={styles.headerInfo}>
          <Text style={styles.userName}>{user?.username || "Użytkownik"}</Text>
          <Text style={styles.statsText}>
            Znajomi: <Text style={styles.statsNumber}>{friends.length}</Text>
          </Text>
          <Text style={styles.statsText}>
            Dołączył: <Text style={styles.statsNumber}>{user?.joinedDate || "Nieznana"}</Text>
          </Text>
        </View>
      </View>

      {/* 2. Wydział i kierunek */}
      <Text style={styles.facultyText}>{MOCK_EXTRAS.faculty}</Text>
      <Text style={styles.majorText}>{MOCK_EXTRAS.majorAndYear}</Text>

      {/* 3. Biografia / Opis */}
      <Text style={styles.userBio}>{user?.bio || "Brak opisu"}</Text>

      {/* 4. Przycisk Edycji */}
      <Button
        title="Edytuj profil"
        onPress={gotoEditProfile}
        style={styles.editButton}
      />

      {/* 5. Zwijane Sekcje */}
      <CollapsibleSection title="Znajomi">
        {friends.length > 0 ? (
          friends.map((friend) => (
            <TouchableOpacity key={friend.id} onPress={() => goToFriendProfile(friend.username)} style={styles.listItem}>
              <Avatar uri={MOCKS.AVATAR} size={40} />
              <Text style={styles.listText}>{friend.username}</Text>
            </TouchableOpacity>
          ))
        ) : (
          <Text style={styles.infoText}>Brak znajomych na liście</Text>
        )}
      </CollapsibleSection>

      <CollapsibleSection title="Moje wydarzenia">
        {events.length > 0 ? (
          events.map((event) => (
            <View key={event.id} style={styles.listItem}>
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

    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: THEME.spacing.m,
    backgroundColor: THEME.colors.lm_bg,
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
    fontFamily: "Roboto", //Musimy mieć duże name i małe name
    fontWeight: "700" as const,
    lineHeight: 20,
    fontSize: 20,
  },
  statsText: {
    ...THEME.typography.text,
    color: THEME.colors.lm_txt,
  },
  statsNumber: {
    fontWeight: "bold",
  },
  facultyText: {
    ...THEME.typography.faculty,
    fontSize: 18,
    lineHeight: 20.5,
  },
  majorText: {
    ...THEME.typography.text,
    marginBottom: THEME.spacing.s,
  },
  userBio: {
    ...THEME.typography.text,
    color: THEME.colors.lm_txt,
    marginBottom: THEME.spacing.m,
  },
  editButton: {
    marginBottom: THEME.spacing.l,
  },
  infoText: {
    ...THEME.typography.text,
    color: THEME.colors.lm_ico,
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
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: THEME.spacing.s,
    borderBottomWidth: 1,
    borderBottomColor: THEME.colors.lm_bg,
  },
  listText: {
    ...THEME.typography.text,
    marginLeft: THEME.spacing.m,
    fontSize: 16,
    fontWeight: "500",
  },
  listTitle: {
    ...THEME.typography.text,
    fontWeight: "bold",
    fontSize: 16,
  },
  listSubtitle: {
    ...THEME.typography.text,
    fontSize: 14,
    color: THEME.colors.lm_txt,
    marginTop: 2,
  }
});

export default UserScreen;