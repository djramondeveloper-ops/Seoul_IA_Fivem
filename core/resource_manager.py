from __future__ import annotations

from pathlib import Path

from core.models import ResourceInspection
from core.file_scoper import FileScoper
from core.structure_analyzer import StructureAnalyzer
from core.task_router import TaskRouter
from core.context_meter import ContextMeter
from core.file_summarizer import FileSummarizer


class ResourceManager:
    def __init__(self) -> None:
        self.structure = StructureAnalyzer()
        self.scoper = FileScoper()
        self.router = TaskRouter()
        self.context_meter = ContextMeter()
        self.file_summarizer = FileSummarizer()

    EXCLUDED_DIRS = {".git", ".github", "__pycache__", "node_modules", ".idea", ".vscode"}
    EXCLUDED_FILES = {"README.md", "EXAMPLES.md", "TEMPLATES.md"}
    ALLOWED_CODE_EXTS = {".lua", ".js", ".html", ".css", ".json", ".md"}

    def _resources_root(self, repo_path: str) -> Path:
        return Path(repo_path) / "resources"

    def list_resources(self, repo_path: str) -> list[tuple[str, Path]]:
        root = self._resources_root(repo_path)
        if not root.exists():
            return []

        found: list[tuple[str, Path]] = []
        for path in root.rglob("*"):
            if not path.is_dir():
                continue
            if path.name.startswith("."):
                continue
            if (path / "fxmanifest.lua").exists() or (path / "__resource.lua").exists():
                found.append((path.name, path))

        found.sort(key=lambda item: item[0].lower())
        return found

    def list_custom_resources(self, repo_path: str, prefix: str) -> list[tuple[str, Path]]:
        return [item for item in self.list_resources(repo_path) if item[0].startswith(prefix)]

    def find_resource(self, repo_path: str, resource_name: str) -> Path | None:
        matches = [
            path
            for name, path in self.list_resources(repo_path)
            if name.lower() == resource_name.lower()
        ]
        return matches[0] if matches else None

    def suggest_resources(self, repo_path: str, needle: str, limit: int = 10) -> list[str]:
        needle = needle.lower()
        names = [name for name, _ in self.list_resources(repo_path)]
        starts = [n for n in names if n.lower().startswith(needle)]
        contains = [n for n in names if needle in n.lower() and n not in starts]
        return (starts + contains)[:limit]

    def inspect_resource(
        self,
        repo_path: str,
        resource_name: str,
        subpath: str = "",
        objective: str = "entender a estrutura",
        user_input: str = "",
        lock_objective: bool = True,
    ) -> ResourceInspection | None:
        resource_path = self.find_resource(repo_path, resource_name)
        if not resource_path:
            return None

        target = resource_path / subpath if subpath else resource_path
        if not target.exists():
            return None

        repo = Path(repo_path)
        rel = target.relative_to(repo).as_posix()
        working_dir = target if target.is_dir() else target.parent

        manifest = resource_path / "fxmanifest.lua"
        if not manifest.exists():
            manifest = resource_path / "__resource.lua"

        manifest_text = self._read_limited(manifest, max_chars=3000) if manifest.exists() else ""
        manifest_rel = ""
        if manifest.exists():
            try:
                manifest_rel = manifest.relative_to(working_dir).as_posix()
            except Exception:
                manifest_rel = manifest.name

        intent = self.router.route(user_input or objective)
        resolved_objective = objective.strip() if objective and lock_objective else intent.objective

        warnings: list[str] = []
        if subpath and target.is_file():
            warnings.append("Escopo restrito a um arquivo específico.")
        elif subpath and target.is_dir():
            warnings.append("Escopo restrito a uma pasta específica do resource.")

        warnings.append(
            f"Objetivo aplicado: {resolved_objective}. Origem: {'manual' if lock_objective else 'roteamento automático'}."
        )
        warnings.append(f"Leitura da intenção: {intent.task_type} (confiança {intent.confidence}).")
        warnings.append(intent.reason)

        tree = self._build_tree(target, max_depth=4, max_entries=120)
        key_files = self._collect_key_files(target, working_dir)
        analyzed = self.structure.summarize(target, working_dir, manifest_text)
        structure_summary = self.structure.render(analyzed)
        structure_data = {
            "scope_type": analyzed.scope_type,
            "entry_points": analyzed.entry_points,
            "config_files": analyzed.config_files,
            "ui_files": analyzed.ui_files,
            "client_files": analyzed.client_files,
            "server_files": analyzed.server_files,
            "shared_files": analyzed.shared_files,
            "data_files": analyzed.data_files,
            "dependencies": analyzed.dependencies,
            "exports": analyzed.exports,
            "likely_roles": analyzed.likely_roles,
            "key_notes": analyzed.key_notes,
            "recommended_context_files": analyzed.recommended_context_files,
        }

        seed_inspection = ResourceInspection(
            name=resource_name,
            abs_path=str(target),
            rel_path=rel,
            tree=tree,
            working_dir=str(working_dir),
            display_root="." if target == working_dir else target.name,
            manifest_path=manifest_rel,
            manifest_text=manifest_text,
            key_files=key_files,
            context_files=[],
            structure_summary=structure_summary,
            structure_data=structure_data,
            warnings=warnings,
            objective=resolved_objective,
            task_intent=intent.__dict__.copy(),
        )
        scoped = self.scoper.select(seed_inspection, objective=resolved_objective)
        context_files = scoped.selected_files or analyzed.recommended_context_files or key_files

        inspection = ResourceInspection(
            name=resource_name,
            abs_path=str(target),
            rel_path=rel,
            tree=tree,
            working_dir=str(working_dir),
            display_root="." if target == working_dir else target.name,
            manifest_path=manifest_rel,
            manifest_text=manifest_text,
            key_files=key_files,
            context_files=context_files,
            structure_summary=structure_summary,
            structure_data=structure_data,
            scope_strategy=self.scoper.render(scoped),
            warnings=warnings,
            objective=resolved_objective,
            task_intent=intent.__dict__.copy(),
        )

        inspection.confirmed_facts = self._build_confirmed_facts(inspection)
        inspection.inferred_facts = self._build_inferred_facts(inspection)
        inspection.not_confirmed = self._build_not_confirmed(inspection)
        inspection.scope_validation = self._validate_scope(inspection, intent)
        inspection.warnings.extend(item for item in inspection.scope_validation if item not in inspection.warnings)

        summaries = self.file_summarizer.summarize_many(working_dir, inspection.context_files)
        inspection.file_summaries = [summary.__dict__ for summary in summaries]
        inspection.file_summaries_text = self.file_summarizer.render_many(summaries)

        context_report = self.context_meter.limit(inspection, objective=resolved_objective)
        inspection.context_estimate = {
            "estimated_tokens": context_report.estimated_tokens,
            "max_tokens": context_report.max_tokens,
            "usage_percent": context_report.usage_percent,
            "selected_files_before": context_report.selected_files_before,
            "selected_files_after": context_report.selected_files_after,
            "removed_files": context_report.removed_files,
            "notes": context_report.notes,
        }
        inspection.context_status = context_report.status
        inspection.was_limited = context_report.was_limited
        if context_report.notes:
            inspection.warnings.extend(note for note in context_report.notes if note not in inspection.warnings)

        if context_report.was_limited:
            summaries = self.file_summarizer.summarize_many(working_dir, inspection.context_files)
            inspection.file_summaries = [summary.__dict__ for summary in summaries]
            inspection.file_summaries_text = self.file_summarizer.render_many(summaries)

        return inspection

    def _build_confirmed_facts(self, inspection: ResourceInspection) -> list[str]:
        data = inspection.structure_data or {}
        facts: list[str] = []
        if inspection.manifest_path:
            facts.append(f"Manifesto detectado em {inspection.manifest_path}.")
        if data.get("entry_points"):
            facts.append(f"Pontos de entrada confirmados: {', '.join(data['entry_points'][:6])}.")
        if data.get("client_files"):
            facts.append(f"Há arquivos client no escopo: {', '.join(data['client_files'][:4])}.")
        if data.get("server_files"):
            facts.append(f"Há arquivos server no escopo: {', '.join(data['server_files'][:4])}.")
        if data.get("shared_files"):
            facts.append(f"Há camada shared no escopo: {', '.join(data['shared_files'][:4])}.")
        if data.get("ui_files"):
            facts.append(f"Há arquivos de UI/NUI no escopo: {', '.join(data['ui_files'][:4])}.")
        if data.get("dependencies"):
            facts.append(f"Dependências explícitas no manifesto: {', '.join(data['dependencies'][:6])}.")
        if data.get("exports"):
            facts.append(f"Exports confirmados pelo manifesto: {', '.join(data['exports'][:6])}.")
        return facts

    def _build_inferred_facts(self, inspection: ResourceInspection) -> list[str]:
        data = inspection.structure_data or {}
        inferred: list[str] = []
        if data.get("likely_roles"):
            inferred.extend(f"Inferência estrutural: {item}." for item in data["likely_roles"][:6])
        if data.get("key_notes"):
            inferred.extend(f"Nota inferida pelo analyzer: {item}" for item in data["key_notes"][:4])
        return inferred

    def _build_not_confirmed(self, inspection: ResourceInspection) -> list[str]:
        data = inspection.structure_data or {}
        pending: list[str] = [
            "Fluxo completo de eventos/callbacks não foi confirmado só pela estrutura.",
            "Validação server-side de eventos e permissões não foi confirmada neste primeiro passe.",
        ]
        if data.get("ui_files") and not data.get("client_files"):
            pending.append("O acoplamento real entre UI e client não ficou confirmado apenas pela estrutura.")
        if not inspection.file_summaries:
            pending.append("Não houve resumo de arquivos suficiente para confirmar a lógica central.")
        return pending

    def _validate_scope(self, inspection: ResourceInspection, intent) -> list[str]:
        data = inspection.structure_data or {}
        msgs: list[str] = []
        scope_type = data.get("scope_type", "")
        if intent.suggested_scope == "resource" and scope_type == "file":
            msgs.append("Escopo provavelmente estreito demais para o objetivo atual; um resource inteiro tende a ser mais seguro.")
        if inspection.objective == "revisar NUI" and data.get("ui_files") and not data.get("client_files"):
            msgs.append("Revisão NUI sem client suficiente; convém incluir o arquivo que chama SendNUIMessage/RegisterNUICallback.")
        if inspection.objective == "procurar problemas" and data.get("client_files") and not data.get("server_files"):
            msgs.append("Debug parcial: há client, mas o server não entrou no primeiro passe e pode conter a causa real.")
        if inspection.objective == "comparar com framework" and not inspection.manifest_path:
            msgs.append("Comparação sem manifesto detectado perde qualidade; convém revisar o root do resource.")
        return msgs

    def _read_limited(self, path: Path, max_chars: int = 3000) -> str:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return ""
        return content[:max_chars].strip()

    def _is_excluded(self, path: Path) -> bool:
        if path.name in self.EXCLUDED_FILES:
            return True
        if path.suffix.lower() == ".sql":
            return True
        return any(part in self.EXCLUDED_DIRS for part in path.parts)

    def _collect_key_files(self, target: Path, working_dir: Path) -> list[str]:
        if target.is_file():
            return [target.relative_to(working_dir).as_posix()]

        candidates: list[Path] = []
        priority_names = [
            "fxmanifest.lua",
            "__resource.lua",
            "config.lua",
            "shared.lua",
            "client.lua",
            "server.lua",
            "init.lua",
        ]
        for name in priority_names:
            p = target / name
            if p.exists() and not self._is_excluded(p):
                candidates.append(p)

        for folder in ["client", "server", "shared", "config", "html", "web", "locales", "data"]:
            d = target / folder
            if d.exists() and d.is_dir() and not self._is_excluded(d):
                for child in sorted(d.rglob("*")):
                    if not child.is_file() or self._is_excluded(child):
                        continue
                    if child.suffix.lower() not in self.ALLOWED_CODE_EXTS:
                        continue
                    candidates.append(child)

        for child in sorted(target.iterdir()):
            if not child.is_file() or self._is_excluded(child):
                continue
            if child.suffix.lower() not in self.ALLOWED_CODE_EXTS:
                continue
            candidates.append(child)

        seen: set[str] = set()
        rels: list[str] = []
        for p in candidates:
            rel = p.relative_to(working_dir).as_posix()
            if rel not in seen:
                seen.add(rel)
                rels.append(rel)
        return rels[:24]

    def _build_tree(self, root: Path, max_depth: int = 4, max_entries: int = 120) -> str:
        lines: list[str] = ["."]
        count = 0

        def walk(path: Path, prefix: str = "", depth: int = 0) -> None:
            nonlocal count
            if count >= max_entries or depth > max_depth:
                return
            try:
                entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
            except Exception:
                return

            visible = [e for e in entries if not e.name.startswith(".") and not self._is_excluded(e)]
            for idx, entry in enumerate(visible):
                if count >= max_entries:
                    lines.append(prefix + "└── ...")
                    return
                branch = "└── " if idx == len(visible) - 1 else "├── "
                label = entry.name + ("/" if entry.is_dir() else "")
                lines.append(prefix + branch + label)
                count += 1
                if entry.is_dir() and depth < max_depth:
                    ext = "    " if idx == len(visible) - 1 else "│   "
                    walk(entry, prefix + ext, depth + 1)

        if root.is_dir():
            walk(root)
        return "\n".join(lines)
