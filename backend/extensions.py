from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
# Limiter instantion (in-memory)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    headers_enabled=True,            # turn on headers
    retry_after="delta-seconds"      

)