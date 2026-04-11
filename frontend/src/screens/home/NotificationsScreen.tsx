import React, { useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { useFriends } from '../../contexts/FriendsContext';
import { THEME } from '../../utils/constants';
import { useTheme } from '../../contexts/ThemeContext';

const NotificationsScreen = () => {
    const { incomingRequests, acceptRequest, declineRequest, fetchFriends } = useFriends();
    const { colors } = useTheme();

    useEffect(() => {
        fetchFriends(); // Odświeżenie danych o powiadomieniach
    }, []);

    const renderItem = ({ item }: { item: any }) => (
        <View style={[styles.itemContainer, { backgroundColor: colors.card }]}>
            <View style={styles.userInfo}>
                <Text style={[styles.username, { color: colors.text }]}>{item.user.username}</Text>
            </View>
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
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: THEME.spacing.m,
        marginBottom: THEME.spacing.s,
        borderRadius: THEME.borderRadius.m,
    },
    userInfo: {
        flex: 1,
    },
    username: {
        fontSize: 16,
        fontWeight: 'bold',
    },
    actionButtons: {
        flexDirection: 'row',
        gap: 8,
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
