import { AppNotification, AggregatedNotification } from '../services/notifications';

const AGGREGATABLE_TAGS = [
    'event-new-participant',
    'event-new-comment',
    'comment-reply-created',
];

const getAggregatedMessage = (tag: string, names: string[], eventName: string): string => {
    const uniqueNames = Array.from(new Set(names));
    const count = uniqueNames.length;

    let subject = '';
    if (count === 1) {
        subject = uniqueNames[0];
    } else if (count === 2) {
        subject = `${uniqueNames[0]} i ${uniqueNames[1]}`;
    } else {
        subject = `${uniqueNames[0]} i ${count - 1} innych`;
    }

    switch (tag) {
        case 'event-new-participant':
            return count === 1
                ? `${subject} dołączył(a) do twojego wydarzenia ${eventName}.`
                : `${subject} dołączyli do twojego wydarzenia ${eventName}.`;
        case 'event-new-comment':
            return count === 1
                ? `${subject} skomentował(a) twoje wydarzenie ${eventName}.`
                : `${subject} skomentowali twoje wydarzenie ${eventName}.`;
        case 'comment-reply-created':
            return count === 1
                ? `${subject} odpowiedział(a) na twój komentarz w wydarzeniu ${eventName}.`
                : `${subject} odpowiedzieli na twój komentarz w wydarzeniu ${eventName}.`;
        default:
            return `${subject} wygenerował(a) nowe powiadomienie dla wydarzenia ${eventName}.`;
    }
};

const getNameFromPayload = (tag: string, payload: any): string | null => {
    switch (tag) {
        case 'event-new-participant': return payload.participant_name;
        case 'event-new-comment': return payload.commenter_name;
        case 'comment-reply-created': return payload.replier_name;
        default: return null;
    }
};

export const aggregateNotifications = (notifications: AppNotification[]): AggregatedNotification[] => {
    const groups: Record<string, AppNotification[]> = {};
    const result: AggregatedNotification[] = [];

    notifications.forEach(notif => {
        if (AGGREGATABLE_TAGS.includes(notif.tag) && notif.payload.event_id) {
            const key = `${notif.tag}_${notif.payload.event_id}`;
            if (!groups[key]) {
                groups[key] = [];
            }
            groups[key].push(notif);
        } else {
            result.push({
                ...notif,
                aggregated_ids: [notif.notification_id],
                count: 1,
                raw_notifications: [notif],
            });
        }
    });

    Object.values(groups).forEach(group => {
        if (group.length === 1) {
            const notif = group[0];
            result.push({
                ...notif,
                aggregated_ids: [notif.notification_id],
                count: 1,
                raw_notifications: [notif],
            });
        } else if (group.length > 1) {
            group.sort((a, b) => {
                const dateA = new Date(`${a.date}T${a.time}`);
                const dateB = new Date(`${b.date}T${b.time}`);
                return dateB.getTime() - dateA.getTime();
            });

            const latestNotif = group[0];
            const tag = latestNotif.tag;
            const eventName = latestNotif.payload.event_name || 'Nieznane wydarzenie';

            const names = group
                .map(n => getNameFromPayload(tag, n.payload))
                .filter(Boolean) as string[];

            const isRead = group.every(n => n.is_read);

            result.push({
                ...latestNotif,
                is_read: isRead,
                notification_id: `agg_${tag}_${latestNotif.payload.event_id}`,
                aggregated_ids: group.map(n => n.notification_id),
                count: group.length,
                raw_notifications: group,
                payload: {
                    ...latestNotif.payload,
                    message: getAggregatedMessage(tag, names, eventName),
                }
            });
        }
    });

    result.sort((a, b) => {
        const dateA = new Date(`${a.date}T${a.time}`);
        const dateB = new Date(`${b.date}T${b.time}`);
        return dateB.getTime() - dateA.getTime();
    });

    return result;
};
