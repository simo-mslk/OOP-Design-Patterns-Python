"""Singleton pattern - configuration manager refactor.

Problems of the original code:
- config.json is read from disk 4 times for one request (slow, useless I/O)
- no shared state: every module has its own dict
- changes are not synchronized: a module that edits its copy is alone to see it
- hard to mock in tests: load_config() is called everywhere, no single point to override
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Optional

CONFIG_FILE = Path(__file__).with_name("config.json")
_MISSING = object()


class ConfigManager:
    _instance: Optional[ConfigManager] = None
    _lock = threading.Lock()     # two threads calling get_instance() at the same time -> still 1 instance

    def __new__(cls, *args, **kwargs):
        # Even ConfigManager() gives back the existing object
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:          # double-checked locking
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, path: Optional[Path] = None):
        if self._initialized:                      # __init__ runs on every ConfigManager() call
            return
        self.path = Path(path or CONFIG_FILE)
        self.load_count = 0
        self._data: dict = {}
        self.reload()
        self._initialized = True

    @classmethod
    def get_instance(cls) -> ConfigManager:
        return cls()

    def reload(self) -> None:
        """Read the file (once at start, or on purpose if the file changed)."""
        with open(self.path, encoding="utf-8") as file:
            self._data = json.load(file)
        self.load_count += 1
        print(f"[config] {self.path.name} loaded (load #{self.load_count})")

    def get(self, key: str, default: Any = None) -> Any:
        """Dotted path into the nested dict: get("database.host") -> "localhost"."""
        node: Any = self._data
        for part in key.split("."):
            node = node.get(part, _MISSING) if isinstance(node, dict) else _MISSING
            if node is _MISSING:
                return default
        return node

    def set(self, key: str, value: Any) -> None:
        """Change a value in memory; every module sees it because they share the instance."""
        *path, last = key.split(".")
        node = self._data
        for part in path:
            node = node.setdefault(part, {})
        node[last] = value

    @classmethod
    def _reset_for_tests(cls) -> None:
        """Tests need a fresh instance (e.g. to load a temporary config file)."""
        cls._instance = None


# ---------------------------------------------------------------------------
# The 4 "modules" of the app, now all using the same instance
# ---------------------------------------------------------------------------

# database.py
def connect_database():
    config = ConfigManager.get_instance()
    print(f"Connecting to database at {config.get('database.host')}:{config.get('database.port')}")


# email_service.py
def send_email(to: str, subject: str):
    config = ConfigManager.get_instance()
    print(f"Sending email from {config.get('email.sender')} via {config.get('email.smtp_host')}")


# payment_service.py
def process_payment(amount: float):
    config = ConfigManager.get_instance()
    print(f"Processing {amount}€ in {config.get('payment.environment')} mode")


# app.py
def start_application():
    config = ConfigManager.get_instance()
    print(f"Starting {config.get('app.name')} (debug={config.get('app.debug')})")


if __name__ == "__main__":
    start_application()          # first access: the file is read here
    connect_database()           # same instance, no new read
    send_email("user@test.com", "Welcome")

    ConfigManager.get_instance().set("payment.environment", "production")
    process_payment(99.99)       # sees the change made above

    config = ConfigManager.get_instance()
    print("same object:", config is ConfigManager() is ConfigManager.get_instance())
    print("file read", config.load_count, "time(s)")
    print("missing key with default:", config.get("cache.ttl", 300))
