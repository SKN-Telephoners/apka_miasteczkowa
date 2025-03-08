from flask import Flask
from models import User
from extension import db, bcrypt

DB_URI = "postgresql://postgres:postgres@localhost/apka_miasteczkowa?sslmode=require"

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI

db.init_app(app)
bcrypt.init_app(app)

with app.app_context():
    db.create_all()

test_user = User('db124','pasword123','db@email.com')
db.session.add(test_user)
db.session.commit()
print("Dodane do bazy")




if __name__ == '__main__':
    app.run()