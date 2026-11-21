from __future__ import annotations
import platform
import shutil
import subprocess
from core.models import EnvironmentStatus, Settings
from core.ollama_manager import OllamaManager

class EnvironmentManager:
    def __init__(self) -> None:
        self.ollama = OllamaManager()

    def check(self, settings: Settings) -> EnvironmentStatus:
        status = EnvironmentStatus()
        status.python_version = platform.python_version()
        status.git_found = shutil.which("git") is not None
        status.ollama_found = shutil.which("ollama") is not None
        status.aider_found = shutil.which(settings.aider_command) is not None

        if status.ollama_found:
            try:
                result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
                status.ollama_running = result.returncode == 0
            except Exception:
                status.ollama_running = False
        if status.ollama_running:
            status.installed_models = self.ollama.list_models()

        if not status.git_found:
            status.issues.append("Git não encontrado no PATH.")
        if not status.ollama_found:
            status.issues.append("Ollama não encontrado no PATH.")
        elif not status.ollama_running:
            status.issues.append("Ollama encontrado, mas o comando 'ollama list' falhou.")
        if not status.aider_found:
            status.issues.append(f"Comando do Aider não encontrado: {settings.aider_command}")

        return status
