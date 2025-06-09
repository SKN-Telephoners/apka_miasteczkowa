# backend/__init__.py

from flask import Flask, jsonify, make_response
from backend.extensions import db, bcrypt, jwt, mail, limiter, CORS
from backend.config import Config, TestConfig
from backend.routes import main, auth, events  # DODANE: import blueprintu "events"
from werkzeug.exceptions import HTTPException
from flask_migrate import Migrate


def create_app(test_mode=False):
    app = Flask(__name__)
    CORS(app)
    
    migrate = Migrate(app, db)

    # Inicjalizacja limiter (in-memory)
    limiter.init_app(app)

    # Załaduj konfigurację
    if test_mode:
        app.config.from_object(TestConfig)
    else:
        app.config.from_object(Config)

    # Inicjalizacja rozszerzeń
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)

    # Rejestracja blueprintów
    app.register_blueprint(main, url_prefix="/api")
    app.register_blueprint(auth, url_prefix="/api/auth")
    app.register_blueprint(events, url_prefix="/api")  # DODANE: rejestracja blueprintu "events" pod /api

    # Opcjonalny root, żeby szybko sprawdzić, że serwer działa
    @app.route("/")
    def index():
        return jsonify({"message": "Backend działa"}), 200

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
