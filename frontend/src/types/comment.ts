export interface Comment {
  comment_id: string;
  parent_comment_id: string | null;
  user_id: string;
  username?: string | null;
  profile_picture_url?: string | null;
  event_id: string;
  created_at: string;
  content: string;
  edited: boolean;
  deleted: boolean;
  replies: Comment[];
}