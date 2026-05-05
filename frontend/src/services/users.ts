import api from "./api";
import { User } from "../types/friends";

export interface UserSearchPagination {
  total: number;
  pages: number;
  current_page: number;
}

export interface UserSearchResponse {
  users: User[];
  pagination: UserSearchPagination;
}

export const searchUsersByUsername = async (
  search: string,
  page: number = 1,
  limit?: number,
): Promise<UserSearchResponse> => {
  try {
    const response = await api.get<UserSearchResponse>("/api/users/users_list", {
      params: {
        search,
        page,
        ...(typeof limit === "number" ? { limit } : {}),
      },
    });

    const users = (response.data?.users || []).map((user: any) => ({
      id: user.user_id,
      username: user.username,
      email: "",
      academy: user.academy,
      faculty: user.faculty,
      course: user.course,
      year: user.year,
      avatarUrl: user.profile_picture?.url || undefined,
      profile_picture: user.profile_picture || null,
      is_friend: user.is_friend,
      is_self: user.is_self,
    }));

    return {
      users,
      pagination: response.data?.pagination || {
        total: 0,
        pages: 0,
        current_page: page,
      },
    };
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || "Network error";
    throw new Error(msg);
  }
};

// Odpowiedź z /api/users/profile wygląda tak:
// { "status": "success", "data": { "user_id": "...", "username": "...", "email": "..." } }

interface GetUserResponse {
  data: {
    user_id: string;
    username: string;
    email: string;
    description: string | null;
    profile_picture: { cloud_id: string; url: string } | null;
    academy: string | null;
    faculty: string | null;
    course: string | null;
    year: number | null;
    academic_clubs: string[] | null;
    created_at: string;
  };
}

export const getUserProfile = async (userId: string) => {
  try {
    const ts = new Date().getTime();
    const response = await api.get(`/api/users/profile/${userId}?t=${ts}`);
    return response.data;
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || "Błąd pobierania profilu";
    throw new Error(msg);
  }
};

export const getPublicUserProfile = async (userId: string) => {
  try {
    const response = await api.get(`/api/users/public_profile/${userId}`);
    return response.data;
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || "Błąd pobierania profilu użytkownika";
    throw new Error(msg);
  }
};

export const deleteAccount = async (): Promise<void> => {
  try {
    await api.delete("/api/users/settings/delete_account");
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || "Błąd podczas usuwania konta";
    throw new Error(msg);
  }
};
