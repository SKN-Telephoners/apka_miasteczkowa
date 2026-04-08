import api from "./api";
import { Event, EventPicture } from "../types";

type ApiMessage = { message?: string }; //type string insure for backend function response
type CreateEventResponse = { message: string; event_id: string; creator_id: string };

type EventPictureInput = EventPicture | null;
type UploadPictureResponse = {
    pictures?: Array<{
        cloud_id: string;
        picture_url?: string;
    }>;
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
        const formData = new FormData();
        formData.append("files", {
            uri,
            name: fileName,
            type: "image/jpeg",
        } as any);

        const response = await api.post<UploadPictureResponse>("api/pictures/upload-batch", formData, {
            headers: {
                "Content-Type": "multipart/form-data",
            },
        });

        const uploadedPicture = response.data.pictures?.[0];
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
        const response = await api.delete<ApiMessage>(`api/events/delete/${eventId}`);
        return response.data.message ?? "Event deleted";// return, delete if unnecessary
    }
    // error handling 
    catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const getEvents = async (page: number = 1, limit: number = 20): Promise<PaginatedEvents> => {
    try {
        const response = await api.get<PaginatedEvents>('api/events/feed', { params: { page, limit } });
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
        const response = await api.get<ParticipationStatusResponse>(`api/events/participation/${eventId}`);
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
        const response = await api.post<ApiMessage>(`api/events/join/${eventId}`);
        return response.data.message ?? "Joined event successfully";
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const leaveEvent = async (eventId: string): Promise<string> => {
    try {
        const response = await api.delete<ApiMessage>(`api/events/leave/${eventId}`);
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