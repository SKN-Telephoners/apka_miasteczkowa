from flask import Flask
from datetime import datetime
import re

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

app = Flask(__name__)

class User:
    def __init__(self, username, email, password, major, semester, degree, university, birth_year, picture=None, description=None):
        self.username = username
        self.email = email
        self.password = password
        self.major = major  
        self.semester = semester 
        self.degree = degree 
        self.university = university  
        self.picture = picture
        self.description = description
        self.birth_year = birth_year


    def change_email(self, new_email):
        if(re.fullmatch(regex, new_email)):
            self.email=new_email
            return "Changed successfully"
        else:
            return "Invalid Email"

    def change_password(self, new_password):
        self.password = new_password

    def change_picture(self, new_picture):
        self.picture = new_picture

    def change_description(self, new_description):
        self.description = new_description

    def get_age(self):
        current_year = datetime.now().year
        return current_year - self.birth_year


@app.route('/')
def home():
    return 'Hello World!'


if __name__ == '__main__':
    app.run()