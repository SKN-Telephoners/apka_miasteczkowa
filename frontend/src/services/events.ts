import api from "./api";
import { Event, EventPicture } from "../types";

type ApiMessage = { message?: string }; //type string insure for backend function response
type CreateEventResponse = { message: string; event_id: string; creator_id: string };

type EventPictureInput = EventPicture | null;
type UploadPictureResponse = {
    cloud_id?: string;
    public_id?: string;
    clout_id?: string;
    picture_url?: string;
    pictures?: Array<{
        cloud_id: string;
        public_id?: string;
        picture_url?: string;
    }>;
    data?: {
        cloud_id?: string;
        public_id?: string;
        clout_id?: string;
        picture_url?: string;
        pictures?: Array<{
            cloud_id: string;
            public_id?: string;
            picture_url?: string;
        }>;
    };
};

const normalizePictures = (
    pictures?: EventPictureInput[] | EventPictureInput | null,
): EventPicture[] | undefined => {
    if (!pictures) {
        return undefined;
    }

    const pictureList = Array.isArray(pictures) ? pictures : [pictures];
    const normalizedPictures = pictureList
        .filter((picture): picture is EventPicture => Boolean(picture && picture.cloud_id))
        .map((picture) => ({ cloud_id: picture.cloud_id }));

    return normalizedPictures.length > 0 ? normalizedPictures : undefined;
};

export const uploadEventPicture = async (uri: string, fileName = "event-picture.jpg") : Promise<EventPicture> => {
    try {
        const derivedName = fileName || uri.split("/").pop() || "event-picture.jpg";
        const ext = derivedName.split(".").pop()?.toLowerCase();
        const mimeType = ext === "png" ? "image/png" : ext === "webp" ? "image/webp" : "image/jpeg";

        const formData = new FormData();
        const filePayload = {
            uri,
            name: derivedName,
            type: mimeType,
        } as any;
        formData.append("file", filePayload);
        formData.append("tags", "event-picture");

        const response = await api.post<UploadPictureResponse>("/api/pictures/upload", formData);
        const responseData: UploadPictureResponse = response.data || {};

        const uploadedPicture =
            responseData.pictures?.[0]
            ?? responseData.data?.pictures?.[0]
            ?? (responseData.cloud_id ? { cloud_id: responseData.cloud_id, picture_url: responseData.picture_url } : undefined)
            ?? (responseData.public_id ? { cloud_id: responseData.public_id, picture_url: responseData.picture_url } : undefined)
            ?? (responseData.clout_id ? { cloud_id: responseData.clout_id, picture_url: responseData.picture_url } : undefined)
            ?? (responseData.data?.cloud_id ? { cloud_id: responseData.data.cloud_id, picture_url: responseData.data.picture_url } : undefined)
            ?? (responseData.data?.public_id ? { cloud_id: responseData.data.public_id, picture_url: responseData.data.picture_url } : undefined)
            ?? (responseData.data?.clout_id ? { cloud_id: responseData.data.clout_id, picture_url: responseData.data.picture_url } : undefined);

        if (!uploadedPicture?.cloud_id) {
            console.log("Upload response (missing cloud_id):", JSON.stringify(responseData));
        }

        if (!uploadedPicture?.cloud_id) {
            throw new Error("Upload picture failed");
        }

        return {
            cloud_id: uploadedPicture.cloud_id,
            url: uploadedPicture.picture_url,
        };
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export interface CreateEventData {
    name: string;
    description: string;
    date: string;
    time: string;
    location: string;
    is_private: boolean;
    picture?: EventPictureInput;
    pictures?: EventPictureInput[] | EventPictureInput | null;
    // key = "name", "description", "date", "time", "location"
}

export interface EditEventData {
    name?: string;
    description?: string;
    date?: string;
    time?: string;
    location?: string;
    is_private?: boolean;
    picture?: EventPictureInput;
    pictures?: EventPictureInput[] | EventPictureInput | null;
}

export interface PaginatedEvents {
    data: Event[];
    pagination: {
        page: number;
        limit: number;
        total: number;
        pages: number;
    };
}

export interface MapEventsResponse {
    data: Event[];
}

export interface FeedQueryParams {
    q?: string;
    visibility?: "all" | "public" | "private";
    participation?: "all" | "joined" | "not_joined";
    created_window?: "all" | "today" | "week" | "month" | "year" | "older";
    sort_mode?: "default" | "members_desc" | "members_asc" | "comments_desc" | "comments_asc";
    creator_source?: "all" | "friends" | "others";
}

export interface ParticipationStatusResponse {
    is_participating: boolean;
    participant_count: number;
}

export interface EventInviteNotification {
    id: string;
    createdAt?: string | null;
    inviter: {
        id: string;
        username: string;
        email?: string;
        academy?: string | null;
        course?: string | null;
        avatarUrl?: string;
        profile_picture?: { cloud_id: string; url: string } | null;
    };
    event: Event;
}

// Create event
export const createEvent = async(eventData: CreateEventData) : Promise<CreateEventResponse> =>{ // check promise
    try {
        const { picture, pictures, ...baseData } = eventData;
        const normalizedPictures = normalizePictures(pictures ?? picture);

        const response = await api.post<CreateEventResponse>('api/events/create', {
            ...baseData,
            ...(normalizedPictures ? { pictures: normalizedPictures } : {}),
        });
        return response.data;
        }
        // error handling 
         catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

// Delete event 
export const deleteEvent = async (eventId: string): Promise<string> => {
    try {
        const response = await api.delete<ApiMessage>(`/api/events/delete/${eventId}`);
        return response.data.message ?? "Event deleted";// return, delete if unnecessary
    }
    // error handling 
    catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const getEvents = async (
    page: number = 1,
    limit: number = 20,
    query: FeedQueryParams = {},
): Promise<PaginatedEvents> => {
    try {
        const response = await api.get<PaginatedEvents>('api/events/feed', {
            params: {
                page,
                limit,
                ...(query.q ? { q: query.q } : {}),
                ...(query.visibility ? { visibility: query.visibility } : {}),
                ...(query.participation ? { participation: query.participation } : {}),
                ...(query.created_window ? { created_window: query.created_window } : {}),
                ...(query.sort_mode ? { sort_mode: query.sort_mode } : {}),
                ...(query.creator_source ? { creator_source: query.creator_source } : {}),
            },
        });
        return response.data;
    }
    // error handling 
    catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const getMapEvents = async (): Promise<Event[]> => {
    try {
        const response = await api.get<MapEventsResponse>("/api/events/map");
        return response.data.data || [];
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const getParticipationStatus = async (eventId: string): Promise<ParticipationStatusResponse> => {
    try {
        const response = await api.get<ParticipationStatusResponse>(`/api/events/participation/${eventId}`);
        return {
            is_participating: response.data.is_participating,
            participant_count: Number(response.data.participant_count ?? 0),
        };
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const getUserCreatedEvents = async (userId: string): Promise<Event[]> => {
    try {
        const response = await api.get<{ data: any[] }>(`/api/events/${userId}/creator`);
        return (response.data.data || []).map(event => ({
            ...event,
            id: event.id || event.event_id,
            participant_count: event.participant_count ?? event.participation_count
        })) as Event[];
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Błąd pobierania utworzonych wydarzeń użytkownika";
        throw new Error(msg);
    }
};

export const getUserParticipatingEvents = async (userId: string): Promise<Event[]> => {
    try {
        const response = await api.get<{ data: any[] }>(`/api/events/${userId}/participant`);
        return (response.data.data || []).map(event => ({
            ...event,
            id: event.id || event.event_id,
            participant_count: event.participant_count ?? event.participation_count
        })) as Event[];
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Błąd pobierania wydarzeń, w których użytkownik bierze udział";
        throw new Error(msg);
    }
};

export const joinEvent = async (eventId: string): Promise<string> => {
    try {
        const response = await api.post<ApiMessage>(`/api/events/join/${eventId}`);
        return response.data.message ?? "Joined event successfully";
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const leaveEvent = async (eventId: string): Promise<string> => {
    try {
        const response = await api.delete<ApiMessage>(`/api/events/leave/${eventId}`);
        return response.data.message ?? "Left event successfully";
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const inviteToEvent = async (eventId: string, invitedUserId: string): Promise<string> => {
    try {
        const response = await api.post<ApiMessage>(`/api/events/invite/${eventId}`, {
            invited: invitedUserId,
        });
        return response.data.message ?? "Invite created successfully";
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const deleteInviteToEvent = async (eventId: string, invitedUserId: string): Promise<string> => {
    try {
        const response = await api.delete<ApiMessage>(`/api/events/delete_invite/${eventId}`, {
            data: {
                invited: invitedUserId,
            },
        });
        return response.data.message ?? "Invite deleted successfully";
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const getSentInvitesForEvent = async (eventId: string): Promise<string[]> => {
    try {
        const response = await api.get<{ invited_ids?: string[] }>(`/api/events/invites/${eventId}`);
        const invitedIds = response.data?.invited_ids;
        return Array.isArray(invitedIds) ? invitedIds : [];
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const getIncomingEventInvites = async (): Promise<EventInviteNotification[]> => {
    try {
        const response = await api.get<{ 
            data?: Array<{
                notification_id: string;
                type: string;
                payload: {
                    invite_id: string;
                    sender_id: string;
                    sender_name: string;
                    event_id: string;
                    event_name: string;
                    message: string;
                };
                date: string;
                time: string;
            }>
        }>("/api/notifications/?type=event_invite&status=all");

        const notifications = response.data?.data;
        if (!Array.isArray(notifications)) return [];

        return notifications.map(notif => ({
            id: notif.payload.invite_id,
            createdAt: `${notif.date} ${notif.time}`,
            inviter: {
                id: notif.payload.sender_id,
                username: notif.payload.sender_name,
                academy: undefined,
                course: undefined,
            },
            event: {
                id: notif.payload.event_id,
                name: notif.payload.event_name,
                description: "",
                location: "",
                date: notif.date,
                time: notif.time,
                creator_id: notif.payload.sender_id,
                is_private: false,
                comment_count: 0,
                participant_count: 0,
            }
        }));
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};


export const changeInviteStatus = async (inviteId: string, status: "accepted" | "declined"): Promise<string> => {
    try {
        const response = await api.post<ApiMessage>(`/api/events/change_invite_status/${inviteId}`, { status });
        return response.data.message ?? "Invite status changed successfully";
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

// Edit event for now - to change
export const editEvent = async (eventId: string, data: EditEventData): Promise<string> => {
    try {
        const { picture, pictures, ...baseData } = data;
        const normalizedPictures = normalizePictures(pictures ?? picture);
        const hasExplicitPictureField = Object.prototype.hasOwnProperty.call(data, "picture")
            || Object.prototype.hasOwnProperty.call(data, "pictures");

        const response = await api.put<ApiMessage>(`api/events/edit/${eventId}`, {
            ...baseData,
            ...(normalizedPictures ? { pictures: normalizedPictures } : hasExplicitPictureField ? { pictures: [] } : {}),
        });
        return response.data.message ?? "Event Edited";
    } catch (err: any){
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
}