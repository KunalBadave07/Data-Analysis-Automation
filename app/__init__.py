from dotenv import load_dotenv
from flask import Flask

from app.config import Config
from app.extensions import bcrypt, login_manager
from app.services.auth_store import init_auth_db


def create_app(config_overrides: dict | None = None) -> Flask:
    load_dotenv(override=True)

    app = Flask(__name__)
    app.config.from_object(Config)
    if config_overrides:
        app.config.update(config_overrides)

    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    with app.app_context():
        init_auth_db()

    from app.routes.analysis import analysis_bp
    from app.routes.auth import auth_bp
    from app.routes.dataset import dataset_bp
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dataset_bp)
    app.register_blueprint(analysis_bp)

    return app
