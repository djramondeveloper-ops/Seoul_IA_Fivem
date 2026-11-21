from __future__ import annotations
import json
import subprocess

class OllamaManager:
    def list_models(self) -> list[str]:
        try:
            result = subprocess.run(["ollama", "list", "--json"], capture_output=True, text=True, check=False)
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    models = data.get("models", [])
                    return [item.get("name", "") for item in models if item.get("name")]
        except Exception:
            pass

        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, check=False)
            if result.returncode != 0:
                return []
            lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
            if not lines:
                return []
            models: list[str] = []
            for line in lines[1:]:
                first = line.split()[0].strip()
                if first:
                    models.append(first)
            return models
        except Exception:
            return []

    def pull_model(self, model_name: str) -> int:
        try:
            result = subprocess.run(["ollama", "pull", model_name], check=False)
            return result.returncode
        except FileNotFoundError:
            print("Ollama não encontrado no PATH.")
            return 1
        except Exception as exc:
            print(f"Erro ao baixar modelo: {exc}")
            return 1
