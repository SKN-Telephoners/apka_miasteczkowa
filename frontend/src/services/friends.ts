import api from "./api";

import { User, Request } from '../types/friends';

type ApiMessage = { message?: string }; //type string insure for backend function response

export interface FriendsDataResponse {
  friends: User[];
  incomingRequests: Request[];
  outgoingRequests: Request[];
}

export const getFriendsList = async (): Promise<FriendsDataResponse> => {
  try {
    const response = await api.get<{ message?: string; friends: User[]; incomingRequests: Request[]; outgoingRequests: Request[] }>('/api/friends/list');
    return {
      friends: response.data?.friends || [],
      incomingRequests: response.data?.incomingRequests || [],
      outgoingRequests: response.data?.outgoingRequests || []
    };
  } catch (err: any) {
    //error handling for now
    const msg = err?.response?.data?.message || err?.message || "Network error"
    throw new Error(msg)
  }
}

// Function to search users - move do correct spot 
export const searchUsers = async (query: string): Promise<User[]> => {
  try {
    const response = await api.get<{ users: any[] }>('/api/users/users_list', {
      params: { search: query, limit: 20 }
    });
    
    return response.data?.users?.map(u => ({
      id: u.user_id,
      username: u.username,
      email: "", // publiczna szukajka raczej tego nie zdradzi
      academy: u.academy,
      faculty: u.faculty,
      course: u.course,
      year: u.year,
      avatarUrl: u.profile_picture?.url || u.profile_picture || undefined,
      profile_picture: u.profile_picture || null,
      is_friend: u.is_friend
    })) as User[];
  } catch (err) {
    console.warn("Wyszukiwanie użytkowników zwróciło wyjątek:", err);
    return [];
  }
};

// Function to send a friend request
export const addFriend = async (friendId: string): Promise<string> => {
  try {
    // post /create_friend_request/:friendId{string}
    const response = await api.post<ApiMessage>(`/api/friends/request/${friendId}/create`);
    return response.data.message ?? "Friend request created";
  } catch (err: any) {
    // error handling for now
    const msg = err?.response?.data?.message || err?.message || "Network error";
    throw new Error(msg);
  }
};

// Function to accept a friend request
export const acceptFriend = async (friendId: string): Promise<string> => {
  try {
    const response = await api.post<ApiMessage>(`/api/friends/request/${friendId}/accept`);
    return response.data.message ?? "Friend request accepted";
  } catch (err: any) {
    // error handling for now
    const msg = err?.response?.data?.message || err?.message || "Network error";
    throw new Error(msg);
  }
};
// Function to reject a friend request
export const rejectFriend = async (friendId: string): Promise<string> => {
  try {
    const response = await api.post<ApiMessage>(`/api/friends/request/${friendId}/decline`);
    return response.data.message ?? "Friend request rejected";
  } catch (err: any) {
    // error handling for now
    const msg = err?.response?.data?.message || err?.message || "Network error";
    throw new Error(msg);
  }
};
// Function to cancel friend request
export const cancelRequest = async (friendId: string): Promise<string> => {
  try {
    const response = await api.post<ApiMessage>(`/api/friends/request/${friendId}/cancel`);
    return response.data.message ?? "Friend request canceled";
  } catch (err: any) {
    // error handling for now
    const msg = err?.response?.data?.message || err?.message || "Network error";
    throw new Error(msg);
  }
}

// Function to remove a friend
export const removeFriend = async (friendId: string): Promise<string> => {
  try {
    const response = await api.post<ApiMessage>(`/api/friends/${friendId}/remove`);
    return response.data.message ?? "Friend removed";
  } catch (err: any) {
    // error handling for now
    const msg = err?.response?.data?.message || err?.message || "Network error";
    throw new Error(msg);
  }
}

// Function to fetch pending requests
export const getPendingRequests = async (): Promise<{incomingRequests: Request[], outgoingRequests: Request[]}> => {
    try {
        const response = await api.get<{ data: { incoming_pending_requests: any[], outgoing_pending_requests: any[]} }>('/api/friends/request/pending');
        
        const mapToRequest = (req: any, isOutgoing: boolean): Request => ({
            id: req.request_id,
            senderId: isOutgoing ? "" : req.sender_id,
            receiverId: isOutgoing ? req.receiver_id : "",
            createdAt: req.requested_at,
            user: {
                id: isOutgoing ? req.receiver_id : req.sender_id,
                username: isOutgoing ? req.receiver_username : req.sender_username,
                email: "",
            } as User
        });

        return {
            incomingRequests: (response.data.data?.incoming_pending_requests || []).map((req: any) => mapToRequest(req, false)),
            outgoingRequests: (response.data.data?.outgoing_pending_requests || []).map((req: any) => mapToRequest(req, true))
        };
    } catch (err: any) {
        const msg = err?.response?.data?.message || err?.message || "Network error"
        throw new Error(msg)
    }
}
