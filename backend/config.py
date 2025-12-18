import os
from datetime import timedelta
from backend.extensions import bcrypt
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    BCRYPT_LOG_ROUNDS = 12
    
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    MAIL_SERVER = os.getenv("MAIL_SERVER")  #SMTP server ex. smtp.gmail.com
    MAIL_PORT = int(os.getenv("MAIL_PORT"))  #TLS or 465 for SSL
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")

    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
    CELERY = dict(
        broker_url=CELERY_BROKER_URL,
        result_backend=CELERY_RESULT_BACKEND,
        task_ignore_result=True,
    )
    
    
class TestConfig(Config):
    MAIL_SUPPRESS_SEND = True
    MAIL_BACKEND = 'flask_mail.backends.locmem.EmailBackend'
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL", 
        "postgresql://postgres:postgres@localhost/apka_miasteczkowa_test?sslmode=require"
    ) #jeżeli się nie uda z .env to i tak będzie
    CELERY = dict(
        broker_url="memory://",
        result_backend="cache+memory://",
        task_always_eager=True,       
        task_eager_propagates=True    
    )

