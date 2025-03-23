import os

class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:zaq1%40WSX@localhost/apka?sslmode=require"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:zaq1%40WSX@localhost/apka?sslmode=require"
    TESTING = True
