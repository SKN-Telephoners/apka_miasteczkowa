import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { AppNotification, AggregatedNotification } from '../services/notifications';
import { THEME } from '../utils/constants';
import AppIcon, { IconName } from './AppIcon';

interface NotificationCardProps {
    notification: AppNotification | AggregatedNotification;
    onPress?: () => void;
    actions?: React.ReactNode;
}

const getIconForTag = (tag: string): { name: IconName; color: string } => {
    switch (tag) {
        case 'friend-request-created':
        case 'friend-request-accepted':
            return { name: 'AddUser', color: '#3498db' };
        case 'invite-created':
        case 'invite-status-update':
            return { name: 'Send', color: '#9b59b6' };
        case 'event-new-participant':
        case 'event-new-comment':
        case 'comment-reply-created':
            return { name: 'Comment', color: '#f39c12' };
        case 'friend-new-public-event':
        case 'friend-new-private-event':
        case 'joined-event-updated':
        case 'joined-event-deleted':
            return { name: 'Events', color: '#e74c3c' };
        default:
            return { name: 'Bell', color: '#7f8c8d' };
    }
};

const getLocalizedMessage = (tag: string, payload: any): string => {
    switch (tag) {
        case 'event-new-participant':
            return `${payload.participant_name} dołączył(a) do Twojego wydarzenia ${payload.event_name}.`;
        case 'event-new-comment':
            return `${payload.commenter_name} skomentował(a) Twoje wydarzenie ${payload.event_name}.`;
        case 'invite-created':
            return `${payload.sender_name} zaprosił(a) Cię do wydarzenia ${payload.event_name}.`;
        case 'invite-status-update':
            const statusPl = payload.status === 'accepted' ? 'zaakceptował(a)' : 'odrzucił(a)';
            return `${payload.invitee_name} ${statusPl} Twoje zaproszenie do ${payload.event_name}.`;
        case 'joined-event-updated':
            return `Wydarzenie w którym bierzesz udział (${payload.event_name}) zostało zaktualizowane.`;
        case 'joined-event-deleted':
            return `Wydarzenie "${payload.event_name}" organizowane przez ${payload.creator_name} zostało anulowane.`;
        case 'friend-request-created':
            return `${payload.sender_name} wysłał(a) Ci zaproszenie do znajomych.`;
        case 'friend-request-accepted':
            return `${payload.friend_name} zaakceptował(a) Twoje zaproszenie do znajomych!`;
        case 'friend-new-public-event':
            return `Twój znajomy ${payload.creator_name} utworzył nowe wydarzenie publiczne: ${payload.event_name}.`;
        case 'friend-new-private-event':
            return `Twój znajomy ${payload.creator_name} udostępnił Ci prywatne wydarzenie: ${payload.event_name}.`;
        case 'comment-reply-created':
            return `${payload.replier_name} odpowiedział(a) na Twój komentarz w ${payload.event_name}.`;
        default:
            return payload.message || 'Masz nowe powiadomienie.';
    }
};

const NotificationCard: React.FC<NotificationCardProps> = ({ notification, onPress, actions }) => {
    const { colors } = useTheme();
    const { name: iconName, color: iconColor } = getIconForTag(notification.tag);
    
    const isAggregated = 'count' in notification && (notification as AggregatedNotification).count > 1;
    const aggregatedCount = isAggregated ? (notification as AggregatedNotification).count : 0;

    return (
        <TouchableOpacity 
            style={[
                styles.container, 
                { backgroundColor: colors.background, borderColor: colors.border },
                !notification.is_read && { borderLeftWidth: 4, borderLeftColor: colors.primary }
            ]} 
            onPress={onPress}
            activeOpacity={onPress ? 0.7 : 1}
            disabled={!onPress}
        >
            <View style={styles.header}>
                <View style={[styles.iconContainer, { backgroundColor: `${iconColor}20` }]}>
                    <AppIcon name={iconName} size={24} color={iconColor} />
                    {isAggregated && (
                        <View style={[styles.badge, { backgroundColor: colors.primary }]}>
                            <Text style={styles.badgeText}>{aggregatedCount}</Text>
                        </View>
                    )}
                </View>
                <View style={styles.content}>
                    <Text style={[
                        styles.message, 
                        { color: colors.text },
                        !notification.is_read && styles.unreadMessage
                    ]}>
                        {getLocalizedMessage(notification.tag, notification.payload)}
                    </Text>
                    <Text style={[styles.date, { color: colors.icon }]}>
                        {notification.date} o {notification.time}
                    </Text>
                </View>
            </View>

            {actions && (
                <View style={styles.actionsContainer}>
                    {actions}
                </View>
            )}
        </TouchableOpacity>
    );
};

const styles = StyleSheet.create({
    container: {
        padding: THEME.spacing.m,
        marginBottom: THEME.spacing.m,
        borderRadius: THEME.borderRadius.m,
        borderWidth: 1,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'flex-start',
    },
    iconContainer: {
        width: 40,
        height: 40,
        borderRadius: 20,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: THEME.spacing.m,
        position: 'relative',
    },
    badge: {
        position: 'absolute',
        top: -5,
        right: -5,
        width: 20,
        height: 20,
        borderRadius: 10,
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 2,
        borderColor: '#fff',
    },
    badgeText: {
        color: '#fff',
        fontSize: 10,
        fontWeight: 'bold',
    },
    content: {
        flex: 1,
    },
    message: {
        ...THEME.typography.text,
        marginBottom: 4,
    },
    unreadMessage: {
        fontWeight: 'bold',
    },
    date: {
        ...THEME.typography.text,
        fontSize: 12,
    },
    actionsContainer: {
        marginTop: THEME.spacing.m,
        marginLeft: 40 + THEME.spacing.m,
        flexDirection: 'row',
        gap: THEME.spacing.s,
    },
});

export default NotificationCard;
