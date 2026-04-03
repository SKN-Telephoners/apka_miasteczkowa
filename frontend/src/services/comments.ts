import api from "./api";

type ApiMessage = { message?: string };

export const getComments = async (eventId: string) => {
    try {
        const response = await api.get(`api/comments/event/${eventId}`);
        return response.data;
    }
    // error handling 
    catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const createComment = async (eventId: string, content: string): Promise<string> => {
    try {
        const response = await api.post<ApiMessage>(`api/comments/create/${eventId}`, { content });
        return response.data.message ?? "Comment created";
    }
    // error handling 
    catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const editComment = async (commentId: string, content: string): Promise<string> => {
    try {
        const response = await api.post<ApiMessage>(`api/comments/edit/${commentId}`, {
            new_content: content
        });
        return response.data.message ?? "Comment edited";
    }
    // error handling 
    catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const deleteComment = async (commentId: string): Promise<string> => {
    try {
        const response = await api.delete<ApiMessage>(`api/comments/delete/${commentId}`);
        return response.data.message ?? "Comment deleted";// return, delete if unnecessary
    }
    // error handling 
    catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
};

export const replyToComment = async (parentCommentId: string, eventId: string, content: string): Promise<string> => {
    try {
        const response = await api.post<ApiMessage>(
            `api/comments/reply/${parentCommentId}`,
            { content: content },
            { headers: { event_id: eventId } }
        );
        return response.data.message ?? "Created a response";
    }
    // error handling 
    catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error";
        throw new Error(msg);
    }
}