from __future__ import annotations
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import uuid
from core.paths import HISTORY_FILE

class HistoryManager:
    def append(self, payload: dict[str, Any]) -> str:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **payload,
        }
        with HISTORY_FILE.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry["id"]

    def list_recent(self, project_id: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
        if not HISTORY_FILE.exists():
            return []
        lines = [line.strip() for line in HISTORY_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]
        items: list[dict[str, Any]] = []
        for line in lines:
            try:
                item = json.loads(line)
            except Exception:
                continue
            if project_id and item.get("project_id") != project_id:
                continue
            items.append(item)
        return list(reversed(items[-limit:]))

    def get(self, entry_id: str) -> dict[str, Any] | None:
        for item in self.list_recent(limit=5000):
            if item.get("id") == entry_id:
                return item
        return None
