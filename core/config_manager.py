from __future__ import annotations
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any
from core.models import Settings, Session
from core.paths import DATA_DIR, SETTINGS_FILE, PROJECTS_FILE, SESSION_FILE, HISTORY_FILE

class ConfigManager:
    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._ensure_files()

    def _ensure_files(self) -> None:
        if not SETTINGS_FILE.exists():
            self.save_settings(Settings())
        if not PROJECTS_FILE.exists():
            PROJECTS_FILE.write_text(json.dumps({"projects": []}, indent=2, ensure_ascii=False), encoding="utf-8")
        if not SESSION_FILE.exists():
            self.save_session(Session())
        if not HISTORY_FILE.exists():
            HISTORY_FILE.write_text("", encoding="utf-8")

    def load_json(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def save_json(self, path: Path, payload: Any) -> None:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def load_settings(self) -> Settings:
        data = self.load_json(SETTINGS_FILE)
        defaults = Settings().__dict__.copy()
        defaults.update(data)
        return Settings(**defaults)

    def save_settings(self, settings: Settings) -> None:
        self.save_json(SETTINGS_FILE, asdict(settings))

    def load_projects_payload(self) -> dict[str, Any]:
        return self.load_json(PROJECTS_FILE)

    def save_projects_payload(self, payload: dict[str, Any]) -> None:
        self.save_json(PROJECTS_FILE, payload)

    def load_session(self) -> Session:
        data = self.load_json(SESSION_FILE)
        defaults = Session().__dict__.copy()
        defaults.update(data)
        return Session(**defaults)

    def save_session(self, session: Session) -> None:
        self.save_json(SESSION_FILE, asdict(session))
