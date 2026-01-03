import React from "react";
import { View, Text, StyleSheet, Button, ScrollView, TouchableOpacity } from "react-native";
import { useAuth } from "../../contexts/AuthContext";
import { useFriends } from "../../contexts/FriendsContext";
import { useNavigation } from "@react-navigation/native";

// Mock do zmiany na wczoraj, jeśli backend obsłuży te pola
const MOCK_EXTRAS = {
  avatar: "👤", // Placeholder avatara
  bio: "Status: Zew Miasteczka za 3,50!", // Domyślne bio
};

const UserScreen = () => {
  const { user, logout } = useAuth();
  const { friends } = useFriends();
  const navigation = useNavigation<any>(); // Typowanie any dla uproszczenia w tym pliku, idealnie powinno być StackNavigationProp

  const handleEditProfile = () => {
    navigation.navigate("EditProfile");
  };

  const goToFriendProfile = (friendName: string) => {
    console.log(`Przejście do profilu: ${friendName}`);
    // TODO: Zaimplementować widok profilu innego użytkownika
  };

  return (
    <ScrollView style={styles.container}>
      {/* 1. Nagłówek i Avartar */}
      <View style={styles.header}>
        <Text style={styles.avatarPlaceholder}>{MOCK_EXTRAS.avatar}</Text>
        {/* Wyświetlamy prawdziwe dane z tokena/bazy */}
        <Text style={styles.userName}>{user?.username || "Użytkownik"}</Text>
        <Text style={styles.userEmail}>{user?.email}</Text>
        <Text style={styles.userBio}>{MOCK_EXTRAS.bio}</Text>

        <View style={styles.buttonRow}>
          <Button title="Edytuj Profil" onPress={handleEditProfile} />
        </View>
      </View>

      {/* 2. Statystyki */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📈 Statystyki</Text>
        <View style={styles.statsRow}>
          {/* Liczba znajomych brana z kontekstu */}
          <Text style={styles.statItem}>Znajomi: **{friends.length}**</Text>
          <Text style={styles.statItem}>Posty: **0** (Wkrótce)</Text>
        </View>
      </View>

      {/* 3. Lista Postów */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📜 Twoje Posty</Text>
        <Text style={styles.infoText}>Historia postów jest w trakcie budowy przez backend.</Text>
      </View>

      {/* 4. Lista Znajomych */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🤝 Znajomi ({friends.length})</Text>
        {friends.length > 0 ? (
          friends.map((friend, index) => (
            <TouchableOpacity key={friend.id || index} onPress={() => goToFriendProfile(friend.username)}>
              <Text style={styles.listItem}>➡️ {friend.username}</Text>
            </TouchableOpacity>
          ))
        ) : (
          <Text style={styles.infoText}>Brak znajomych. Dodaj kogoś!</Text>
        )}
      </View>

      {/* 5. Funkcjonalność Wylogowania */}
      <View style={styles.section}>
        <Button title="Wyloguj" onPress={logout} color="red" />
      </View>

      <View style={{ height: 50 }} />
    </ScrollView>
  );
};

// Podstawowe style
const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: "#fff",
  },
  header: {
    alignItems: "center",
    marginBottom: 20,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
  },
  avatarPlaceholder: {
    fontSize: 50,
    marginBottom: 10,
  },
  userName: {
    fontSize: 22,
    fontWeight: "bold",
    marginBottom: 2,
  },
  userEmail: {
    fontSize: 14,
    color: "#888",
    marginBottom: 5,
  },
  userBio: {
    fontSize: 14,
    color: "#666",
    textAlign: "center",
    marginBottom: 10,
    fontStyle: 'italic',
  },
  section: {
    marginBottom: 25,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "600",
    marginBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#f0f0f0",
    paddingBottom: 5,
  },
  statsRow: {
    flexDirection: "row",
    justifyContent: "space-around",
  },
  statItem: {
    fontSize: 16,
    textAlign: "center",
  },
  listItem: {
    fontSize: 16,
    paddingVertical: 8,
    color: "#007AFF",
  },
  infoText: {
    fontSize: 14,
    color: "#999",
    fontStyle: "italic",
  },
  buttonRow: {
    marginTop: 10,
  }
});

export default UserScreen;