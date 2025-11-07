from backend.models import TokenBlocklist
from backend.extensions import db

def add_token_to_db(token):
    blocked_token = TokenBlocklist(jti=token)
    db.session.add(blocked_token)
    db.session.commit()

def revoke_token(jti, user_id):
    token = TokenBlocklist(jti=jti, user_id=user_id)
    db.session.add(token)
    db.session.commit()
