from backend.models import TokenBlocklist
from backend.extensions import db
// Service functions for token management and revocation
// Po polsku: Funkcje serwisowe dla zarządzania tokenami i ich unieważnianiem
def add_token_to_db(token):
    blocked_token = TokenBlocklist(jti=token)
    db.session.add(blocked_token)
    db.session.commit()
// Revoke a token by its JTI and user ID
// Po polsku: Unieważnij token za pomocą jego JTI i ID użytkownika
def revoke_token(jti, user_id):
    token = TokenBlocklist(jti=jti, user_id=user_id)
    db.session.add(token)
    db.session.commit()
