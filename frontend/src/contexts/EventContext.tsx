import React, { createContext, useContext, useState } from "react";
import { Event } from "../types";
import { createEvent, deleteEvent } from "../services/events";

interface EventContextType {
  events: Event[];
  isLoading: boolean;
  addEvent: (eventData: { name: string; description: string; date: string; time: string; location: string }) => Promise<void>;
  removeEvent: (eventId: string) => Promise<void>;
}

const EventContext = createContext<EventContextType | undefined>(undefined);

export const EventProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [events, setEvents] = useState<Event[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const addEvent = async (eventData: { name: string; description: string; date: string; time: string; location: string }) => {
    setIsLoading(true);
    try {
      const response = await createEvent(eventData);
      const newEvent: Event = {
        event_id: response.event_id,
        name: eventData.name,
        description: eventData.description,
        date_and_time: `${eventData.date} ${eventData.time}`,
        location: eventData.location,
        creator_id: 'current_user', // Placeholder, bo backend nie zwraca
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
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
      setEvents(prev => prev.filter(event => event.event_id !== eventId));
    } catch (error) {
      console.error("Error deleting event:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <EventContext.Provider value={{ events, isLoading, addEvent, removeEvent }}>
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