from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

DB_URI = "postgresql://postgres:postgres@localhost/apka_miasteczkowa?sslmode=require"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI

db = SQLAlchemy()
bcrypt = Bcrypt()

if __name__ == '__main__':
    app.run()