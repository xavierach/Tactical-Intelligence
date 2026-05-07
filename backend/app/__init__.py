from flask import Flask
from flask_cors import CORS

from .config import Config
from .extensions.db import db
from .routes.competitions import competitions_bp
from .routes.health import health_bp
from .routes.matches import matches_bp
from .routes.reports import reports_bp

def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)

    app.config.from_object(config_object)

    CORS(app)

    db.init_app(app)

    app.register_blueprint(competitions_bp, url_prefix="/api")
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(matches_bp, url_prefix="/api")
    app.register_blueprint(reports_bp, url_prefix="/api")

    return app
