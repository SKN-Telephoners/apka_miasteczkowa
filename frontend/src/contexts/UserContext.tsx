import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { getUserProfile } from "../services/users";
import { useAuth } from "./AuthContext";
import { MOCKS } from "../utils/constants";

export interface UserProfile {
  id: string; // Możemy to zmockować na razie, bo /api/users/me nie zwraca ID w obecnej wersji
  username: string;
  email: string;
  bio: string;
  avatar: string;
  joinedDate: string;
}

interface UserContextType {
  user: UserProfile | null;
  isLoadingUser: boolean;
  updateUser: (data: Partial<UserProfile>) => void;
  fetchUser: () => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoadingUser, setIsLoadingUser] = useState(false);

  const fetchUser = useCallback(async () => {
    if (!isAuthenticated) {
      setUser(null);
      return;
    }

    setIsLoadingUser(true);
    try {
      // 1. Odbiór ORYGINAŁU z backendu
      const profileData = await getUserProfile();

      // 2. Dołączenie MOCKOWANYCH danych profilowych
      setUser({
        id: "1", // MOCK
        username: profileData.username, // ORYGINAŁ
        email: profileData.email, // ORYGINAŁ
        bio: "Status: Zew Miasteczka za 3,50!", // MOCK
        avatar: MOCKS.AVATAR, // MOCK
        joinedDate: "Marzec 2024" // MOCK
      });
    } catch (error) {
      console.error("Error fetching user profile:", error);
    } finally {
      setIsLoadingUser(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const updateUser = (data: Partial<UserProfile>) => {
    // MOCK: Aktualizacja kontekstu lokalnie po edycji na ekranie EditProfileScreen
    setUser(prev => prev ? { ...prev, ...data } : null);
  };

  return (
    <UserContext.Provider value={{ user, isLoadingUser, updateUser, fetchUser }}>
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
