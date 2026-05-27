import React, { useCallback } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { THEME } from '../../utils/constants';
import { useTheme } from '../../contexts/ThemeContext';
import { useNotifications } from '../../contexts/NotificationsContext';
import NotificationsCard from '../../components/NotificationsCard';
import Button from '../../components/Button';
import { changeInviteStatus } from '../../services/events';
import { useFriends } from '../../contexts/FriendsContext';
import { AppNotification } from '../../services/notifications';

const NotificationsScreen = () => {
    const navigation = useNavigation<any>();
    const { colors } = useTheme();
    const { 
        notifications, 
        isLoading, 
        isRefreshing, 
        hasMore, 
        fetchNotifications 
    } = useNotifications();
    const { acceptRequest, declineRequest } = useFriends();

    const handleRefresh = () => {
        fetchNotifications(1, true);
    };

    const handleLoadMore = () => {
        if (hasMore && !isLoading && !isRefreshing) {
            // Paginacja w kontekście może wyliczyć następną stronę,
            // Jeśli context zakłada tylko strzał do strony, to na razie zostawmy
            // TODO: Podpiąć doczytywanie stron
        }
    };

    const renderActionButtons = (notification: AppNotification) => {
        const { tag, payload } = notification;

        if (tag === 'invite-created') {
            return (
                <>
                    <Button
                        title="Akceptuj"
                        type="primary"
                        style={{ flex: 1, marginVertical: 0, height: 36 }}
                        onPress={async () => {
                            await changeInviteStatus(payload.invite_id, 'accepted');
                            fetchNotifications(1, true);
                        }}
                    />
                    <Button
                        title="Odrzuć"
                        type="danger"
                        style={{ flex: 1, marginVertical: 0, height: 36 }}
                        onPress={async () => {
                            await changeInviteStatus(payload.invite_id, 'declined');
                            fetchNotifications(1, true);
                        }}
                    />
                </>
            );
        }

        if (tag === 'friend-request-created') {
            return (
                <>
                    <Button
                        title="Akceptuj"
                        type="primary"
                        style={{ flex: 1, marginVertical: 0, height: 36 }}
                        onPress={async () => {
                            await acceptRequest(payload.friend_request_id);
                            fetchNotifications(1, true);
                        }}
                    />
                    <Button
                        title="Odrzuć"
                        type="danger"
                        style={{ flex: 1, marginVertical: 0, height: 36 }}
                        onPress={async () => {
                            await declineRequest(payload.friend_request_id);
                            fetchNotifications(1, true);
                        }}
                    />
                </>
            );
        }

        return null;
    };

    const handleNotificationPress = (notification: AppNotification) => {
        const { tag, payload } = notification;

        if (payload.event_id) {
            navigation.navigate('Main', {
                screen: 'Wydarzenia',
                params: {
                    screen: 'EventPreview',
                    params: {
                        event_id: payload.event_id,
                        screenTitle: 'Szczegóły z powiadomienia',
                        allowEdit: false,
                    },
                },
            });
        } else if (payload.sender_id && tag.includes('friend')) {
            navigation.navigate("UserScreen", {
                visitedUser: {
                    id: payload.sender_id,
                    user_id: payload.sender_id,
                    username: payload.sender_name || payload.creator_name || 'Użytkownik',
                    is_friend: tag !== 'friend-request-created',
                },
            });
        }
    };

    const renderItem = ({ item }: { item: AppNotification }) => {
        const actions = renderActionButtons(item);
        
        return (
            <NotificationsCard
                notification={item}
                onPress={() => handleNotificationPress(item)}
                actions={actions}
            />
        );
    };

    return (
        <View style={[styles.container, { backgroundColor: colors.background }]}>
            {notifications.length === 0 && !isLoading ? (
                <Text style={[styles.emptyText, { color: colors.text }]}>Brak nowych powiadomień</Text>
            ) : (
                <FlatList
                    data={notifications}
                    renderItem={renderItem}
                    keyExtractor={(item) => item.notification_id}
                    contentContainerStyle={styles.list}
                    refreshControl={
                        <RefreshControl 
                            refreshing={isRefreshing} 
                            onRefresh={handleRefresh} 
                            colors={[colors.primary]}
                            tintColor={colors.primary}
                        />
                    }
                    onEndReached={handleLoadMore}
                    onEndReachedThreshold={0.5}
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
    emptyText: {
        textAlign: 'center',
        marginTop: 50,
        fontSize: 16,
    }
});

export default NotificationsScreen;
