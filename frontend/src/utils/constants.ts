import { Platform } from "react-native";

export const API_BASE_URL = __DEV__
  ? Platform.select({
      android: "http://10.0.2.2:5000",
      ios: "http://localhost:5000",
      default: "http://localhost:5000",
    })
  : "https://production-api.com";

export const STORAGE_KEYS = {
  ACCESS_TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
  USER_DATA: "user_data",
} as const;

export const TIMEOUTS = {
  REQUEST_TIMEOUT: 10000,
  RETRY_DELAY: 1000,
} as const;

export const COLORS = {
  primary: "#",
  primaryLight: "#",
  primaryDark: "#",

  secondary: "#",
  secondaryLight: "#",
  secondaryDark: "#",

  accent: "#",

  white: "#ffffff",
  black: "#000000",
  gray: "#f5f5f5",
  grayDark: "#666666",
  grayLight: "#cccccc",

  // Status Colors
  success: "#",
  error: "#",
  warning: "#",
  info: "#",

  // Transparent Colors
  overlay: "rgba(0, 0, 0, 0.5)",
  transparentBlue: "rgba(3, 0, 209, 0.8)",
  transparentOrange: "rgba(207, 111, 2, 0.8)",
} as const;

// Messages
export const MESSAGES = {
  // Auth Messages
  AUTH: {
    LOGIN_SUCCESS: "Logowanie powiodło się!",
    LOGIN_ERROR: "Wystąpił błąd podczas logowania",
    LOGIN_INVALID_CREDENTIALS: "Nieprawidłowa nazwa użytkownika lub hasło",
    LOGIN_USER_NOT_FOUND: "Użytkownik nie istnieje",
    REGISTER_SUCCESS: "Rejestracja powiodła się!",
    REGISTER_ERROR: "Wystąpił błąd podczas rejestracji",
    REGISTER_USER_EXISTS: "Użytkownik już istnieje",
    LOGOUT_SUCCESS: "Wylogowano pomyślnie",
    PASSWORD_RESET_SENT: "Link do resetowania hasła został wysłany",
    PASSWORD_RESET_ERROR: "Błąd podczas resetowania hasła",
    TOKEN_EXPIRED: "Sesja wygasła. Zaloguj się ponownie",
    FIELDS_REQUIRED: "Uzupełnij proszę wszystkie pola",
    INVALID_EMAIL: "Nieprawidłowy adres email",
    PASSWORD_TOO_SHORT: "Hasło musi mieć co najmniej 8 znaków",
    PASSWORDS_DO_NOT_MATCH: "Hasła nie są identyczne",
  },

  // Error Messages
  ERROR: {
    NETWORK_ERROR: "Brak połączenia z serwerem",
    SERVER_ERROR: "Błąd serwera. Spróbuj ponownie później",
    TIMEOUT_ERROR: "Przekroczono czas oczekiwania",
    UNKNOWN_ERROR: "Wystąpił nieznany błąd",
    INVALID_RESPONSE: "Nieprawidłowa odpowiedź serwera",
  },

  // Validation Messages
  VALIDATION: {
    REQUIRED_FIELD: "To pole jest wymagane",
    INVALID_EMAIL: "Nieprawidłowy format adresu email",
    MIN_LENGTH: (min: number) => `Minimum ${min} znaków`,
    MAX_LENGTH: (max: number) => `Maksimum ${max} znaków`,
    PASSWORDS_MATCH: "Hasła muszą być identyczne",
  },

  // UI Messages
  UI: {
    LOADING: "Ładowanie...",
    PLEASE_WAIT: "Proszę czekać...",
    TRY_AGAIN: "Spróbuj ponownie",
    CANCEL: "Anuluj",
    CONFIRM: "Potwierdź",
    SAVE: "Zapisz",
    DELETE: "Usuń",
    EDIT: "Edytuj",
    CLOSE: "Zamknij",
    BACK: "Wstecz",
    NEXT: "Dalej",
    SUBMIT: "Wyślij",
  },

  // App Specific Messages
  APP: {
    WELCOME_TITLE: "Aplikacja Miasteczkowa",
    WELCOME_QUOTE: "Bo życie studenckie to coś więcej niż nauka",
    LOGIN_TITLE: "Zaloguj się",
    REGISTER_TITLE: "Załóż konto",
    RESET_PASSWORD_TITLE: "Zresetuj hasło",
    HOME_TITLE: "Strona główna",
  },

  // Placeholder Messages
  PLACEHOLDERS: {
    USERNAME: "Nazwa użytkownika",
    EMAIL: "Adres email",
    PASSWORD: "Hasło",
    CONFIRM_PASSWORD: "Potwierdź hasło",
    SEARCH: "Szukaj...",
  },

  // Button Labels
  BUTTONS: {
    LOGIN: "Zaloguj się",
    REGISTER: "Załóż konto",
    LOGOUT: "Wyloguj się",
    FORGOT_PASSWORD: "Zapomniałeś hasła?",
    RESET_PASSWORD: "Zresetuj hasło",
    SEND_RESET_LINK: "Wyślij link",
    BACK_TO_LOGIN: "Powrót do logowania",
    UPDATE_PROFILE: "Zaktualizuj profil",
  },
} as const;

export const APP_CONFIG = {
  NAME: "Aplikacja Miasteczkowa",
  VERSION: "1.0.0",
  MIN_PASSWORD_LENGTH: 8,
  MAX_USERNAME_LENGTH: 30,
  MAX_EMAIL_LENGTH: 100,
} as const;
