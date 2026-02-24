import api from "./api";
import { Event } from "../types";


export interface EventData {
  name: string;
  description: string;
  date: string;
  time: string;
  location: string;
}

type CreateEventResponse = { message: string; event_id: string };
type ApiMessage = { message?: string };

export interface PaginatedEvents {
  data: Event[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

export const createEvent = async (eventData: EventData): Promise<CreateEventResponse> => {
  try {
    const response = await api.post<CreateEventResponse>(`/api/events/create`, eventData);
    return response.data;
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || "Network error";
    throw new Error(msg);
  }
};

export const deleteEvent = async (eventId: string): Promise<string> => {
  try {
    const response = await api.delete<ApiMessage>(`/api/events/delete/${eventId}`);
    return response.data.message ?? "Event deleted";
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || "Network error";
    throw new Error(msg);
  }
};

export const editEvent = async (
  eventId: string,
  eventData: Partial<EventData>
): Promise<string> => {
  try {
    const response = await api.put<ApiMessage>(`/api/events/edit/${eventId}`, eventData);
    return response.data.message ?? `Event ${eventId} edited`;
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || "Network error";
    throw new Error(msg);
  }
};

export const getEvents = async (page: number = 1, limit: number = 20): Promise<PaginatedEvents> => {
  try {
    const response = await api.get<PaginatedEvents>(`/api/events/feed`, { params: { page, limit } });
    return response.data;
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || "Network error";
    throw new Error(msg);
  }
};
