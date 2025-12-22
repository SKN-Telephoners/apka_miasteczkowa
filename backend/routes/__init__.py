from .auth_routes import auth_bp
from .users_routes import users_bp
from .friendships_routes import friends_bp
from .events_routes import events_bp
from .comments_routes import comments_bp
from .email_routes import email_bp
from . import tokens

__all__ = [
    "tokens"
    "auth_bp",
    "users_bp",
    "friends_bp",
    "events_bp",
    "comments_bp",
    "email_bp",
]

def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(friends_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(email_bp)