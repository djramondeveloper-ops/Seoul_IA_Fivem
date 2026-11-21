from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.models import Project
from core.paths import TEMPLATES_DIR


@dataclass
class ScaffoldResult:
    resource_name: str
    flavor: str
    resource_path: str
    target_root: str
    created_files: list[str] = field(default_factory=list)
    created_dirs: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ResourceScaffolder:
    FLAVOR_MAP = {
        "básico": "basic",
        "basico": "basic",
        "basic": "basic",
        "com banco": "db",
        "db": "db",
        "database": "db",
        "com nui": "nui",
        "nui": "nui",
        "com banco + nui": "db_nui",
        "admin/staff": "admin",
        "phone app": "phone_app",
    }

    def scaffold(self, project: Project, resource_name: str, flavor: str, target_dir: str | None = None) -> ScaffoldResult:
        resource_name = (resource_name or "").strip()
        if not resource_name:
            raise ValueError("Nome do resource não informado.")
        safe_name = self._sanitize_name(resource_name)
        flavor_key = self.FLAVOR_MAP.get((flavor or "").strip().lower(), "basic")
        template_flavor = self._template_flavor(flavor_key)

        root = Path(target_dir) if target_dir else self._detect_target_root(Path(project.repo_path))
        resource_path = root / safe_name
        if resource_path.exists():
            raise FileExistsError(f"O resource '{safe_name}' já existe em {resource_path}.")

        result = ScaffoldResult(
            resource_name=safe_name,
            flavor=flavor_key,
            resource_path=str(resource_path),
            target_root=str(root),
        )

        dirs = self._directories_for_flavor(flavor_key)
        for rel_dir in dirs:
            directory = resource_path / rel_dir if rel_dir != "." else resource_path
            directory.mkdir(parents=True, exist_ok=True)
            result.created_dirs.append(directory.relative_to(root).as_posix())

        context = {
            "RESOURCE_NAME": safe_name,
            "FRAMEWORK": project.framework,
            "DATABASE": project.database,
            "CUSTOM_PREFIX": project.custom_prefix,
        }

        for rel_path, tpl_name in self._files_for_flavor(flavor_key):
            template_path = TEMPLATES_DIR / "qbcore_resource" / template_flavor / tpl_name
            rendered_rel_path = self._render_template(rel_path, context)
            target_path = resource_path / rendered_rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            content = self._render_template(template_path.read_text(encoding="utf-8"), context)
            target_path.write_text(content, encoding="utf-8")
            result.created_files.append(target_path.relative_to(root).as_posix())

        if flavor_key in {"db_nui", "admin", "phone_app"}:
            result.warnings.append(
                "Foi usada a base mais próxima disponível nesta V1. A IA deve completar a especialização desse tipo."
            )

        return result

    def _template_flavor(self, flavor_key: str) -> str:
        if flavor_key in {"basic"}:
            return "basic"
        if flavor_key in {"db"}:
            return "db"
        return "nui"

    def _directories_for_flavor(self, flavor_key: str) -> list[str]:
        dirs = [".", "client", "server", "shared"]
        if flavor_key in {"db", "db_nui"}:
            dirs.append("sql")
        if flavor_key in {"nui", "db_nui", "admin", "phone_app"}:
            dirs.append("web")
        return dirs

    def _files_for_flavor(self, flavor_key: str) -> list[tuple[str, str]]:
        if flavor_key == "basic":
            return [
                ("fxmanifest.lua", "fxmanifest.lua.tpl"),
                ("client/main.lua", "client_main.lua.tpl"),
                ("server/main.lua", "server_main.lua.tpl"),
                ("shared/config.lua", "shared_config.lua.tpl"),
            ]
        if flavor_key == "db":
            return [
                ("fxmanifest.lua", "fxmanifest.lua.tpl"),
                ("client/main.lua", "client_main.lua.tpl"),
                ("server/main.lua", "server_main.lua.tpl"),
                ("shared/config.lua", "shared_config.lua.tpl"),
                ("sql/{{RESOURCE_NAME}}.sql", "sql.sql.tpl"),
            ]
        return [
            ("fxmanifest.lua", "fxmanifest.lua.tpl"),
            ("client/main.lua", "client_main.lua.tpl"),
            ("server/main.lua", "server_main.lua.tpl"),
            ("shared/config.lua", "shared_config.lua.tpl"),
            ("web/index.html", "web_index.html.tpl"),
            ("web/style.css", "web_style.css.tpl"),
            ("web/app.js", "web_app.js.tpl"),
        ]

    def _detect_target_root(self, repo_path: Path) -> Path:
        candidates = [
            repo_path / "resources" / "[local]",
            repo_path / "resources" / "[standalone]",
            repo_path / "resources",
            repo_path,
        ]
        for path in candidates:
            if path.exists() and path.is_dir():
                return path
        return repo_path

    def _render_template(self, text: str, context: dict[str, str]) -> str:
        rendered = text
        for key, value in context.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", value)
        return rendered

    def _sanitize_name(self, value: str) -> str:
        cleaned = value.strip().replace(" ", "_")
        return "".join(ch for ch in cleaned if ch.isalnum() or ch in {"_", "-", "[", "]"})
