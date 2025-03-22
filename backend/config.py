import os

class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost/apka_miasteczkowa?sslmode=require"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'b7edff280334ae7cfe848b089e79d0b6f32d83c1193bdff4152744f3f96d6161'
    
class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost/apka_miasteczkowa_test?sslmode=require"
    TESTING = True