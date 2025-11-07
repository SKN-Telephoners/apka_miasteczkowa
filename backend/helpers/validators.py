import re

MAX_EMAIL_LEN = 320
MAX_USERNAME_LEN = 32
MIN_USERNAME_LEN = 3

def validate_registration_data(data):
    if not data or not {"username", "password", "email"}.issubset(data.keys()):
        return False, "Missing required fields"

    email = data["email"]
    username = data["username"]

    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    if (
        not re.match(email_pattern, email)
        or len(email) > MAX_EMAIL_LEN
        or not (MIN_USERNAME_LEN <= len(username) <= MAX_USERNAME_LEN)
    ):
        return False, "Invalid username or email"

    return True, ""
