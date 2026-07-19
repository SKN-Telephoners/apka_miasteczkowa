import React, { createContext, useCallback, useContext, useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import * as friendsService from "../services/friends";
import { Request, User } from "../types/friends";

interface FriendsContextType {
  friends: User[];
  incomingRequests: Request[];
  outgoingRequests: Request[];
  loading: boolean;
  error: string | null;
  fetchFriends: () => Promise<void>;
  sendFriendRequest: (userId: string) => Promise<void>;
  acceptRequest: (requestId: string) => Promise<void>;
  declineRequest: (requestId: string) => Promise<void>;
  removeFriend: (friendId: string) => Promise<void>;
  searchUsers: (query: string) => Promise<User[]>; // Akcja zwracająca wynik
}

const FriendsContext = createContext<FriendsContextType | undefined>(undefined);

const FRIENDS_KEY = ["friends"] as const;
const PENDING_REQUESTS_KEY = ["friend-requests", "pending"] as const;

export const FriendsProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const queryClient = useQueryClient();

  const friendsQuery = useQuery({
    queryKey: FRIENDS_KEY,
    queryFn: friendsService.getFriendsList,
  });

  const pendingQuery = useQuery({
    queryKey: PENDING_REQUESTS_KEY,
    queryFn: friendsService.getPendingRequests,
  });

  const friends = friendsQuery.data?.friends ?? [];
  const incomingRequests =
    pendingQuery.data?.incomingRequests ?? friendsQuery.data?.incomingRequests ?? [];
  const outgoingRequests =
    pendingQuery.data?.outgoingRequests ?? friendsQuery.data?.outgoingRequests ?? [];

  const loading = friendsQuery.isFetching || pendingQuery.isFetching;
  const error = (friendsQuery.error as any)?.message || (pendingQuery.error as any)?.message || null;

  const fetchFriends = useCallback(async () => {
    await Promise.all([friendsQuery.refetch(), pendingQuery.refetch()]);
  }, [friendsQuery.refetch, pendingQuery.refetch]);

  const invalidateFriendsData = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: FRIENDS_KEY });
    queryClient.invalidateQueries({ queryKey: PENDING_REQUESTS_KEY });
  }, [queryClient]);

  const sendFriendRequestMutation = useMutation({
    mutationFn: friendsService.addFriend,
    onMutate: async (userId: string) => {
      const tempRequest: Request = {
        id: `temp_${Date.now()}`,
        senderId: "",
        receiverId: userId,
        createdAt: new Date().toISOString(),
        user: { id: userId, username: "Wysyłanie...", email: "" } as User,
      };
      queryClient.setQueryData(PENDING_REQUESTS_KEY, (prev: any) => ({
        incomingRequests: prev?.incomingRequests ?? [],
        outgoingRequests: [...(prev?.outgoingRequests ?? []), tempRequest],
      }));
    },
    onSettled: invalidateFriendsData,
  });

  const acceptRequestMutation = useMutation({
    mutationFn: friendsService.acceptFriend,
    onSettled: invalidateFriendsData,
  });

  const declineRequestMutation = useMutation({
    mutationFn: friendsService.rejectFriend,
    onSettled: invalidateFriendsData,
  });

  const removeFriendMutation = useMutation({
    mutationFn: friendsService.removeFriend,
    onSettled: invalidateFriendsData,
  });

  const sendFriendRequest = useCallback(
    async (userId: string) => {
      await sendFriendRequestMutation.mutateAsync(userId);
    },
    [sendFriendRequestMutation],
  );

  const acceptRequest = useCallback(
    async (requestId: string) => {
      await acceptRequestMutation.mutateAsync(requestId);
    },
    [acceptRequestMutation],
  );

  const declineRequest = useCallback(
    async (requestId: string) => {
      await declineRequestMutation.mutateAsync(requestId);
    },
    [declineRequestMutation],
  );

  const removeFriend = useCallback(
    async (friendId: string) => {
      await removeFriendMutation.mutateAsync(friendId);
    },
    [removeFriendMutation],
  );

  const searchUsers = useCallback(async (query: string): Promise<User[]> => {
    try {
      return await friendsService.searchUsers(query);
    } catch (err) {
      console.error("Error searching users:", err);
      return [];
    }
  }, []);

  const contextValue = useMemo(
    () => ({
      friends,
      incomingRequests,
      outgoingRequests,
      loading,
      error,
      fetchFriends,
      sendFriendRequest,
      acceptRequest,
      declineRequest,
      removeFriend,
      searchUsers,
    }),
    [
      friends,
      incomingRequests,
      outgoingRequests,
      loading,
      error,
      fetchFriends,
      sendFriendRequest,
      acceptRequest,
      declineRequest,
      removeFriend,
      searchUsers,
    ],
  );

  return (
    <FriendsContext.Provider value={contextValue}>
      {children}
    </FriendsContext.Provider>
  );
};

export const useFriends = () => {
  const context = useContext(FriendsContext);
  if (context === undefined) {
    throw new Error("useFriends must be used within a FriendsProvider");
  }
  return context;
};
