import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { getNotifications, AppNotification } from '../services/notifications';
import { useAuth } from './AuthContext';

interface NotificationsContextProps {
    notifications: AppNotification[];
    unreadCount: number | null;
    isLoading: boolean;
    isRefreshing: boolean;
    hasMore: boolean;
    fetchNotifications: (page?: number, isRefresh?: boolean) => Promise<void>;
    // markAsRead: (notificationId: string) => Promise<void>; // FUTURE IMPLEMENTATION
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
            const data = await getNotifications(page, 20); // Domyślnie 20 powiadomień na stronę
            
            if (isRefresh || page === 1) {
                setNotifications(data.data);
            } else {
                setNotifications(prev => [...prev, ...data.data]);
            }
            
            // Paginacja i liczba nieprzeczytanych z response
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

    // Opcjonalne pobieranie po autoryzacji
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

    /*
    // FUTURE IMPLEMENTATION
    const markAsRead = async (notificationId: string) => {
        try {
            // await markNotificationAsRead(notificationId);
            // Zaktualizuj stan lokalnie, aby nie musieć fetchować ponownie
            setNotifications(prev => 
                prev.map(notif => 
                    notif.notification_id === notificationId 
                        ? { ...notif, is_read: true } 
                        : notif
                )
            );
            setUnreadCount(prev => prev && prev > 0 ? prev - 1 : 0);
        } catch (error) {
            console.error("Failed to mark notification as read", error);
        }
    };
    */

    return (
        <NotificationsContext.Provider value={{
            notifications,
            unreadCount,
            isLoading,
            isRefreshing,
            hasMore,
            fetchNotifications,
            // markAsRead
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
