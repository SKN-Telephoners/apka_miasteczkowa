import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Image } from "react-native";
import { useAuth } from "../../contexts/AuthContext";
import { useFriends } from "../../contexts/FriendsContext";
import { useNavigation } from "@react-navigation/native";
import { THEME, MOCKS } from "../../utils/constants";
import Button from "../../components/Button";
import CollapsibleSection from "../../components/CollapsibleSection";
import Avatar from "../../components/Avatar";

// Mock do zmiany na wczoraj, jeśli backend obsłuży te pola
const MOCK_EXTRAS = {
  bio: "Status: Zew Miasteczka za 3,50!", // Domyślne bio
  faculty: "WIEiT",
  majorAndYear: "Teleinformatyka 1 rok"
};

const UserScreen = () => {
  const { user, logout } = useAuth();
  const { friends } = useFriends();
  const navigation = useNavigation<any>();

  const handleEditProfile = () => {
    navigation.navigate("EditProfile");
  };

  const handleAddPhoto = () => {
    console.log("Dodawanie zdjęcia...");
  };

  const goToFriendProfile = (friendName: string) => {
    console.log(`Przejście do profilu: ${friendName}`);
  };

  return (
    <View style={styles.container}>
      {/* 1. Nagłówek: Avatar + Nazwa + Statystyki */}
      <View style={styles.headerRow}>
        <Avatar uri={MOCKS.AVATAR} size={80} style={{ marginRight: THEME.spacing.m }} />

        <View style={styles.headerInfo}>
          <Text style={styles.userName}>{user?.username || "Użytkownik"}</Text>
        </View>
      </View>

      {/* 2. Wydział i kierunek */}
      <Text style={styles.facultyText}>{MOCK_EXTRAS.faculty}</Text>
      <Text style={styles.majorText}>{MOCK_EXTRAS.majorAndYear}</Text>

      {/* 3. Biografia / Opis */}
      <Text style={styles.userBio}>{MOCK_EXTRAS.bio}</Text>

      {/* 4. Przycisk Edycji */}
      <Button
        title="Edytuj profil"
        onPress={handleEditProfile}
        style={styles.editButton}
      />

      {/* 5. Zwijane Sekcje */}
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

      <CollapsibleSection title="Wpisy">
        <Text style={styles.infoText}>Historia wpisów (w budowie)</Text>
      </CollapsibleSection>

    </View>
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
    ...THEME.typography.name,
    fontSize: 20,
    lineHeight: 16,
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
  }
});

export default UserScreen;