from dotenv import load_dotenv
import os
from flask_migrate import Migrate
from backend.extensions import db

load_dotenv()

from backend import create_app

app = create_app(dev_mode=True)
celery_app = app.extensions["celery"]
migrate = Migrate(app, db)

if __name__ == "main":
    app.run(host="0.0.0.0", port=5000, debug=True)