import React, { createContext, useContext, useState } from "react";
import { Event } from "../types";
import { createEvent, CreateEventData, deleteEvent } from "../services/events";

const normalizeEventPictures = (
  pictures?: CreateEventData["pictures"] | CreateEventData["picture"],
) => {
  if (!pictures) {
    return undefined;
  }

  const pictureList = Array.isArray(pictures) ? pictures : [pictures];
  const normalized = pictureList
    .filter((picture): picture is NonNullable<typeof picture> => Boolean(picture && picture.cloud_id))
    .map((picture) => ({ cloud_id: picture.cloud_id }));

  return normalized.length > 0 ? normalized : undefined;
};

interface EventContextType {
  events: Event[];
  isLoading: boolean;
  addEvent: (eventData: CreateEventData) => Promise<void>;
  removeEvent: (eventId: string) => Promise<void>;
}

const EventContext = createContext<EventContextType | undefined>(undefined);

export const EventProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [events, setEvents] = useState<Event[]>([]);
  const [isLoading, setIsLoading] = useState(false);

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
        pictures: normalizeEventPictures(eventData.pictures ?? eventData.picture),
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