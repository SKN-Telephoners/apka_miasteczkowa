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
}