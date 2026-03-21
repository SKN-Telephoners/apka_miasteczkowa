export type Event = {
    id: string;
    name: string;
    description: string;
    date: string;
    time: string;
    location: string;
    creator_id: string;
    created_at?: string;
    updated_at?: string;
    is_edited?: boolean;
    comment_count: number;
    participant_count?: number;
    is_private: boolean;
}