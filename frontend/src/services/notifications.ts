import api from './api';

export interface NotificationPayload {
    message: string;
    [key: string]: any;
}

export interface AppNotification {
    notification_id: string;
    tag: string;
    is_read: boolean;
    date: string;
    time: string;
    payload: NotificationPayload;
}

export interface PaginationMeta {
    page: number;
    limit: number;
    total: number;
    pages: number;
    has_next: boolean;
    unread_count: number | null;
}

export interface GetNotificationsResponse {
    data: AppNotification[];
    pagination: PaginationMeta;
}

export const getNotifications = async (
    page: number = 1,
    limit: number = 20,
    status: 'unread' | 'read' | 'all' = 'all'
): Promise<GetNotificationsResponse> => {
    try {
        const response = await api.get('/notifications/', {
            params: {
                page,
                limit,
                status
            }
        });
        return response.data.data;
    } catch (error) {
        console.error('Error fetching notifications:', error);
        throw error;
    }
};

/**
 * FUTURE: Endpoint do oznaczania powiadomienia jako przeczytane.
 * Na ten moment zakomentowane ze względu na brak implementacji w backendzie.
 */
/*
export const markNotificationAsRead = async (notificationId: string): Promise<void> => {
    try {
        await api.put(`/notifications/${notificationId}/read`);
    } catch (error) {
        console.error(`Error marking notification ${notificationId} as read:`, error);
        throw error;
    }
};
*/
