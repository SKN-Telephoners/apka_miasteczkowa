import React, { createContext, useContext, useState } from "react";
import { Event } from "../types";
import { createEvent, CreateEventData, deleteEvent, getEvents } from "../services/events";

interface EventContextType {
  events: Event[];
  isLoading: boolean;
  addEvent: (eventData: CreateEventData) => Promise<void>;
  removeEvent: (eventId: string) => Promise<void>;
  fetchEvents: (page?: number) => Promise<void>;
}

const EventContext = createContext<EventContextType | undefined>(undefined);

export const EventProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [events, setEvents] = useState<Event[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchEvents = async (page: number = 1) => {
    setIsLoading(true);
    try {
      const response = await getEvents(page);
      setEvents(response.data || []);
    } catch (error) {
      console.error("Error fetching events:", error);
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    fetchEvents();
  }, []);

  const addEvent = async (eventData: CreateEventData) => {
    setIsLoading(true);
    try {
      const response = await createEvent(eventData);
      const newEvent: Event = {
        id: response.event_id,
        name: eventData.name,
        description: eventData.description,
        date: eventData.date,
        time: eventData.time,
        location: eventData.location,
        creator_id: response.creator_id,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        comment_count: 0,
        is_private: eventData.is_private,
      };
      setEvents(prev => [...prev, newEvent]);
    } catch (error) {
      console.error("Error creating event:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const removeEvent = async (eventId: string) => {
    setIsLoading(true);
    try {
      await deleteEvent(eventId);
      setEvents(prev => prev.filter(event => event.id !== eventId));
    } catch (error) {
      console.error("Error deleting event:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <EventContext.Provider value={{ events, isLoading, addEvent, removeEvent, fetchEvents }}>
      {children}
    </EventContext.Provider>
  );
};

export const useEvents = () => {
  const context = useContext(EventContext);
  if (!context) {
    throw new Error("useEvents must be used within an EventProvider");
  }
  return context;
};