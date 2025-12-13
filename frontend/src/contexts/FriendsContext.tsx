import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
// Import funkcji API i Storage
// Zastąpić je naszymi implementacjami!
import api from '../services/api';
import { User, Request, FriendsContextType } from '../types/friends'; 

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
  searchUsers: (query: string) => Promise<User[]>; // Akcja zwracająca wynik
}

const FRIENDS_CACHE_KEY = 'friendsCache';
const CONTEXT_DEFAULT_VALUE: FriendsContextType = {
  friends: [],
  incomingRequests: [],
  outgoingRequests: [],
  loading: true, // Zaczynamy od ładowania, aby pobrać cache
  error: null,
  // Zastępcze funkcje dla typowania:
  fetchFriends: async () => {},
  sendFriendRequest: async () => {},
  acceptRequest: async () => {},
  declineRequest: async () => {},
  searchUsers: async () => [],
};

const FriendsContext = createContext<FriendsContextType | undefined>(undefined);

export const FriendsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // --- STAN LOKALNY ---
  const [friends, setFriends] = useState<User[]>([]);
  const [incomingRequests, setIncomingRequests] = useState<Request[]>([]);
  const [outgoingRequests, setOutgoingRequests] = useState<Request[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // --- PERSISTENCE: ZAPISYWANIE DANYCH DO CACHE ---
  const saveCache = useCallback(async (data: { friends: User[], incomingRequests: Request[], outgoingRequests: Request[] }) => {
    try {
      await AsyncStorage.setItem(FRIENDS_CACHE_KEY, JSON.stringify(data));
    } catch (e) {
      console.error("Failed to save friends cache", e);
    }
  }, []);

  const fetchFriends = useCallback(async (isInitialLoad: boolean = false) => {
    setError(null);
    if (!isInitialLoad) {
      setLoading(true); 
    }
    
    try {
      // Symulacja pobierania danych (do zmiany na nasze funkcje API)
      const data = await api.getFriendsData(); // Zakładamy, że to zwraca { friends, incomingRequests, outgoingRequests }
      
      setFriends(data.friends);
      setIncomingRequests(data.incomingRequests);
      setOutgoingRequests(data.outgoingRequests);
      
      // Synchronizacja cache po pomyślnym pobraniu
      await saveCache(data);

    } catch (err) {
      setError("Nie udało się załadować danych o znajomych.");
      console.error("Error fetching friends data:", err);
    } finally {
      setLoading(false);
    }
  }, [saveCache]);

  const sendFriendRequest = useCallback(async (userId: string) => {
    try {
      setLoading(true);
      const newRequest = await api.sendRequest(userId); 
      
      setOutgoingRequests(prev => [...prev, newRequest]);
      
      await saveCache({ friends, incomingRequests, outgoingRequests: [...outgoingRequests, newRequest] });
    } catch (err) {
      setError("Nie udało się wysłać zaproszenia.");
    } finally {
      setLoading(false);
    }
  }, [friends, incomingRequests, outgoingRequests, saveCache]);

  const acceptRequest = useCallback(async (requestId: string) => {
    try {
      setLoading(true);
      const acceptedFriend = await api.acceptRequest(requestId); 
      
      setIncomingRequests(prev => prev.filter(req => req.id !== requestId));

      setFriends(prev => [...prev, acceptedFriend]);
      
      await saveCache({ 
        friends: [...friends, acceptedFriend], 
        incomingRequests: incomingRequests.filter(req => req.id !== requestId), 
        outgoingRequests 
      });

    } catch (err) {
      setError("Nie udało się zaakceptować zaproszenia.");
    } finally {
      setLoading(false);
    }
  }, [friends, incomingRequests, outgoingRequests, saveCache]);


  const declineRequest = useCallback(async (requestId: string) => {
    try {
      setLoading(true);
      await api.declineRequest(requestId); 
      
  
      setIncomingRequests(prev => prev.filter(req => req.id !== requestId));
      

      await saveCache({ 
        friends, 
        incomingRequests: incomingRequests.filter(req => req.id !== requestId), 
        outgoingRequests 
      });
    } catch (err) {
      setError("Nie udało się odrzucić zaproszenia.");
    } finally {
      setLoading(false);
    }
  }, [friends, incomingRequests, outgoingRequests, saveCache]);


  const searchUsers = useCallback(async (query: string): Promise<User[]> => {
    try {
      return await api.searchUsers(query);
    } catch (err) {
      console.error("Error searching users:", err);
      // Można ustawić error w stanie kontekstu, ale często lepiej obsłużyć go lokalnie w komponencie wyszukiwania.
      return []; 
    }
  }, []);

  useEffect(() => {
    const loadCacheAndFetch = async () => {
      try {
        const cachedData = await AsyncStorage.getItem(FRIENDS_CACHE_KEY);
        if (cachedData) {
          const parsedData = JSON.parse(cachedData);
          setFriends(parsedData.friends || []);
          setIncomingRequests(parsedData.incomingRequests || []);
          setOutgoingRequests(parsedData.outgoingRequests || []);
        }
      } catch (e) {
        console.error("Failed to load friends cache", e);
      } finally {
        fetchFriends(true); 
      }
    };

    loadCacheAndFetch();
  }, [fetchFriends]);


  // --- KONTEKSTOWA WARTOŚĆ (Użycie useMemo dla optymalizacji) ---
  const contextValue = useMemo(() => ({
    friends,
    incomingRequests,
    outgoingRequests,
    loading,
    error,
    fetchFriends,
    sendFriendRequest,
    acceptRequest,
    declineRequest,
    searchUsers,
  }), [
    friends,
    incomingRequests,
    outgoingRequests,
    loading,
    error,
    fetchFriends,
    sendFriendRequest,
    acceptRequest,
    declineRequest,
    searchUsers,
  ]);

  return (
    <FriendsContext.Provider value={contextValue}>
      {children}
    </FriendsContext.Provider>
  );
};

export const useFriends = () => {
  const context = useContext(FriendsContext);
  if (context === undefined) {
    throw new Error('useFriends must be used within a FriendsProvider');
  }
  return context;
};