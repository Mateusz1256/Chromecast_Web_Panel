import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask

from app.blueprints.health import health_bp
from app.config import AppConfig
from app.services.cast_service import CastService


def create_app(config_object=AppConfig):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    _ensure_runtime_directories(app)
    _configure_logging(app)
    _register_services(app)

    app.register_blueprint(health_bp)
    return app


def _ensure_runtime_directories(app):
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
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
    app.extensions["cast_service"] = CastService(
        cast_ip=app.config["CAST_IP"],
        timeout_seconds=app.config["CAST_TIMEOUT_SECONDS"],
    )
