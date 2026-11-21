from __future__ import annotations
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = APP_ROOT / "data"
FRAMEWORKS_DIR = APP_ROOT / "frameworks"
INTERNAL_DIR = APP_ROOT / "internal"
PROMPTS_DIR = APP_ROOT / "prompts"
TEMPLATES_DIR = APP_ROOT / "templates"
SCRIPTS_DIR = APP_ROOT / "scripts"

SETTINGS_FILE = DATA_DIR / "settings.json"
PROJECTS_FILE = DATA_DIR / "projects.json"
SESSION_FILE = DATA_DIR / "session.json"
HISTORY_FILE = DATA_DIR / "history.jsonl"
FRAMEWORK_REGISTRY_FILE = FRAMEWORKS_DIR / "registry.json"
DEFAULT_AIDERIGNORE = TEMPLATES_DIR / "aiderignore.txt"
