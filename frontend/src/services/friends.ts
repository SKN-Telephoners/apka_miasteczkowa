import api from "./api";

import { User, Request } from '../types/friends';

type ApiMessage = { message?: string }; //type string insure for backend function response

export interface FriendsDataResponse {
  friends: User[];
  incomingRequests: Request[];
  outgoingRequests: Request[];
}

// Function to get the friends list
export const getFriendsList = async (): Promise<any> => {
  return null;
  //TO-DO: impement in backend
}

// Function to search users
export const searchUsers = async (query: string): Promise<User[]> => {
  const response = await api.get<User[]>('/users/search', { params: { q: query } });
  return response.data;
};

// Function to send a friend request
export const addFriend = async (friendId: string): Promise<string> => {
  try {
    // post /create_friend_request/:friendId{string}
    const response = await api.post<ApiMessage>(`/create_friend_request/${friendId}`);
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
    const response = await api.post<ApiMessage>(`/accept_friend_request/${friendId}`);
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
    const response = await api.post<ApiMessage>(`/reject_friend_request/${friendId}`);
    return response.data.message ?? "Friend request rejected";
  } catch (err: any) {
    // error handling for now
    const msg = err?.response?.data?.message || err?.message || "Network error";
    throw new Error(msg);
  }
};