import api from "./api";

export const getComments = async (eventId: string) => {
    try {
        const response = await api.get(`/get_comments_list/${eventId}`);
        return response.data;
    }
    // error handling 
    catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};