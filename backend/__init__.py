from flask import Flask, jsonify, make_response
from backend.extensions import db, bcrypt, jwt, mail, limiter, CORS, celery_init_app, load_static_data
from backend.config import Config, TestConfig
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge
from flask_talisman import Talisman
import logging
from backend.routes import register_blueprints
import cloudinary
import os

def create_app(test_mode=False, dev_mode=False):
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "https://production-api.com"}})

    if test_mode:
        app.config.from_object(TestConfig)
    else:
        app.config.from_object(Config)

    load_static_data(app)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    celery_init_app(app)
    
    cloudinary_url = os.getenv("CLOUDINARY_URL")
    if cloudinary_url:
        cloudinary.config(cloudinary_url=cloudinary_url, secure=True)
    else:
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            secure=True,
        )

    cloudinary_cfg = cloudinary.config()
    if not (cloudinary_cfg.cloud_name and cloudinary_cfg.api_key and cloudinary_cfg.api_secret):
        app.logger.warning("Cloudinary is not fully configured. Set CLOUDINARY_URL or CLOUDINARY_CLOUD_NAME/CLOUDINARY_API_KEY/CLOUDINARY_API_SECRET.")

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

    @app.errorhandler(RequestEntityTooLarge)
    def on_request_too_large(_e):
        max_size_mb = round(app.config.get("MAX_CONTENT_LENGTH", 0) / (1024 * 1024))
        return make_response(jsonify({
            "error": "Plik za duży",
            "message": f"Maksymalny rozmiar pliku to {max_size_mb} MB."
        }), 413)

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
