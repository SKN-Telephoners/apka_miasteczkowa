from flask import Flask
from backend.extensions import db, bcrypt, CORS
from backend.config import Config, TestConfig
from backend.routes import main

def create_app(test_mode=False):
    app = Flask(__name__)
    CORS(app)
    
    if test_mode:
        app.config.from_object(TestConfig)
    else:
        app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    
    app.register_blueprint(main)
    
    return app
