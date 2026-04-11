import api from "./api";

// Odpowiedź z /api/users/profile wygląda tak:
// { "status": "success", "data": { "user_id": "...", "username": "...", "email": "..." } }

interface GetUserResponse {
  data: {
    user_id: string;
    username: string;
    email: string;
    description: string | null;
    profile_picture: { cloud_id: string; url: string } | null;
    academy: string | null;
    course: string | null;
    year: number | null;
    academic_clubs: string[] | null;
    created_at: string;
  };
}

export const getUserProfile = async () => {
  try {
    const ts = new Date().getTime();
    const response = await api.get<GetUserResponse>(`/api/users/profile?t=${ts}`);
    return response.data.data;
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || "Błąd pobierania profilu";
    throw new Error(msg);
  }
};
