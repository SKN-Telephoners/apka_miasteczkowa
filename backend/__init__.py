from flask import Flask
from backend.extensions import db, bcrypt, CORS, jwt
from backend.config import Config, TestConfig
from backend.routes import main, auth

def create_app(test_mode=False):
    app = Flask(__name__)
    CORS(app)
    
    if test_mode:
        app.config.from_object(TestConfig)
    else:
        app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    
    return app