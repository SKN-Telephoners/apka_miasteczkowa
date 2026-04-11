import api from "./api";
import { Event, EventPicture } from "../types";
import { API_BASE_URL } from "../utils/constants";
import { tokenStorage } from "../utils/storage";

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
        const accessToken = await tokenStorage.getAccessToken();

        if (!accessToken) {
            throw new Error("Brak tokenu dostępu. Zaloguj się ponownie.");
        }

        const formData = new FormData();
        const filePayload = {
            uri,
            name: derivedName,
            type: mimeType,
        } as any;
        formData.append("file", filePayload);
        formData.append("tags", "event-picture");

        const response = await fetch(`${API_BASE_URL}/api/pictures/upload`, {
            method: "POST",
            headers: {
                Authorization: `Bearer ${accessToken}`,
            },
            body: formData,
        });

        let responseData: UploadPictureResponse = {};
        try {
            responseData = (await response.json()) as UploadPictureResponse;
        } catch {
            responseData = {};
        }

        if (!response.ok) {
            throw new Error((responseData as any)?.message || `Upload failed (${response.status})`);
        }
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