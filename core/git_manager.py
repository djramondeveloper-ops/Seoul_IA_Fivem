from __future__ import annotations
import subprocess
from pathlib import Path

class GitManager:
    def is_git_repo(self, path: str) -> bool:
        try:
            result = subprocess.run(["git", "-C", path, "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True, check=False)
            return result.returncode == 0 and result.stdout.strip().lower() == "true"
        except Exception:
            return False

    def status_short(self, path: str) -> str:
        try:
            result = subprocess.run(["git", "-C", path, "status", "--short"], capture_output=True, text=True, check=False)
            return result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
        except Exception as exc:
            return f"Erro ao consultar git: {exc}"

    def has_problematic_deletions(self, path: str) -> bool:
        status = self.status_short(path)
        if not status:
            return False
        for line in status.splitlines():
            marker = line[:2]
            if "D" in marker or marker == "??":
                return True
        return False

    def init_repo(self, path: str) -> int:
        try:
            result = subprocess.run(["git", "-C", path, "init"], check=False)
            return result.returncode
        except Exception:
            return 1
