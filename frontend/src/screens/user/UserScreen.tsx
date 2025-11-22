import React from "react";
import { View, Text, StyleSheet, Button, ScrollView } from "react-native";
import { useAuth } from "../../contexts/AuthContext";

// Mock do poniedziałku
const MOCK_USER = {
  name: "Jan Kowalski",
  avatar: "[Avatar Janka]", // Placeholder
  bio: "Frontend Developer. Lubię TypeScript i szybkie kawy.",
  stats: {
    followers: 120,
    following: 55,
    posts: 42,
  },
  friends: ["Anna Nowak", "Piotr Zieliński", "Ewa Lewandowska"],
  recentPosts: [
    "Wydarzenie 1: Spotkanie z ekipą (05.11)",
    "Wydarzenie 2: Hackathon (20.10)",
  ],
};

const UserScreen = () => {
  // Funkcja do wylogowania
  const { logout } = useAuth();
  
  // Funkcja placeholder dla edycji
  const handleEditProfile = () => {
    console.log("Przejście do Edycji Profilu...");
    // Tutaj będzie nawigacja do edytora
  };

  // Funkcja placeholder dla przejścia do profilu znajomego
  const goToFriendProfile = (friendName: string) => {
    console.log(`Przejście do profilu: ${friendName}`);
    // Jeszcze nawigacja
  };

  return (
    <ScrollView style={styles.container}>
      {/* 1. Nagłówek i Avartar */}
      <View style={styles.header}>
        <Text style={styles.avatarPlaceholder}>{MOCK_USER.avatar}</Text>
        <Text style={styles.userName}>{MOCK_USER.name}</Text>
        <Text style={styles.userBio}>{MOCK_USER.bio}</Text>
        <View style={styles.buttonRow}>
          <Button title="Edytuj Profil" onPress={handleEditProfile} />
        </View>
      </View>

      {/* 2. Statystyki */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📈 Statystyki</Text>
        <View style={styles.statsRow}>
          <Text style={styles.statItem}>Obserwujący: **{MOCK_USER.stats.followers}**</Text>
          <Text style={styles.statItem}>Obserwowani: **{MOCK_USER.stats.following}**</Text>
          <Text style={styles.statItem}>Posty: **{MOCK_USER.stats.posts}**</Text>
        </View>
      </View>

      {/* 3. Lista Postów */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>📜 Twoje Posty</Text>
        {MOCK_USER.recentPosts.map((post, index) => (
          <Text key={index} style={styles.listItem} onPress={() => console.log(`Post: ${post}`)}>
            - {post}
          </Text>
        ))}
      </View>

      {/* 4. Lista Znajomych */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🤝 Znajomi</Text>
        {MOCK_USER.friends.map((friend, index) => (
          <Text key={index} style={styles.listItem} onPress={() => goToFriendProfile(friend)}>
            ➡️ {friend}
          </Text>
        ))}
      </View>

      {/* 5. Funkcjonalność Wylogowania */}
      <View style={styles.section}>
        <Button title="Logout" onPress={logout} color="red" />
      </View>
      
      <View style={{ height: 50 }} /> {/* Dodatkowy margines na dole */}
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
    fontSize: 24,
    marginBottom: 10,
    fontWeight: 'bold',
  },
  userName: {
    fontSize: 22,
    fontWeight: "bold",
    marginBottom: 5,
  },
  userBio: {
    fontSize: 14,
    color: "#666",
    textAlign: "center",
    marginBottom: 10,
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
    fontSize: 14,
    textAlign: "center",
  },
  listItem: {
    fontSize: 16,
    paddingVertical: 5,
    color: "#007AFF", // Kolor linku
  },
  buttonRow: {
    marginTop: 10,
  }
});

export default UserScreen;