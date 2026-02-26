from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
// Initialize Flask extensions for database, password hashing, JWT management, email handling, and rate limiting
// Po polsku: Inicjalizacja rozszerzeń Flask dla bazy danych, hashowania haseł, zarządzania JWT, obsługi maili i ograniczania liczby żądań
db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
mail = Mail()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    headers_enabled=True,
    retry_after="delta-seconds"      
)