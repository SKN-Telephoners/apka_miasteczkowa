import React, { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Alert, FlatList, SafeAreaView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useNavigation } from "@react-navigation/native";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useTheme } from "../../contexts/ThemeContext";
import { useFriends } from "../../contexts/FriendsContext";
import { useAuth } from "../../contexts/AuthContext";
import { searchUsersByUsername } from "../../services/users";
import { User } from "../../types/friends";
import UserCard from "../../components/UserCard";
import { THEME } from "../../utils/constants";
import InputField from "../../components/InputField";

const SearchScreen = () => {
  const navigation = useNavigation<any>();
  const { colors } = useTheme();
  const { userId } = useAuth();
  const { sendFriendRequest } = useFriends();
  const queryClient = useQueryClient();

  const [searchQuery, setSearchQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  const styles = useMemo(() => getStyles(colors), [colors]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setDebouncedQuery(searchQuery.trim());
    }, 300);

    return () => clearTimeout(timeout);
  }, [searchQuery]);

  const shouldSearch = debouncedQuery.length > 0;

  const { data, isFetching, error } = useQuery({
    queryKey: ["user-search", userId, debouncedQuery],
    queryFn: () => searchUsersByUsername(debouncedQuery, 1, 50),
    enabled: shouldSearch && Boolean(userId),
    staleTime: 0,
    refetchOnMount: "always",
  });

  const users = data?.users ?? [];

  const handleSendRequest = async (targetUserId: string) => {
    try {
      await sendFriendRequest(targetUserId);
      await queryClient.invalidateQueries({ queryKey: ["user-search", userId] });
    } catch (err: any) {
      Alert.alert("Błąd", err?.message || "Nie udało się wysłać zaproszenia");
    }
  };

  const renderItem = ({ item }: { item: User }) => {
    const academy = item.academy || undefined;
    const course = item.course || undefined;
    const isFriend = Boolean(item.is_friend);
    const isSelf = item.id === userId || Boolean((item as any).is_self);

    return (
      <View style={styles.cardWrap}>
        <UserCard
          creatorDisplayName={item.username}
          uniName={academy}
          majorName={course}
          yearOfStudy={item.year ?? undefined}
          showCreatedAt={false}
          showMetaIcon={true}
          showUsernameIcon={!isFriend && !isSelf}
          onUsernameIconPress={!isFriend && !isSelf ? () => handleSendRequest(item.id) : undefined}
          onMetaIconPress={() =>
            navigation.navigate("Main", {
              screen: "Profil",
              params: {
                screen: "UserProfile",
                params: {
                  visitedUser: {
                    ...item,
                    id: item.id,
                    user_id: item.id,
                  },
                },
              },
            })
          }
          avatarUri={item.profile_picture?.url || item.avatarUrl}
        />
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.container}>
        <InputField
          placeholder="Szukaj użytkowników"
          value={searchQuery}
          onChangeText={setSearchQuery}
          showSearchSpriteIcon
          showFloatingLabel={false}
          reserveErrorSpace={false}
        />

        {!shouldSearch ? (
          <Text style={styles.helperText}>Wpisz nazwę użytkownika, aby rozpocząć wyszukiwanie.</Text>
        ) : isFetching ? (
          <View style={styles.stateWrap}>
            <ActivityIndicator size="large" color={colors.highlight} />
          </View>
        ) : error ? (
          <View style={styles.stateWrap}>
            <Text style={[styles.stateText, { color: colors.text }]}>Nie udało się pobrać użytkowników.</Text>
          </View>
        ) : users.length === 0 ? (
          <View style={styles.stateWrap}>
            <Text style={[styles.stateText, { color: colors.text }]}>Brak wyników</Text>
          </View>
        ) : (
          <FlatList
            data={users}
            keyExtractor={(item, index) => item.id || `${item.username}-${index}`}
            renderItem={renderItem}
            contentContainerStyle={styles.list}
            ItemSeparatorComponent={() => <View style={styles.separator} />}
          />
        )}
      </View>
    </SafeAreaView>
  );
};

const getStyles = (colors: typeof THEME.colors.light) =>
  StyleSheet.create({
    screen: {
      flex: 1,
      backgroundColor: colors.background,
    },
    container: {
      flex: 1,
      padding: 16,
    },
    helperText: {
      marginTop: 12,
      color: colors.icon,
      fontSize: 13,
    },
    list: {
      paddingTop: 12,
      paddingBottom: 24,
    },
    cardWrap: {
      backgroundColor: colors.background,
      borderRadius: 16,
      paddingVertical: 12,
      paddingHorizontal: 8,
    },
    separator: {
      height: 12,
    },
    stateWrap: {
      flex: 1,
      alignItems: "center",
      justifyContent: "center",
    },
    stateText: {
      fontSize: 15,
    },
  });

export default SearchScreen;