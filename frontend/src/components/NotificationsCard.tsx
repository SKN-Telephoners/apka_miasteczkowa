import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useTheme } from '../contexts/ThemeContext';
import { AppNotification } from '../services/notifications';
import { THEME } from '../utils/constants';
import AppIcon, { IconName } from './AppIcon';

interface NotificationCardProps {
    notification: AppNotification;
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

const NotificationCard: React.FC<NotificationCardProps> = ({ notification, onPress, actions }) => {
    const { colors } = useTheme();
    const { name: iconName, color: iconColor } = getIconForTag(notification.tag);

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
                </View>
                <View style={styles.content}>
                    <Text style={[
                        styles.message, 
                        { color: colors.text },
                        !notification.is_read && styles.unreadMessage
                    ]}>
                        {notification.payload.message || 'Nowe powiadomienie'}
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
