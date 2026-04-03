import api from "./api";
import { Event } from "../types";

type ApiMessage = { message?: string }; //type string insure for backend function response
type CreateEventResponse = { message: string; event_id: string; creator_id: string };

export interface CreateEventData {
    name: string;
    description: string;
    date: string;
    time: string;
    location: string;
    is_private: boolean;
    // key = "name", "description", "date", "time", "location"
}

export interface EditEventData {
    name?: string;
    description?: string;
    date?: string;
    time?: string;
    location?: string;
    is_private?: boolean;
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
        const response = await api.post<CreateEventResponse>('api/events/create', eventData);
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
        const response = await api.put<ApiMessage>(`api/events/edit/${eventId}`, data);
        return response.data.message ?? "Event Edited";
    } catch (err: any){
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
}