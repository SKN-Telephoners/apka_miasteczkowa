from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from celery import Celery, Task
from flask import Flask
import os
import json

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
mail = Mail()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    headers_enabled=True,
    retry_after="delta-seconds", 
    storage_uri="redis://localhost:6379"     
)

#celery
def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app

def load_static_data(app):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.normpath(os.path.join(base_dir, "keys")) 
    
    files = {
        'ACADEMY_DATA': 'academy.json',
        'COURSES_DATA': 'courses.json',
        'CLUBS_DATA': 'academic_clubs.json',
        'FACULTIES_DATA': 'faculties.json'
    }

    for config_key, filename in files.items():
        path = os.path.join(data_dir, filename)
        try:
            with open(path, encoding="utf-8") as f:
                app.config[config_key] = json.load(f)
        except Exception as e:
            app.logger.error(f"Failed to load static file {filename}: {e}")
            app.config[config_key] = {} if "DATA" in config_key else []