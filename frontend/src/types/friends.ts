export type User = {
  id: string;
  username: string;
  email: string;
  avatarUrl?: string; // idk
  academy?: string | null;
  faculty?: string | null;
  course?: string | null;
  year?: number | null;
  is_friend?: boolean;
  profile_picture?: { cloud_id: string; url: string } | null;
};

export type Request = {
  id: string; // ID zaproszenia
  senderId: string;
  receiverId: string;
  createdAt: string; // Data wysłania zaproszenia
  user: User;
};

export interface FriendsContextType {
  // Stan
  friends: User[];
  incomingRequests: Request[];
  outgoingRequests: Request[];
  loading: boolean;
  error: string | null;

  // Akcje
  fetchFriends: () => Promise<void>;
  sendFriendRequest: (userId: string) => Promise<void>;
  acceptRequest: (requestId: string) => Promise<void>;
  declineRequest: (requestId: string) => Promise<void>;
  searchUsers: (query: string) => Promise<User[]>;
}