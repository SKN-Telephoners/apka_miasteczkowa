from flask import Flask, jsonify, make_response
from backend.extensions import db, bcrypt, jwt, mail, limiter, CORS
from backend.config import Config, TestConfig
from backend.routes.auth_routes import auth_bp
from backend.routes.user_routes import user_bp
from backend.routes.mail_routes import mail_bp
from werkzeug.exceptions import HTTPException

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(mail_bp)

def create_app(test_mode=False):
    app = Flask(__name__)
    CORS(app)
    
# Initializing limtier (in-memory)
    limiter.init_app(app)

    if test_mode:
        app.config.from_object(TestConfig)
    else:
        app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    
    app.register_blueprint(main)
    app.register_blueprint(auth)
    
    @app.errorhandler(429)
    def on_ratelimit(e):
        resp = e.get_response()
        retry_after = resp.headers.get("Retry-After")

        message = (
            f"Spróbuj ponownie za {retry_after} sekund."
            if retry_after
            else "Za dużo prób. Spróbuj później."
        )

        payload = {
            "error": "Za dużo żądań.",
            "message": message
        }
        response = make_response(jsonify(payload), 429)
        if retry_after:
            response.headers["Retry-After"] = retry_after
        return response

    return app
