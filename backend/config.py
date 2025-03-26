from datetime import timedelta

class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost/apka_miasteczkowa?sslmode=require"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "" #provide secret key
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost/apka_miasteczkowa_test?sslmode=require"
    TESTING = True

