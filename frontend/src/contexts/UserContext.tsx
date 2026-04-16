import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { getUserProfile } from "../services/users";
import { userService } from "../services/api";
import { useAuth } from "./AuthContext";
import { MOCKS } from "../utils/constants";

export interface UserProfile {
  id: string; // Możemy na razie podmienić pod user_id z serwera
  user_id: string; // Alias dla bezproblemowego dopasowania isOwner w UserScreen
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
  joinedDate?: string;
}

interface UserContextType {
  user: UserProfile | null;
  isLoadingUser: boolean;
  fetchUser: () => Promise<void>;
  updateUserProfile: (data: any) => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, userId } = useAuth();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoadingUser, setIsLoadingUser] = useState(false);

  const fetchUser = useCallback(async () => {
    if (!isAuthenticated || !userId) {
      setUser(null);
      return;
    }

    setIsLoadingUser(true);
    try {
      // 1. Odbiór ORYGINAŁU z backendu
      const profileData = await getUserProfile(userId);

      // 2. Usunięcie MOCKOWANYCH danych i wstawienie danych z zapytania
      const nextUser = {
        id: profileData.user_id || "1",
        user_id: profileData.user_id || "1",
        username: profileData.username || "Nieznany", // Tymczasowy fallback jeśli czegoś brakuje
        email: profileData.email || "",
        description: profileData.description || "",
        profile_picture: profileData.profile_picture,
        academy: profileData.academy,
        faculty: profileData.faculty,
        course: profileData.course,
        year: profileData.year,
        academic_clubs: profileData.academic_clubs,
        joinedDate: "Marzec 2024" // TODO: Backend musi zwrócić created_at
      };

      setUser(nextUser as any);
    } catch (error) {
      console.error("Error fetching user profile:", error);
    } finally {
      setIsLoadingUser(false);
    }
  }, [isAuthenticated, userId]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const updateUserProfile = async (data: any) => {
    setIsLoadingUser(true);

    // Optymistyczny update, który natychmiast wymusza zmianę na ekranie:
    setUser((prev) => {
      if (!prev) return prev;
      const next = {
        ...prev,
        username: data.username !== undefined ? data.username : prev.username,
        description: data.description !== undefined ? data.description : prev.description,
        academy: data.academy !== undefined ? data.academy : prev.academy,
        faculty: data.faculty !== undefined ? data.faculty : prev.faculty,
        course: data.course !== undefined ? data.course : prev.course,
        year: data.year !== undefined ? data.year : prev.year,
      };
      return next;
    });

    try {
      await userService.updateProfile(data);

      if (data.academy === "AGH" && data.faculty && data.course && data.year) {
        await userService.updateAcademicDetails({
          faculty: data.faculty,
          course: data.course,
          year: Number(data.year)
        });
      }

      await fetchUser();
    } catch (error) {
      console.error("Błąd podczas aktualizacji profilu użytkownika:", error);
      throw error; // rzucamy błąd dalej, by mógł zostać złapany i wyświetlony przez komponent
    } finally {
      setIsLoadingUser(false);
    }
  };

  return (
    <UserContext.Provider value={{ user, isLoadingUser, fetchUser, updateUserProfile }}>
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
