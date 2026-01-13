from flask import Flask, jsonify, make_response
from backend.extensions import db, bcrypt, jwt, mail, limiter, CORS, celery_init_app
from backend.config import Config, TestConfig
from backend.routes import main, auth
from werkzeug.exceptions import HTTPException
from flask_talisman import Talisman
import logging

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
    mail.init_app(app)
    limiter.init_app(app)

    celery_init_app(app)
    
    app.register_blueprint(main)
    app.register_blueprint(auth)

    logging.basicConfig(level=logging.INFO)

    csp = {
        'default-src': "'none'",
        'frame-ancestors': "'none'",
        'form-action': "'none'"
    }

    Talisman(
        app,
        content_security_policy=csp,
        force_https=not test_mode,
        session_cookie_secure=not test_mode,
        session_cookie_http_only=True,
        strict_transport_security=True,
        strict_transport_security_max_age=3153600, #1 rok
        referrer_policy='no-referrer'
    )
    
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
