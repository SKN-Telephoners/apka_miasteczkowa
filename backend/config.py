from datetime import timedelta
// Configuration class for the Flask application, including database URI, JWT settings, and email server settings
// Po polsku: Klasa konfiguracyjna dla aplikacji Flask, zawierająca URI bazy danych, ustawienia JWT i ustawienia serwera pocztowego
class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost/apka_miasteczkowa?sslmode=require"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "asdsadsdasdasdasd" #provide secret key
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    MAIL_SERVER = ''  #SMTP server ex. smtp.gmail.com
    MAIL_PORT = 587  #TLS or 465 for SSL
    MAIL_USE_SSL = False  # if SSL True
    MAIL_USERNAME =  'your-email@example.com'
    MAIL_PASSWORD = 'your-email-password'
    MAIL_DEFAULT_SENDER =  'your-email@example.com'
// Test configuration class for the Flask application, with settings for testing environment and email suppression
// Po polsku: Klasa konfiguracyjna testowa dla aplikacji Flask, z ustawieniami dla środowiska testowego i tłumieniem wysyłania maili    
class TestConfig(Config):
    MAIL_SUPPRESS_SEND = True
    MAIL_BACKEND = 'flask_mail.backends.locmem.EmailBackend'
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost/apka_miasteczkowa_test?sslmode=require"
    TESTING = True

