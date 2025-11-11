import api from "./api";

type ApiMessage = { message?: string }; //type string insure for backend function response

interface EventData {
    name: string;
    description: string;
    date: string;
    time: string;
    location: string;
    // key = "name", "description", "date", "time", "location"
}

// Create event
export const createEvent = async(eventData: EventData) : Promise<string> =>{
    try {
        const response = await api.post<ApiMessage>('/create_event', eventData);
        return response.data.message ?? "Event created";// return, delete if unnecessary
        }
        // error handling 
         catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
        }
};

// Delete event 
export const deleteEvent = async(eventId: string) : Promise<string> =>{
    try {
        const response = await api.delete<ApiMessage>(`/delete_event/${eventId}`);
        return response.data.message ?? "Event deleted";// return, delete if unnecessary
        }
        // error handling 
         catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
        }
};