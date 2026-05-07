from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions.db import db
from app.routes.main import main_bp

def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    CORS(app)

    db.init_app(app)

    app.register_blueprint(main_bp)

    return app