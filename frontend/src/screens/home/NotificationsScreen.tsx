import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useFriends } from '../../contexts/FriendsContext';
import { THEME } from '../../utils/constants';
import { useTheme } from '../../contexts/ThemeContext';
import UserCard from '../../components/UserCard';
import { changeInviteStatus, EventInviteNotification, getIncomingEventInvites } from '../../services/events';

type NotificationItem =
    | { kind: 'friend'; item: any; key: string }
    | { kind: 'event'; item: EventInviteNotification; key: string };

const NotificationsScreen = () => {
    const navigation = useNavigation<any>();
    const { incomingRequests, acceptRequest, declineRequest, fetchFriends } = useFriends();
    const { colors } = useTheme();
    const [incomingEventInvites, setIncomingEventInvites] = useState<EventInviteNotification[]>([]);

    const loadNotifications = useCallback(async () => {
        await fetchFriends();
        try {
            const invites = await getIncomingEventInvites();
            setIncomingEventInvites(invites);
        } catch (error) {
            console.error('Failed to load incoming event invites:', error);
            setIncomingEventInvites([]);
        }
    }, [fetchFriends]);

    useEffect(() => {
        loadNotifications();
    }, [loadNotifications]);

    const notifications = useMemo<NotificationItem[]>(() => {
        const friendItems = incomingRequests.map((item: any) => ({
            kind: 'friend' as const,
            item,
            key: `friend-${item.id}`,
        }));
        const eventItems = incomingEventInvites.map((item) => ({
            kind: 'event' as const,
            item,
            key: `event-${item.id}`,
        }));
        return [...friendItems, ...eventItems];
    }, [incomingRequests, incomingEventInvites]);

    const renderFriendRequestItem = (item: any) => {
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
                    avatarUri={item.user.profile_picture?.url || item.user.avatarUrl}
                    createdAtDisplay={item.user.course || undefined}
                    metaPrefix={item.user.academy || "wydział • kierunek"}
                    showUsernameIcon={false}
                    showMetaIcon={true}
                    showMetaRow={true}
                    showCreatedAt={Boolean(item.user.course)}
                    onMetaIconPress={handleNavigateToProfile}
                />
                <View style={styles.actionButtons}>
                    <TouchableOpacity 
                        style={[styles.button, { backgroundColor: colors.highlight }]} 
                        onPress={async () => {
                            await acceptRequest(item.id);
                            await loadNotifications();
                        }}
                    >
                        <Text style={styles.buttonText}>Akceptuj</Text>
                    </TouchableOpacity>
                    <TouchableOpacity 
                        style={[styles.button, styles.declineButton]} 
                        onPress={async () => {
                            await declineRequest(item.id);
                            await loadNotifications();
                        }}
                    >
                        <Text style={styles.buttonText}>Odrzuć</Text>
                    </TouchableOpacity>
                </View>
            </View>
        );
    };

    const renderEventInviteItem = (invite: EventInviteNotification) => {
        const handleNavigateToProfile = () => {
            navigation.navigate("UserScreen", {
                visitedUser: {
                    id: invite.inviter.id,
                    user_id: invite.inviter.id,
                    username: invite.inviter.username,
                    is_friend: true,
                },
            });
        };

        const openEventPreview = () => {
            navigation.navigate('Main', {
                screen: 'Wydarzenia',
                params: {
                    screen: 'EventPreview',
                    params: {
                        event: invite.event,
                        screenTitle: 'Zaproszenie do wydarzenia',
                        allowEdit: false,
                    },
                },
            });
        };

        return (
            <View style={[styles.itemContainer, { backgroundColor: colors.card }]}> 
                <UserCard
                    creatorDisplayName={invite.inviter.username}
                    avatarUri={invite.inviter.profile_picture?.url || invite.inviter.avatarUrl}
                    createdAtDisplay={invite.inviter.course || undefined}
                    metaPrefix={invite.inviter.academy || 'wydział • kierunek'}
                    showUsernameIcon={false}
                    showMetaIcon={true}
                    showMetaRow={true}
                    showCreatedAt={Boolean(invite.inviter.course)}
                    onMetaIconPress={handleNavigateToProfile}
                />

                <TouchableOpacity style={[styles.eventLink, { borderColor: colors.border }]} onPress={openEventPreview} activeOpacity={0.8}>
                    <Text style={[styles.eventTitle, { color: colors.text }]}>{invite.event.name}</Text>
                    <Text style={[styles.eventSubtitle, { color: colors.icon }]}>{invite.event.date} o {invite.event.time} • {invite.event.location}</Text>
                </TouchableOpacity>

                <View style={styles.actionButtons}>
                    <TouchableOpacity
                        style={[styles.button, { backgroundColor: colors.highlight }]}
                        onPress={async () => {
                            await changeInviteStatus(invite.id, 'accepted');
                            await loadNotifications();
                        }}
                    >
                        <Text style={styles.buttonText}>Akceptuj</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                        style={[styles.button, styles.declineButton]}
                        onPress={async () => {
                            await changeInviteStatus(invite.id, 'declined');
                            await loadNotifications();
                        }}
                    >
                        <Text style={styles.buttonText}>Odrzuć</Text>
                    </TouchableOpacity>
                </View>
            </View>
        );
    };

    const renderItem = ({ item }: { item: NotificationItem }) => {
        if (item.kind === 'friend') {
            return renderFriendRequestItem(item.item);
        }
        return renderEventInviteItem(item.item);
    };

    return (
        <View style={[styles.container, { backgroundColor: colors.background }]}>
            {notifications.length === 0 ? (
                <Text style={[styles.emptyText, { color: colors.text }]}>Brak nowych powiadomień</Text>
            ) : (
                <FlatList
                    data={notifications}
                    renderItem={renderItem}
                    keyExtractor={(item) => item.key}
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
    eventLink: {
        marginTop: THEME.spacing.s,
        marginHorizontal: THEME.spacing.s,
        paddingVertical: THEME.spacing.s,
        borderBottomWidth: 1,
    },
    eventTitle: {
        ...THEME.typography.eventTitle,
    },
    eventSubtitle: {
        ...THEME.typography.text,
        marginTop: 4,
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
