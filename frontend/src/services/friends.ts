import api from "./api";

import { User, Request } from '../types/friends';

type ApiMessage = { message?: string }; //type string insure for backend function response

export interface FriendsDataResponse {
  friends: User[];
  incomingRequests: Request[];
  outgoingRequests: Request[];
}

// Function to get the friends list
export const getFriendsList = async (): Promise<FriendsDataResponse> => {
  try {
    const response = await api.get<{ message?: string; data: { friends: User[] } }>('/api/friends/list');
    return {
      friends: response.data?.data?.friends || [],
      incomingRequests: [], // MOCK: Backend nie ma jeszcze endpointu na prośby
      outgoingRequests: []  // MOCK: Backend nie ma jeszcze endpointu na prośby
    };
  }catch (err: any){
    //error handling for now
    const msg = err?.response?.data?.message || err?.message || "Network error"
    throw new Error(msg)
  }
}

// Function to search users - move do correct spot 
export const searchUsers = async (query: string): Promise<User[]> => {
  try {
    const response = await api.get<User[]>('/api/users/search', { params: { q: query } });
    return response.data;
  } catch (err) {
    console.warn("Wyszukiwanie znajomych nie jest jeszcze zaimplementowane w backendzie");
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

