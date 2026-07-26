import React, { createContext, useContext, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getUserProfile } from "../services/users";
import { userService } from "../services/api";
import { useAuth } from "./AuthContext";

export interface UserProfile {
  id: string;
  user_id: string;
  username: string;
  email: string;
  description?: string;
  profile_picture?: {
    cloud_id: string;
    url: string;
  };
  academy?: string;
  faculty?: string;
  course?: string;
  year?: number;
  academic_clubs?: string[];
  created_at?: string;
}

interface UserContextType {
  user: UserProfile | null;
  isLoadingUser: boolean;
  fetchUser: () => Promise<void>;
  updateUserProfile: (data: any) => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

const mapProfile = (profileData: any): UserProfile => ({
  id: profileData.user_id || "1",
  user_id: profileData.user_id || "1",
  username: profileData.username || "Nieznany",
  email: profileData.email || "",
  description: profileData.description || "",
  profile_picture: profileData.profile_picture,
  academy: profileData.academy,
  faculty: profileData.faculty,
  course: profileData.course,
  year: profileData.year,
  academic_clubs: profileData.academic_clubs,
  created_at: profileData.created_at || "", 
});

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, userId } = useAuth();
  const queryClient = useQueryClient();

  const userQueryKey = ["user", userId] as const;

  const { data: user, isLoading: isLoadingUser, refetch } = useQuery({
    queryKey: userQueryKey,
    queryFn: async () => mapProfile(await getUserProfile(userId as string)),
    enabled: isAuthenticated && !!userId,
  });

  const fetchUser = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const mutation = useMutation({
    mutationFn: async (data: any) => {
      await userService.updateProfile(data);
      if (data.academy === "AGH" && data.faculty && data.course && data.year) {
        await userService.updateAcademicDetails({
          faculty: data.faculty,
          course: data.course,
          year: Number(data.year),
        });
      }
    },
    onMutate: async (data: any) => {
      await queryClient.cancelQueries({ queryKey: userQueryKey });
      const previousUser = queryClient.getQueryData<UserProfile>(userQueryKey);
      queryClient.setQueryData<UserProfile | undefined>(userQueryKey, (prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          username: data.username !== undefined ? data.username : prev.username,
          description: data.description !== undefined ? data.description : prev.description,
          academy: data.academy !== undefined ? data.academy : prev.academy,
          faculty: data.faculty !== undefined ? data.faculty : prev.faculty,
          course: data.course !== undefined ? data.course : prev.course,
          year: data.year !== undefined ? data.year : prev.year,
        };
      });
      return { previousUser };
    },
    onError: (_err, _data, context) => {
      if (context?.previousUser) {
        queryClient.setQueryData(userQueryKey, context.previousUser);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: userQueryKey });
    },
  });

  const updateUserProfile = useCallback(
    async (data: any) => {
      await mutation.mutateAsync(data);
    },
    [mutation],
  );

  return (
    <UserContext.Provider
      value={{
        user: user ?? null,
        isLoadingUser: isLoadingUser || mutation.isPending,
        fetchUser,
        updateUserProfile,
      }}
    >
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error("useUser musi być użyty wewnątrz UserProvider");
  }
  return context;
};