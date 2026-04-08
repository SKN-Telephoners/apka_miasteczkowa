export type EventPicture = {
    cloud_id: string;
    url?: string;
};

export type EventVisibilityFilter = "all" | "public" | "private";

// Prepared for future backend integration. UI can expose this but filtering is not applied yet.
export type EventCreatorFilter = "all" | "friends" | "others";

export type FutureEventSortMode =
    | "default"
    | "members_desc"
    | "members_asc"
    | "comments_desc"
    | "comments_asc";

export type EventCreatedAtFilter =
    | "all"
    | "today"
    | "week"
    | "month"
    | "year"
    | "older";

export type EventFilterState = {
    visibility: EventVisibilityFilter;
    creatorSource: EventCreatorFilter;
    sortMode: FutureEventSortMode;
    createdAtWindow: EventCreatedAtFilter;
};

export const DEFAULT_EVENT_FILTERS: EventFilterState = {
    visibility: "all",
    creatorSource: "all",
    sortMode: "default",
    createdAtWindow: "all",
};

export type Event = {
    id: string;
    name: string;
    description: string;
    date: string;
    time: string;
    location: string;
    creator_id: string;
    creator_username?: string | null;
    created_at?: string;
    updated_at?: string;
    is_edited?: boolean;
    comment_count: number;
    participant_count?: number;
    is_participating?: boolean;
    is_private: boolean;
    pictures?: EventPicture[];
}