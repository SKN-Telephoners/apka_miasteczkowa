from flask import request, jsonify, Blueprint
from flask_jwt_extended import jwt_required, get_current_user
from backend.responses import ResponseTypes, make_api_response
from backend.extensions import db
from datetime import datetime, timezone, timedelta
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required, set_access_cookies
import os
import json
import re

users_bp = Blueprint("users", __name__, url_prefix="/api/users")

@users_bp.route("/me", methods=["GET"])
@jwt_required()
def get_user_info():
    user = get_current_user()

    if not user:
        return make_api_response(ResponseTypes.NOT_FOUND, message="User not found")

    return make_api_response(ResponseTypes.SUCCESS, data={
        "user": {
            "username": user.username,
            "email": user.email
        }})

@users_bp.route("/user_update", methods=["POST"])
@jwt_required()                                    
def update_user_course_or_academy():

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # To daje ścieżke do plików z bazą kierunków akademii itd
    DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "keys")) # tu jest ważne żeby zmienić w razie włżenia tych plików to innych folderów pozmieniać

    with open(os.path.join(DATA_DIR, "academy.json"), encoding="utf-8") as f:
        academy_data = json.load(f)
    with open(os.path.join(DATA_DIR, "courses.json"), encoding="utf-8") as r:
        courses_data = json.load(r)
    with open(os.path.join(DATA_DIR, "academic_circle.json") , encoding="utf-8") as a:
        academic_circle_data = json.load(a)

    user_data = request.get_json() #To prosi frontend o nowe dane

    academy = user_data.get("academy")
    course_year = user_data.get("course and year")
    academic_circle = user_data.get("academic_circle")

    course_pattern = rf"^({'|'.join(courses_data)})\s\d$"

    if (academy != "AGH" and course_year) or (academy != "AGH" and academic_circle): #Ta część ma sprawdzać zgodność tego co jest w menu z plikami
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Only AGH members can change course and academic circle")

    if academy not in academy_data and academy != None:
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Such academy doesn't exist")

    if course_year != None and not re.match(course_pattern, course_year):
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Such course doesn't exist")

    if course_year is not None and not re.fullmatch(r"^[A-Za-zĄąĆćĘęŁłŃńÓóŚśŹźŻż ]+ [1-6]$", course_year):
        return make_api_response(ResponseTypes.BAD_REQUEST, message="Year must be between 1 and 6")

    if academic_circle != None:
        user_circles = [circle.strip() for circle in academic_circle.split(",")]
        for circle in user_circles:
            if circle not in academic_circle_data:
                return make_api_response(ResponseTypes.BAD_REQUEST, message="Such circle  doesn't exist")

    user = get_current_user()


    if academy:
        user.academy = academy
    else:
        user.academy = None
   
    if academy == "AGH" and course_year:
        user.course_year = course_year
    else:
        user.course_year = None
            
    if academy == "AGH" and academic_circle:   
        user.academic_circle = academic_circle 
    else:
        academic_circle = None

    db.session.commit()

    return make_api_response(ResponseTypes.SUCCESS, message="User updated successfully")