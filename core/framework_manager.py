from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from core.paths import FRAMEWORK_REGISTRY_FILE

class FrameworkManager:
    def __init__(self) -> None:
        self.registry = self._load_registry()

    def _load_registry(self) -> dict[str, Any]:
        return json.loads(FRAMEWORK_REGISTRY_FILE.read_text(encoding="utf-8"))

    def names(self) -> list[str]:
        return list(self.registry["frameworks"].keys())

    def get(self, name: str) -> dict[str, Any]:
        return self.registry["frameworks"].get(name, {})

    def recommended_aiderignore(self, framework_name: str) -> list[str]:
        return self.get(framework_name).get("default_ignore_patterns", [])
