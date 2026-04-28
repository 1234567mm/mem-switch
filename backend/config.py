import os
import platform
import yaml
from pathlib import Path


def get_app_data_dir() -> Path:
    sys = platform.system()
    if sys == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"
    return base / "Mem-Switch"


APP_DATA_DIR = get_app_data_dir()
CONFIG_FILE = APP_DATA_DIR / "config.yaml"
SQLITE_DIR = APP_DATA_DIR / "sqlite"
QDRANT_DIR = APP_DATA_DIR / "qdrant_storage"
DOCUMENTS_DIR = APP_DATA_DIR / "documents"
IMPORTS_DIR = APP_DATA_DIR / "imports"
LOGS_DIR = APP_DATA_DIR / "logs"

BACKEND_PORT = 8765
BACKEND_HOST = "127.0.0.1"


class AppConfig:
    def __init__(self):
        self._config = {}
        self._ensure_dirs()
        self._load()

    def _ensure_dirs(self):
        for d in [APP_DATA_DIR, SQLITE_DIR, QDRANT_DIR,
                  DOCUMENTS_DIR, IMPORTS_DIR, LOGS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    def _defaults(self) -> dict:
        return {
            "ollama_host": "http://127.0.0.1:11434",
            "llm_model": "",
            "embedding_model": "nomic-embed-text",
            "qdrant_host": "localhost",
            "qdrant_port": 6333,
            "memory_expiry_days": 180,
            "extract_dimensions": ["preference", "expertise", "project_context"],
        }

    def _load(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = self._defaults()
            self._save()

    def _save(self):
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)

    def get(self, key: str, default=None):
        return self._config.get(key, default)

    def set(self, key: str, value):
        self._config[key] = value
        self._save()

    def update(self, data: dict):
        self._config.update(data)
        self._save()

    def as_dict(self) -> dict:
        return dict(self._config)


config = AppConfig()
