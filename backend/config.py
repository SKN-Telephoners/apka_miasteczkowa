class Config:
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost/apka_miasteczkowa?sslmode=require"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost/apka_miasteczkowa_test?sslmode=require"
    TESTING = True
