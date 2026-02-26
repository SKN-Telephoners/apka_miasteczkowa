from backend.extensions import db, bcrypt
from sqlalchemy import CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone
// User model representing the users of the application, with fields for username, password hash, email, and creation date
// Po polsku: Model użytkownika reprezentujący użytkowników aplikacji, z polami dla nazwy użytkownika, hasha hasła, emaila i daty utworzenia
class User(db.Model):
    __tablename__ = "app_user"
    
    user_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = db.Column(db.String(32), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(320), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    
    __table_args__ = (
        CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'", name="email_format"),
    )
    // Initialize a new User instance with the provided username, password, and email, hashing the password for secure storage
    // Po polsku: Inicjalizacja nowej instancji użytkownika z podaną nazwą użytkownika, hasłem i emailem, haszując hasło dla bezpiecznego przechowywania
    def __init__(self, username, password, email):
        self.username = username
        self.email = email # TODO! Add function that checks email using regex
        pass_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        self.password_hash = pass_hash
    // Validate the provided password against the stored password hash
    // Po polsku: Walidacja podanego hasła w stosunku do przechowywanego hasha hasła    
    def validate_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    // Update the user's password by hashing the new password and storing it in the database
    // Po polsku: Aktualizacja hasła użytkownika poprzez haszowanie nowego hasła i przechowywanie go w bazie danych
    def update_password(self, password):
        pass_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        self.password_hash = pass_hash
    // Return a string representation of the User instance, showing the username
    // Po polsku: Zwrócenie reprezentacji tekstowej instancji użytkownika, pokazującej nazwę użytkownika
    def __repr__(self):
        return f"User {self.username}"
// TokenBlocklist model representing revoked JWT tokens, with fields for token ID, token type, user ID, revocation time, and expiration time
// Po polsku: Model TokenBlocklist reprezentujący unieważnione tokeny JWT, z polami dla ID tokena, typu tokena, ID użytkownika, czasu unieważnienia i czasu wygaśnięcia    
class TokenBlocklist(db.Model):
    __tablename__ = "token_blocklist"

    token_id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    jti = db.Column(db.String(36), nullable=False, unique=True)
    token_type = db.Column(db.String(18), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("app_user.user_id", ondelete='CASCADE'), nullable=False, index=True)
    revoked_at = db.Column(db.DateTime)
    expires = db.Column(db.DateTime, nullable=False)

    user = db.relationship("User")