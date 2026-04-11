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

// Function to search users
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
      avatarUrl: u.profile_picture || undefined,
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

