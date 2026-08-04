import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional

SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "secret",
    "secret_key",
    "csrf_token",
    "token",
    "cookie",
    "authorization",
    "headers",
    "media_url",
    "content_id",
    "title",
}


class AuditService:
    def __init__(
        self,
        log_path: str,
        max_bytes: int,
        backup_count: int,
        logger_name: str = "audit",
    ):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if logger_name == "audit":
            logger_name = f"audit.{abs(hash(str(self.log_path.resolve())))}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self._ensure_handler(max_bytes, backup_count)
        self._last_app_id: Optional[str] = None

    def record(
        self,
        user: str,
        command: str,
        ok: bool,
        error: str = "",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        payload = {
            "user": user or "anonymous",
            "command": command,
            "ok": bool(ok),
            "error": error,
            "details": _sanitize(details or {}),
        }
        self.logger.info(json.dumps(payload, sort_keys=True))

    def record_app_change(self, user: str, status: Dict[str, Any]) -> None:
        app_id = status.get("app_id")
        if not app_id or app_id == self._last_app_id:
            return
        previous = self._last_app_id
        self._last_app_id = app_id
        self.record(
            user=user,
            command="app_change",
            ok=True,
            details={
                "previous_app_id": previous,
                "app_id": app_id,
                "app_name": status.get("app_name"),
            },
        )

    def recent_entries(
        self,
        limit: int = 20,
        errors_only: bool = False,
    ) -> List[Dict[str, Any]]:
        entries = []
        if not self.log_path.exists():
            return entries
        with self.log_path.open("r", encoding="utf-8") as log_file:
            lines = log_file.readlines()
        for line in reversed(lines):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if errors_only and entry.get("ok") is True:
                continue
            entries.append(entry)
            if len(entries) >= limit:
                break
        return entries

    def _ensure_handler(self, max_bytes: int, backup_count: int) -> None:
        target = str(self.log_path)
        for handler in self.logger.handlers:
            is_target_handler = (
                isinstance(handler, RotatingFileHandler)
                and handler.baseFilename == target
            )
            if is_target_handler:
                return
        handler = RotatingFileHandler(
            target,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            if key.lower() in SENSITIVE_KEYS:
                sanitized[key] = "[redacted]"
            else:
                sanitized[key] = _sanitize(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    return value
