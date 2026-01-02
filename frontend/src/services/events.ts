import api from "./api";

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

// Create event
export const createEvent = async(eventData: EventData) : Promise<CreateEventResponse> =>{ // check promise
    try {
        const response = await api.post<CreateEventResponse>('/create_event', eventData);
        return response.data;
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