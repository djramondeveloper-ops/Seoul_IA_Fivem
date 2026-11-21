from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Settings:
    ollama_api_base: str = "http://localhost:11434"
    aider_command: str = "aider"
    default_framework: str = "QBCore"
    default_db: str = "oxmysql"
    default_prefix: str = "seoul_"
    default_model: str = "qwen2.5-coder:7b"
    heavy_model: str = "qwen3-coder:30b"
    safe_mode: bool = True
    auto_create_aiderignore: bool = True
    allow_non_git: bool = False
    show_advanced_menu: bool = False
    theme: str = "dark"


@dataclass
class Session:
    active_project_id: str = ""
    active_model: str = ""
    last_history_id: str = ""
    last_action_label: str = ""


@dataclass
class Project:
    id: str
    name: str
    repo_path: str
    framework: str
    database: str
    custom_prefix: str
    default_model: str
    heavy_model: str
    notes: str = ""
    reference_mode: str = "none"
    reference_repo_url: str = ""
    reference_local_path: str = ""


@dataclass
class EnvironmentStatus:
    python_version: str = ""
    git_found: bool = False
    ollama_found: bool = False
    aider_found: bool = False
    ollama_running: bool = False
    installed_models: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


@dataclass
class AiderResult:
    returncode: int = 0
    output: str = ""
    auto_replied_prompts: int = 0


@dataclass
class TaskIntent:
    raw_user_input: str = ""
    task_type: str = "unknown"
    objective: str = "entender a estrutura"
    confidence: float = 0.35
    reason: str = "Fallback estrutural."
    matched_keywords: list[str] = field(default_factory=list)
    suggested_scope: str = "resource"
    requires_framework_reference: bool = False


@dataclass
class ResourceInspection:
    name: str
    abs_path: str
    rel_path: str
    tree: str
    working_dir: str
    display_root: str
    manifest_path: str = ""
    manifest_text: str = ""
    key_files: list[str] = field(default_factory=list)
    context_files: list[str] = field(default_factory=list)
    structure_summary: str = ""
    structure_data: dict = field(default_factory=dict)
    scope_strategy: str = ""
    context_estimate: dict = field(default_factory=dict)
    context_status: str = ""
    was_limited: bool = False
    file_summaries: list[dict] = field(default_factory=list)
    file_summaries_text: str = ""
    warnings: list[str] = field(default_factory=list)
    objective: str = ""
    confirmed_facts: list[str] = field(default_factory=list)
    inferred_facts: list[str] = field(default_factory=list)
    not_confirmed: list[str] = field(default_factory=list)
    scope_validation: list[str] = field(default_factory=list)
    task_intent: dict = field(default_factory=dict)
