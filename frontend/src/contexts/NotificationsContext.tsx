import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback, useMemo } from 'react';
import { getNotifications, markNotificationAsRead, AppNotification, AggregatedNotification } from '../services/notifications';
import { aggregateNotifications } from '../utils/notificationAggregator';
import { useAuth } from './AuthContext';

interface NotificationsContextProps {
    notifications: AggregatedNotification[];
    unreadCount: number | null;
    isLoading: boolean;
    isRefreshing: boolean;
    hasMore: boolean;
    fetchNotifications: (page?: number, isRefresh?: boolean) => Promise<void>;
    markAsRead: (notificationIds: string[]) => Promise<void>;
    currentPage: number;
}

const NotificationsContext = createContext<NotificationsContextProps | undefined>(undefined);

export const NotificationsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const { isAuthenticated } = useAuth();

    const [notifications, setNotifications] = useState<AppNotification[]>([]);
    const [unreadCount, setUnreadCount] = useState<number | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(false);
    const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
    const [hasMore, setHasMore] = useState<boolean>(true);
    const [currentPage, setCurrentPage] = useState<number>(1);

    const fetchNotifications = useCallback(async (page: number = 1, isRefresh: boolean = false) => {
        if (!isAuthenticated) return;

        if (isRefresh) {
            setIsRefreshing(true);
        } else {
            setIsLoading(true);
        }

        try {
            const data = await getNotifications(page, 20);

            if (isRefresh || page === 1) {
                setNotifications(data.data);
            } else {
                setNotifications(prev => [...prev, ...data.data]);
            }

            setHasMore(data.pagination.has_next);
            setCurrentPage(data.pagination.page);
            if (data.pagination.unread_count !== null && data.pagination.unread_count !== undefined) {
                setUnreadCount(data.pagination.unread_count);
            }

        } catch (error) {
            console.error('Error in NotificationsContext fetch:', error);
        } finally {
            setIsLoading(false);
            setIsRefreshing(false);
        }
    }, [isAuthenticated]);

    useEffect(() => {
        if (isAuthenticated) {
            fetchNotifications(1, true);
        } else {
            setNotifications([]);
            setUnreadCount(null);
            setHasMore(true);
            setCurrentPage(1);
        }
    }, [isAuthenticated, fetchNotifications]);

    const aggregatedNotifications = useMemo(() => aggregateNotifications(notifications), [notifications]);

    const markAsRead = async (notificationIds: string[]) => {
        try {
            await Promise.all(notificationIds.map(id => markNotificationAsRead(id)));
            setNotifications(prev =>
                prev.map(notif =>
                    notificationIds.includes(notif.notification_id)
                        ? { ...notif, is_read: true }
                        : notif
                )
            );
            setUnreadCount(prev => {
                if (prev === null) return null;
                const newlyRead = notifications.filter(n => notificationIds.includes(n.notification_id) && !n.is_read).length;
                return Math.max(0, prev - newlyRead);
            });
        } catch (error) {
            console.error("Failed to mark notifications as read", error);
        }
    };

    return (
        <NotificationsContext.Provider value={{
            notifications: aggregatedNotifications,
            unreadCount,
            isLoading,
            isRefreshing,
            hasMore,
            currentPage,
            fetchNotifications,
            markAsRead
        }}>
            {children}
        </NotificationsContext.Provider>
    );
};

export const useNotifications = (): NotificationsContextProps => {
    const context = useContext(NotificationsContext);
    if (!context) {
        throw new Error('useNotifications must be used within a NotificationsProvider');
    }
    return context;
};
