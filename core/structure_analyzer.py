from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re


@dataclass
class StructureSummary:
    scope_type: str = "unknown"
    entry_points: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    ui_files: list[str] = field(default_factory=list)
    server_files: list[str] = field(default_factory=list)
    client_files: list[str] = field(default_factory=list)
    shared_files: list[str] = field(default_factory=list)
    data_files: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)
    likely_roles: list[str] = field(default_factory=list)
    key_notes: list[str] = field(default_factory=list)
    recommended_context_files: list[str] = field(default_factory=list)


class StructureAnalyzer:
    CODE_EXTS = {".lua", ".js", ".ts", ".html", ".css", ".json"}
    UI_HINT_DIRS = {"html", "web", "ui", "nui", "frontend"}
    DATA_HINT_DIRS = {"data", "sql", "locales", "stream", "audio", "sounds"}
    CONFIG_HINTS = {"config.lua", "settings.lua", "shared/config.lua"}

    def summarize(self, target: Path, working_dir: Path, manifest_text: str = "") -> StructureSummary:
        summary = StructureSummary(scope_type=self._scope_type(target))

        files = self._collect_files(target)
        rel_files = [self._to_rel(path, working_dir) for path in files]

        for rel in rel_files:
            lower = rel.lower()
            parts = lower.split("/")
            filename = parts[-1]

            if any(part in self.UI_HINT_DIRS for part in parts) or filename.endswith((".html", ".css")):
                summary.ui_files.append(rel)
            if any(part == "client" for part in parts) or filename == "client.lua":
                summary.client_files.append(rel)
            if any(part == "server" for part in parts) or filename == "server.lua":
                summary.server_files.append(rel)
            if any(part == "shared" for part in parts) or filename == "shared.lua":
                summary.shared_files.append(rel)
            if any(part in self.DATA_HINT_DIRS for part in parts) or filename.endswith((".json", ".sql")):
                summary.data_files.append(rel)
            if filename in self.CONFIG_HINTS or filename.startswith("config") or "/config/" in lower:
                summary.config_files.append(rel)

            if filename in {"fxmanifest.lua", "__resource.lua", "client.lua", "server.lua", "shared.lua", "config.lua", "main.lua", "init.lua"}:
                summary.entry_points.append(rel)

        if manifest_text:
            self._apply_manifest_hints(summary, manifest_text)

        summary.entry_points = self._dedupe(summary.entry_points)
        summary.config_files = self._dedupe(summary.config_files)
        summary.ui_files = self._dedupe(summary.ui_files)
        summary.server_files = self._dedupe(summary.server_files)
        summary.client_files = self._dedupe(summary.client_files)
        summary.shared_files = self._dedupe(summary.shared_files)
        summary.data_files = self._dedupe(summary.data_files)
        summary.dependencies = self._dedupe(summary.dependencies)
        summary.exports = self._dedupe(summary.exports)

        summary.likely_roles = self._infer_roles(summary)
        summary.key_notes = self._build_notes(summary)
        summary.recommended_context_files = self._recommend_context(summary, rel_files)
        return summary

    def render(self, summary: StructureSummary) -> str:
        blocks: list[str] = [f"Tipo de escopo: {summary.scope_type}"]

        def add(title: str, items: list[str], limit: int = 8) -> None:
            if not items:
                return
            view = items[:limit]
            suffix = "" if len(items) <= limit else f"\n- ... (+{len(items) - limit})"
            blocks.append(title + ":\n- " + "\n- ".join(view) + suffix)

        add("Pontos de entrada prováveis", summary.entry_points)
        add("Arquivos de config", summary.config_files)
        add("Arquivos client", summary.client_files)
        add("Arquivos server", summary.server_files)
        add("Arquivos shared", summary.shared_files)
        add("Arquivos UI/NUI", summary.ui_files)
        add("Arquivos de dados", summary.data_files)
        add("Dependências explícitas", summary.dependencies)
        add("Exports confirmados", summary.exports)
        add("Funções prováveis do escopo", summary.likely_roles)
        add("Notas do analyzer", summary.key_notes, limit=10)
        add("Contexto recomendado", summary.recommended_context_files, limit=12)
        return "\n\n".join(blocks)

    def _scope_type(self, target: Path) -> str:
        if target.is_file():
            return "file"
        names = {child.name.lower() for child in target.iterdir()} if target.is_dir() else set()
        if "fxmanifest.lua" in names or "__resource.lua" in names:
            return "resource"
        return "folder"

    def _collect_files(self, target: Path) -> list[Path]:
        if target.is_file():
            return [target]

        files: list[Path] = []
        for path in sorted(target.rglob("*")):
            if not path.is_file():
                continue
            if any(part.startswith(".") for part in path.parts):
                continue
            if path.suffix.lower() not in self.CODE_EXTS and path.name not in {"fxmanifest.lua", "__resource.lua"}:
                continue
            files.append(path)
        return files[:400]

    def _to_rel(self, path: Path, working_dir: Path) -> str:
        try:
            return path.relative_to(working_dir).as_posix()
        except Exception:
            return path.name

    def _apply_manifest_hints(self, summary: StructureSummary, manifest_text: str) -> None:
        dep_patterns = [r"dependency\s+['\"]([^'\"]+)['\"]", r"dependencies\s*\{([^}]+)\}"]
        export_patterns = [r"exports\s*\{([^}]+)\}", r"server_exports\s*\{([^}]+)\}"]

        for match in re.finditer(r"(?:client|server|shared)_scripts?\s*\{([^}]+)\}", manifest_text, flags=re.I | re.S):
            block = match.group(1)
            for item in re.findall(r"['\"]([^'\"]+)['\"]", block):
                if "client" in match.group(0).lower():
                    summary.client_files.append(item)
                elif "server" in match.group(0).lower():
                    summary.server_files.append(item)
                else:
                    summary.shared_files.append(item)
                summary.entry_points.append(item)

        for single in re.finditer(r"\b(client|server|shared)_script\s+['\"]([^'\"]+)['\"]", manifest_text, flags=re.I):
            kind = single.group(1).lower()
            item = single.group(2)
            summary.entry_points.append(item)
            getattr(summary, f"{kind}_files").append(item)

        ui_page = re.search(r"ui_page\s+['\"]([^'\"]+)['\"]", manifest_text, flags=re.I)
        if ui_page:
            summary.ui_files.append(ui_page.group(1))
            summary.key_notes.append("Manifest confirma uso de ui_page.")

        files_block = re.search(r"files\s*\{([^}]+)\}", manifest_text, flags=re.I | re.S)
        if files_block:
            for item in re.findall(r"['\"]([^'\"]+)['\"]", files_block.group(1)):
                if any(item.lower().endswith(ext) for ext in (".html", ".css", ".js")):
                    summary.ui_files.append(item)

        for pattern in dep_patterns:
            for match in re.finditer(pattern, manifest_text, flags=re.I | re.S):
                values = re.findall(r"['\"]([^'\"]+)['\"]", match.group(0))
                summary.dependencies.extend(values)

        for pattern in export_patterns:
            for match in re.finditer(pattern, manifest_text, flags=re.I | re.S):
                values = re.findall(r"['\"]([^'\"]+)['\"]", match.group(0))
                summary.exports.extend(values)

    def _infer_roles(self, summary: StructureSummary) -> list[str]:
        roles: list[str] = []
        if summary.ui_files:
            roles.append("possui interface NUI/web")
        if summary.client_files and summary.server_files:
            roles.append("fluxo dividido entre client e server")
        elif summary.client_files:
            roles.append("escopo focado em client")
        elif summary.server_files:
            roles.append("escopo focado em server")
        if summary.shared_files:
            roles.append("usa camada shared para config/utilidades")
        if summary.config_files:
            roles.append("tem configuração separada da lógica")
        if summary.dependencies:
            roles.append("depende explicitamente de outros resources")
        if any(item.endswith(".html") for item in summary.ui_files):
            roles.append("frontend embarcado no resource")
        if summary.data_files:
            roles.append("carrega arquivos auxiliares/dados")
        return self._dedupe(roles)

    def _build_notes(self, summary: StructureSummary) -> list[str]:
        notes: list[str] = []
        if not summary.entry_points:
            notes.append("Nenhum ponto de entrada clássico foi confirmado no escopo lido.")
        if summary.ui_files and not summary.client_files:
            notes.append("Há UI, mas o acoplamento com client não ficou explícito só por estrutura.")
        if len(summary.client_files) > 8 or len(summary.server_files) > 8:
            notes.append("Escopo com muitos arquivos de lógica; convém resumir por pasta antes da IA profunda.")
        if summary.dependencies:
            notes.append("As dependências do manifesto devem ser priorizadas no entendimento do fluxo.")
        if summary.config_files and not summary.shared_files:
            notes.append("Config parece isolada sem camada shared explícita.")
        return notes

    def _recommend_context(self, summary: StructureSummary, all_files: list[str]) -> list[str]:
        ordered: list[str] = []
        buckets = [
            summary.entry_points,
            summary.config_files,
            summary.shared_files,
            summary.client_files,
            summary.server_files,
            summary.ui_files,
            summary.data_files,
        ]
        for bucket in buckets:
            for item in bucket:
                if item not in ordered:
                    ordered.append(item)

        if not ordered:
            ordered = all_files[:12]

        return ordered[:12]

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for value in values:
            norm = value.strip()
            if not norm or norm in seen:
                continue
            seen.add(norm)
            out.append(norm)
        return out
