import { Platform } from "react-native";

export const API_BASE_URL = __DEV__
  ? Platform.select({
    android: "http://10.0.2.2:5000",
    ios: "http://10.0.2.2:5000",
    default: "http://10.0.2.2:5000",
  })
  : "https://production-api.com";

if (!__DEV__ && !API_BASE_URL.startsWith('https://')) {
  throw new Error("App has to use HTTPS protocol");
}

export const STORAGE_KEYS = {
  ACCESS_TOKEN: "access_token",
  REFRESH_TOKEN: "refresh_token",
  USER_DATA: "user_data",
} as const;

export const TIMEOUTS = {
  REQUEST_TIMEOUT: 10000,
  RETRY_DELAY: 1000,
} as const;


export const THEME = {
  colors: {
    // light mode
    lm_bg: "#FFFFFF",
    lm_txt: "#000000",
    lm_nav_cons: "#202020",
    lm_highlight: "#CF6F02",
    lm_ico: "#7F7F7F",
    lm_src_br: "#F8F8F8",
    lm_srch_wrd: "#666666",
    // dark mode
    dm_bg: "#000000",
    dm_txt: "#FFFFFF",
    dm_nav_icons: "#E9E9E9",
    dm_highlight: "#0300D1",
    dm_ico: "#7F7F7F",
    dm_src_br: "#222222",
    dm_srch_wrd: "#999999",
    // agh colors
    agh_red: "#B00E28",
    agh_green: "#00723F",
    agh_black: "#221F21",
    // phone_ui
    phone_ui_bg: "#000000",
    phone_ui_icons: "#D9D9D9",
    // Status Colors (old)
    success: "#",
    error: "#",
    warning: "#",
    info: "#",
    // Transparent Colors (old)
    overlay: "rgba(0, 0, 0, 0.5)",
    transparentBlue: "rgba(3, 0, 209, 0.8)",
    transparentOrange: "rgba(207, 111, 2, 0.8)",
  },

  spacing: {
    xs: 4,
    s: 8,
    m: 16, // default
    l: 24,
    xl: 32,
    xxl: 40,
  },

  typography: {
    title: {
      fontFamily: "Prompt",
      fontWeight: "400" as const,
      fontSize: 20,
      lineHeight: 20,
    },

    eventTitle: {
      fontFamily: "Prompt",
      fontWeight: "700" as const,
      fontSize: 20,
      lineHeight: 20,
    },
    text: {
      fontFamily: "Roboto",
      fontWeight: "400" as const,
      fontSize: 16,
      lineHeight: 20.5,
    },
    name: {
      fontFamily: "Roboto",
      fontWeight: "700" as const,
      fontSize: 16,
      lineHeight: 20,
    },
    faculty: {
      fontFamily: "Roboto",
      fontWeight: "700" as const,
      fontSize: 10,
      lineHeight: 16,
    },
  },

  borderRadius: {
    s: 4,
    m: 8,
    l: 12,
    xl: 16,
    round: 9999, // (avatar w kółku)
  },
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
    CHECK_USERNAME: "Sprawdź czy nazwa użytkownika jest poprawna",
    CHECK_PASSWORD: "Sprawdź czy hasło jest poprawne",
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

export const MOCKS = {
  AVATAR: "https://www.hollywoodreporter.com/wp-content/uploads/2011/06/drive_primary.jpg?w=1440&h=810&crop=1",
} as const;
