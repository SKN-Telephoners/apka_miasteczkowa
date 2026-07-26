import React, { useState } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl, ActivityIndicator } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../../contexts/ThemeContext';
import { THEME } from '../../utils/constants';
import { useNotifications } from '../../contexts/NotificationsContext';
import NotificationCard from '../../components/NotificationsCard';
import NotificationActionButtons from '../../components/NotificationActionButtons';
import { useFriends } from '../../contexts/FriendsContext';
import { changeInviteStatus } from '../../services/events';
import { AggregatedNotification, AppNotification } from '../../services/notifications';

const NotificationsScreen = () => {
    const navigation = useNavigation<any>();
    const { colors } = useTheme();
    const {
        notifications,
        fetchNotifications,
        markAsRead,
        isLoading,
        isRefreshing,
        hasMore,
        currentPage
    } = useNotifications();
    const { acceptRequest, declineRequest } = useFriends();

    const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

    const handleLoadMore = () => {
        if (hasMore && !isLoading && !isRefreshing) {
            fetchNotifications(currentPage + 1);
        }
    };

    const handleRefresh = () => {
        fetchNotifications(1, true);
    };

    const handlePress = (notification: AggregatedNotification | AppNotification, isGroupHeader: boolean = false) => {
        if (isGroupHeader && 'count' in notification && (notification as AggregatedNotification).count > 1) {
            const aggNotif = notification as AggregatedNotification;
            setExpandedIds(prev => {
                const next = new Set(prev);
                if (next.has(aggNotif.notification_id)) {
                    next.delete(aggNotif.notification_id);
                } else {
                    next.add(aggNotif.notification_id);
                }
                return next;
            });

            if (!aggNotif.is_read) {
                markAsRead(aggNotif.aggregated_ids);
            }
            return;
        }

        if (!notification.is_read) {
            if ('aggregated_ids' in notification) {
                markAsRead((notification as AggregatedNotification).aggregated_ids);
            } else {
                markAsRead([notification.notification_id]);
            }
        }

        const tag = notification.tag;
        const payload = notification.payload;

        if (tag === 'friend-request-created' || tag === 'friend-request-accepted') {
            const userId = payload.sender_id || payload.friend_id;
            const username = payload.sender_name || payload.friend_name;
            if (userId) {
                navigation.navigate("UserScreen", {
                    visitedUser: {
                        id: userId,
                        user_id: userId,
                        username: username,
                    },
                });
            }
        } else if (payload.event_id) {
            navigation.navigate("EventDetails", { eventId: payload.event_id });
        }
    };

    const renderActionButtons = (notification: AggregatedNotification | AppNotification, isSubItem: boolean) => {
        if ('count' in notification && (notification as AggregatedNotification).count > 1 && !isSubItem) {
            return null;
        }

        const tag = notification.tag;
        const payload = notification.payload;
        const idsToMark = 'aggregated_ids' in notification ? (notification as AggregatedNotification).aggregated_ids : [notification.notification_id];

        if (tag === 'friend-request-created') {
            const userId = payload.sender_id;
            return (
                <NotificationActionButtons
                    onAccept={async () => {
                        await acceptRequest(userId);
                        markAsRead(idsToMark);
                    }}
                    onDecline={async () => {
                        await declineRequest(userId);
                        markAsRead(idsToMark);
                    }}
                />
            );
        }

        if (tag === 'invite-created') {
            const inviteId = payload.invite_id;
            return (
                <NotificationActionButtons
                    onAccept={async () => {
                        await changeInviteStatus(inviteId, 'accepted');
                        markAsRead(idsToMark);
                    }}
                    onDecline={async () => {
                        await changeInviteStatus(inviteId, 'declined');
                        markAsRead(idsToMark);
                    }}
                />
            );
        }

        return null;
    };

    const renderItem = ({ item }: { item: AggregatedNotification }) => {
        const isExpanded = expandedIds.has(item.notification_id);
        const hasMultiple = item.count > 1;

        return (
            <View>
                <NotificationCard
                    notification={item}
                    onPress={() => handlePress(item, true)}
                    actions={renderActionButtons(item, false)}
                    isExpanded={isExpanded}
                />
                {isExpanded && hasMultiple && (
                    <View style={styles.expandedContainer}>
                        {item.raw_notifications.map(raw => (
                            <NotificationCard
                                key={raw.notification_id}
                                notification={raw}
                                onPress={() => handlePress(raw, false)}
                                actions={renderActionButtons(raw, true)}
                                isSubItem={true}
                            />
                        ))}
                    </View>
                )}
            </View>
        );
    };

    const renderFooter = () => {
        if (!isLoading || isRefreshing) return null;
        return (
            <View style={{ paddingVertical: 20 }}>
                <ActivityIndicator size="small" color={colors.highlight} />
            </View>
        );
    };

    return (
        <View style={[styles.container, { backgroundColor: colors.background }]}>
            <FlatList
                data={notifications}
                renderItem={renderItem}
                keyExtractor={(item) => item.notification_id}
                contentContainerStyle={[styles.list, notifications.length === 0 && { flex: 1 }]}
                onEndReached={handleLoadMore}
                onEndReachedThreshold={0.5}
                refreshControl={
                    <RefreshControl
                        refreshing={isRefreshing}
                        onRefresh={handleRefresh}
                        colors={[colors.highlight]}
                        tintColor={colors.highlight}
                    />
                }
                ListFooterComponent={renderFooter}
                ListEmptyComponent={
                    !isLoading ? (
                        <View style={styles.emptyContainer}>
                            <Text style={[styles.emptyText, { color: colors.text }]}>Brak powiadomień</Text>
                        </View>
                    ) : null
                }
            />
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
    expandedContainer: {
        marginBottom: THEME.spacing.m,
    },
    emptyContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    emptyText: {
        textAlign: 'center',
        fontSize: 16,
    }
});

export default NotificationsScreen;
