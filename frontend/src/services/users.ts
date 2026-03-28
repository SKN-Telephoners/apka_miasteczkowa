import api from "./api";

// Odpowiedź z /api/users/me wygląda tak:
// { "user": { "username": "...", "email": "..." } }

interface GetUserResponse {
  user: {
    username: string;
    email: string;
  };
}

export const getUserProfile = async () => {
  try {
    const response = await api.get<GetUserResponse>("/api/users/me");
    return response.data.user;
  } catch (err: any) {
    const msg = err?.response?.data?.message || err?.message || "Błąd pobierania profilu";
    throw new Error(msg);
  }
};
