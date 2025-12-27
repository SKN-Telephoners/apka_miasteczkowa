class Constants:
    MAX_EMAIL_LEN = 320
    MAX_USERNAME_LEN = 32
    MIN_USERNAME_LEN = 3
    MAX_PASSWORD_LEN = 128
    MIN_EVENT_NAME = 3
    MAX_EVENT_NAME = 32
    MAX_LOCATION_LEN = 32
    MAX_DESCRIPTION_LEN = 1000
    MAX_COMMENT_LEN = 1000
    EMAIL_PATTERN = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    USERNAME_PATTERN = r"^[A-Za-z0-9_.'-]+$"
    PASSWORD_PATTERN = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,72}$"
    RESET_PASSWORD_EXPIRES = 15
    