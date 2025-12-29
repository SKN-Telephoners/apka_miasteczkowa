export interface Comment {
  comment_id: string
  parent_comment_id: string | null
  user_id: string
  event_id: string
  created_at: string
  content: string
  edited: boolean
  replies: Comment[];
}