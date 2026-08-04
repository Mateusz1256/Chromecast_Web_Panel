import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask

from app.blueprints.auth import auth_bp
from app.blueprints.dashboard import dashboard_bp
from app.blueprints.health import health_bp
from app.blueprints.media import media_bp
from app.blueprints.remote import remote_bp
from app.blueprints.settings import settings_bp
from app.config import AppConfig
from app.extensions import csrf, login_manager
from app.models.user import UserStore
from app.services.cast_service import CastService
from app.services.media_service import MediaService
from app.services.playback_service import PlaybackService
from app.services.rate_limiter import CommandRateLimiter
from app.services.settings_service import SettingsService


def create_app(config_object=AppConfig):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    _ensure_runtime_directories(app)
    _configure_logging(app)
    _register_extensions(app)
    _register_services(app)
    _register_cli(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(media_bp)
    app.register_blueprint(remote_bp)
    app.register_blueprint(settings_bp)
    return app


def _ensure_runtime_directories(app):
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["DATABASE_PATH"]).parent.mkdir(parents=True, exist_ok=True)
    Path(app.config["SETTINGS_PATH"]).parent.mkdir(parents=True, exist_ok=True)
    Path(app.config["MEDIA_DIRECTORY"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["LOG_DIRECTORY"]).mkdir(parents=True, exist_ok=True)


def _configure_logging(app):
    log_file = Path(app.config["LOG_DIRECTORY"]) / "app.log"
    handler = RotatingFileHandler(
        str(log_file),
        maxBytes=app.config["LOG_MAX_BYTES"],
        backupCount=app.config["LOG_BACKUP_COUNT"],
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        )
    )
    handler.setLevel(app.config["LOG_LEVEL"])

    app.logger.setLevel(app.config["LOG_LEVEL"])
    has_file_handler = any(
        isinstance(existing, RotatingFileHandler) for existing in app.logger.handlers
    )
    if not has_file_handler:
        app.logger.addHandler(handler)


def _register_services(app):
    user_store = UserStore(app.config["DATABASE_PATH"])
    user_store.init_db()
    settings_service = SettingsService(
        config_path=app.config["SETTINGS_PATH"],
        base_directory=app.config["BASE_DIRECTORY"],
    )
    settings = settings_service.load()
    if not Path(app.config["SETTINGS_PATH"]).exists():
        if app.config["CAST_IP"]:
            settings["cast_ip"] = app.config["CAST_IP"]
        settings["cast_timeout_seconds"] = app.config["CAST_TIMEOUT_SECONDS"]
    app.extensions["user_store"] = user_store
    app.extensions["settings_service"] = settings_service
    app.extensions["media_service"] = MediaService(
        settings_service=settings_service,
        base_directory=app.config["BASE_DIRECTORY"],
        fallback_media_directory=app.config["MEDIA_DIRECTORY"],
    )
    app.extensions["command_rate_limiter"] = CommandRateLimiter(
        app.config["COMMAND_RATE_LIMIT_SECONDS"]
    )
    app.extensions["cast_service"] = CastService(
        cast_ip=settings["cast_ip"],
        timeout_seconds=settings["cast_timeout_seconds"],
    )
    app.extensions["playback_service"] = PlaybackService(
        media_service=app.extensions["media_service"],
        cast_service=app.extensions["cast_service"],
        presets_path=app.config["PRESETS_PATH"],
    )


def _register_extensions(app):
    csrf.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return app.extensions["user_store"].get_by_id(user_id)


def _register_cli(app):
    import click

    @app.cli.command("init-admin")
    @click.option("--username", prompt=True)
    @click.option(
        "--password",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
    )
    def init_admin(username, password):
        user_store = app.extensions["user_store"]
        if user_store.has_users():
            raise click.ClickException("Administrator account already exists")
        user_store.create_admin(username, password)
        click.echo("Administrator account created")
