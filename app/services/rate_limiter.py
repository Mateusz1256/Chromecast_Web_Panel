import threading
import time
from typing import Dict


class RateLimitExceeded(ValueError):
    pass


class CommandRateLimiter:
    def __init__(self, interval_seconds: float):
        self.interval_seconds = interval_seconds
        self._lock = threading.Lock()
        self._last_seen: Dict[str, float] = {}

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            previous = self._last_seen.get(key)
            if previous is not None and now - previous < self.interval_seconds:
                raise RateLimitExceeded("Command rate limit exceeded")
            self._last_seen[key] = now

