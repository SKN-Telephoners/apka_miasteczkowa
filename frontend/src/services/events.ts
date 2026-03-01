import api from "./api";
import { Event } from "../types";

type ApiMessage = { message?: string }; //type string insure for backend function response
type CreateEventResponse = { message: string; event_id: string };

interface EventData {
    name: string;
    description: string;
    date: string;
    time: string;
    location: string;
    // key = "name", "description", "date", "time", "location"
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

// Create event
export const createEvent = async(eventData: EventData) : Promise<CreateEventResponse> =>{ // check promise
    try {
        const response = await api.post<CreateEventResponse>('/create', eventData);
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
        const response = await api.delete<ApiMessage>(`/delete/${eventId}`);
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
        const response = await api.get<PaginatedEvents>('/feed', { params: { page, limit } });
        return response.data;
    }
    // error handling 
    catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

// Edit event for now - to change
export const editEvent = async (eventId: string, data: EventData): Promise<string> => {
    try {
        const response = await api.put<ApiMessage>(`/edit/${eventId}`, data);
        return response.data.message ?? "Event Edited";
    } catch (err: any){
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
}