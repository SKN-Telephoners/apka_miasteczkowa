import React, { useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useFriends } from '../../contexts/FriendsContext';
import { THEME } from '../../utils/constants';
import { useTheme } from '../../contexts/ThemeContext';
import UserCard from '../../components/UserCard';

const NotificationsScreen = () => {
    const navigation = useNavigation<any>();
    const { incomingRequests, acceptRequest, declineRequest, fetchFriends } = useFriends();
    const { colors } = useTheme();

    useEffect(() => {
        fetchFriends(); // Odświeżenie danych o powiadomieniach
    }, []);

    const renderItem = ({ item }: { item: any }) => {
        const handleNavigateToProfile = () => {
            navigation.navigate("UserScreen", {
                visitedUser: {
                    id: item.user.id,
                    user_id: item.user.id,
                    username: item.user.username,
                    is_friend: false,
                },
            });
        };

        return (
            <View style={[styles.itemContainer, { backgroundColor: colors.card }]}>
                <UserCard
                    creatorDisplayName={item.user.username}
                    createdAtDisplay={item.user.department && item.user.major ? `${item.user.department} • ${item.user.major}` : undefined}
                    showUsernameIcon={false}
                    showMetaIcon={true}
                    showMetaRow={true}
                    showCreatedAt={false}
                    onMetaIconPress={handleNavigateToProfile}
                />
                <View style={styles.actionButtons}>
                    <TouchableOpacity 
                        style={[styles.button, { backgroundColor: colors.highlight }]} 
                        onPress={() => acceptRequest(item.id)}
                    >
                        <Text style={styles.buttonText}>Akceptuj</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                        style={[styles.button, styles.declineButton]} 
                        onPress={() => declineRequest(item.id)}
                    >
                        <Text style={styles.buttonText}>Odrzuć</Text>
                    </TouchableOpacity>
                </View>
            </View>
        );
    };

    return (
        <View style={[styles.container, { backgroundColor: colors.background }]}>
            {incomingRequests.length === 0 ? (
                <Text style={[styles.emptyText, { color: colors.text }]}>Brak nowych powiadomień</Text>
            ) : (
                <FlatList
                    data={incomingRequests}
                    renderItem={renderItem}
                    keyExtractor={(item) => item.id}
                    contentContainerStyle={styles.list}
                />
            )}
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
    },
    list: {
        padding: THEME.spacing.m,
    },
    itemContainer: {
        flexDirection: 'column',
        padding: THEME.spacing.m,
        marginBottom: THEME.spacing.s,
        borderRadius: THEME.borderRadius.m,
    },
    actionButtons: {
        flexDirection: 'row',
        gap: 8,
        marginLeft: THEME.spacing.s,
        marginTop: THEME.spacing.s,
        alignSelf: 'flex-end',
    },
    button: {
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: THEME.borderRadius.s,
    },
    declineButton: {
        backgroundColor: '#e74c3c',
    },
    buttonText: {
        color: '#FFFFFF',
        fontWeight: 'bold',
    },
    emptyText: {
        textAlign: 'center',
        marginTop: 50,
        fontSize: 16,
    }
});

export default NotificationsScreen;
