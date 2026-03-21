from flask import Flask, jsonify, make_response
from backend.extensions import db, bcrypt, jwt, mail, limiter, CORS, celery_init_app
from backend.config import Config, TestConfig
from werkzeug.exceptions import HTTPException
from flask_talisman import Talisman
import logging
from backend.routes import register_blueprints
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os

def create_app(test_mode=False, dev_mode=False):
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "https://production-api.com"}})

    if test_mode:
        app.config.from_object(TestConfig)
    else:
        app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    celery_init_app(app)
    cloudinary_config = cloudinary.config(secure=True)

    register_blueprints(app)

    register_blueprints(app)

    logging.basicConfig(level=logging.INFO)

    csp = {
        'default-src': "'none'",
        'frame-ancestors': "'none'",
        'form-action': "'none'"
    }

    # Keep transport security in production, but allow plain HTTP for local dev.
    flask_debug = os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes"}
    secure_transport = not (test_mode or dev_mode or flask_debug)

    Talisman(
        app,
        content_security_policy=csp,
        force_https=secure_transport,
        session_cookie_secure=secure_transport,
        session_cookie_http_only=True,
        strict_transport_security=secure_transport,
        strict_transport_security_max_age=31536000, #1 rok
        referrer_policy='no-referrer'
    )
    
    @app.errorhandler(429)
    def on_ratelimit(e):
        return make_response(jsonify({
            "error": "Za dużo żądań.",
            "message": f"Spróbuj ponownie za {e.description.split('at '[-1])}."
        }), 429)

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException):
            return e
        app.logger.error(f"Internal Server error: {e}")

        return make_response(jsonify({
            "error": "Błąd serwera",
            "message": f"Wystąpił nieoczekiwany błąd"
        }), 500)
    return app
