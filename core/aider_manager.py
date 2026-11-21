from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass
class AiderRunResult:
    returncode: int
    output: str
    auto_replied_prompts: int = 0
    asked_for_input: bool = False
    detected_prompts: list[str] = field(default_factory=list)
    command: list[str] = field(default_factory=list)
    scope_dir: str = ""

    @property
    def code(self) -> int:
        return self.returncode


class AiderManager:
    EXCLUDED_NAMES = {
        "README.md",
        "EXAMPLES.md",
        "TEMPLATES.md",
    }

    EXCLUDED_DIRS = {
        ".github",
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
    }

    EXCLUDED_SUFFIXES = {
        ".pyc",
        ".pyo",
        ".pyd",
    }

    INTERACTIVE_PROMPT_HINTS = (
        "add file to the chat",
        "press enter to return",
        "continue?",
        "are you sure",
        "select files",
    )

    def _read_base_aiderignore(self) -> list[str]:
        template_path = Path(__file__).resolve().parent.parent / "templates" / "aiderignore.txt"
        if not template_path.exists():
            return []
        try:
            lines = template_path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return []
        return [line.strip() for line in lines if line.strip()]

    def _write_scoped_aiderignore(self, scope_dir: Path, framework_ignore: Iterable[str] | None = None) -> Path | None:
        ignore_path = scope_dir / ".aiderignore"
        base_lines = self._read_base_aiderignore() or [
            ".github/",
            "__pycache__/",
            ".git/",
            ".venv/",
            "venv/",
            "node_modules/",
            "README.md",
            "EXAMPLES.md",
            "TEMPLATES.md",
            "*.pyc",
            "*.pyo",
            "*.pyd",
        ]

        merged: list[str] = []
        seen: set[str] = set()
        for line in [*base_lines, *(framework_ignore or [])]:
            clean = (line or "").strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            merged.append(clean)

        try:
            ignore_path.write_text("\n".join(merged) + "\n", encoding="utf-8")
            return ignore_path
        except Exception:
            return None

    def _is_excluded(self, path: Path) -> bool:
        if path.name in self.EXCLUDED_NAMES:
            return True
        if path.suffix.lower() in self.EXCLUDED_SUFFIXES:
            return True
        return any(part in self.EXCLUDED_DIRS for part in path.parts)

    def _normalize_read_files(self, repo_root: Path, scope_dir: Path, read_files: Iterable[str | Path] | None) -> list[str]:
        if not read_files:
            return []

        normalized: list[str] = []
        seen: set[str] = set()
        repo_root_resolved = repo_root.resolve()
        scope_dir_resolved = scope_dir.resolve()

        for raw in read_files:
            p = Path(raw)
            candidates: list[Path] = []
            if p.is_absolute():
                candidates.append(p)
            else:
                candidates.append(scope_dir_resolved / p)
                candidates.append(repo_root_resolved / p)

            abs_path: Path | None = None
            for candidate in candidates:
                try:
                    resolved = candidate.resolve()
                except Exception:
                    resolved = candidate.absolute()
                if resolved.exists():
                    abs_path = resolved
                    break

            if abs_path is None:
                try:
                    abs_path = (scope_dir_resolved / p).resolve()
                except Exception:
                    abs_path = (scope_dir_resolved / p).absolute()

            try:
                rel_to_scope = abs_path.relative_to(scope_dir_resolved)
            except Exception:
                continue

            if self._is_excluded(rel_to_scope):
                continue

            rel_norm = rel_to_scope.as_posix()
            if rel_norm not in seen:
                seen.add(rel_norm)
                normalized.append(rel_norm)
        return normalized

    def _build_command(self, repo_root: Path, scope_dir: Path, model: str, prompt: str, settings, read_files: Iterable[str | Path] | None = None, subtree_only: bool = True, map_tokens: int = 0, framework_ignore: Iterable[str] | None = None) -> list[str]:
        model_name = model if str(model).startswith(("ollama/", "gemini/", "openai/")) else f"ollama/{model}"
        cmd: list[str] = [
            settings.aider_command,
            "--model",
            model_name,
            "--yes-always",
            "--message",
            prompt,
            "--encoding",
            "utf-8",
            "--no-show-model-warnings",
        ]
        if subtree_only:
            cmd.append("--subtree-only")
        if map_tokens >= 0:
            cmd.extend(["--map-tokens", str(map_tokens)])

        ignore_path = None
        if getattr(settings, "auto_create_aiderignore", True):
            ignore_path = self._write_scoped_aiderignore(scope_dir, framework_ignore=framework_ignore)
        if ignore_path is not None:
            cmd.extend(["--aiderignore", str(ignore_path)])

        for rel_path in self._normalize_read_files(repo_root, scope_dir, read_files):
            cmd.extend(["--read", rel_path])
        return cmd

    def _detect_interactive_prompts(self, text: str) -> list[str]:
        normalized = (text or "").lower()
        found: list[str] = []
        for hint in self.INTERACTIVE_PROMPT_HINTS:
            if hint in normalized and hint not in found:
                found.append(hint)
        return found

    def launch(self, repo_path: str, model: str, prompt: str, settings, *, working_dir: str | None = None, cwd: str | None = None, read_files: Iterable[str | Path] | None = None, subtree_only: bool = True, map_tokens: int = 0, framework_ignore: Iterable[str] | None = None) -> AiderRunResult:
        repo_root = Path(repo_path).resolve()
        effective_dir = working_dir or cwd
        scope_dir = Path(effective_dir).resolve() if effective_dir else repo_root

        cmd = self._build_command(
            repo_root=repo_root,
            scope_dir=scope_dir,
            model=model,
            prompt=prompt,
            settings=settings,
            read_files=read_files,
            subtree_only=subtree_only,
            map_tokens=map_tokens,
            framework_ignore=framework_ignore,
        )

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env.pop("TERM", None)
        # Credentials stay in environment variables, not arguments or project files.
        if model.startswith("gemini/") and not env.get("GEMINI_API_KEY"):
            msg = "GEMINI_API_KEY ausente. Configure a variavel de ambiente para usar Gemini."
            print(msg)
            return AiderRunResult(returncode=2, output=msg, command=cmd, scope_dir=str(scope_dir))
        if model.startswith("openai/") and not env.get("OPENAI_API_KEY"):
            msg = "OPENAI_API_KEY ausente. Configure a variavel de ambiente para usar OpenAI."
            print(msg)
            return AiderRunResult(returncode=2, output=msg, command=cmd, scope_dir=str(scope_dir))
        if model.startswith("ollama/") or "/" not in model:
            env["OLLAMA_API_BASE"] = settings.ollama_api_base

        try:
            process = subprocess.Popen(
                cmd,
                cwd=str(scope_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
            )
        except FileNotFoundError:
            msg = f"Comando do Aider não encontrado: {settings.aider_command}"
            print(msg)
            return AiderRunResult(returncode=1, output=msg, auto_replied_prompts=0, command=cmd, scope_dir=str(scope_dir))
        except Exception as e:
            msg = f"Erro ao abrir Aider: {e}"
            print(msg)
            return AiderRunResult(returncode=1, output=msg, auto_replied_prompts=0, command=cmd, scope_dir=str(scope_dir))

        output_chunks: list[str] = []
        detected_prompts: list[str] = []
        if process.stdout is not None:
            for line in process.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                output_chunks.append(line)
                for hint in self._detect_interactive_prompts(line):
                    if hint not in detected_prompts:
                        detected_prompts.append(hint)

        code = process.wait()
        return AiderRunResult(
            returncode=code,
            output="".join(output_chunks),
            auto_replied_prompts=0,
            asked_for_input=bool(detected_prompts),
            detected_prompts=detected_prompts,
            command=cmd,
            scope_dir=str(scope_dir),
        )
