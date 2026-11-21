from __future__ import annotations
from dataclasses import asdict
from pathlib import Path
from typing import Any
import uuid
from core.config_manager import ConfigManager
from core.models import Project

class ProjectManager:
    def __init__(self, config: ConfigManager) -> None:
        self.config = config

    def list_projects(self) -> list[Project]:
        payload = self.config.load_projects_payload()
        return [Project(**item) for item in payload.get("projects", [])]

    def save_all(self, projects: list[Project]) -> None:
        self.config.save_projects_payload({"projects": [asdict(p) for p in projects]})

    def create_project(self, **kwargs: Any) -> Project:
        project = Project(id=str(uuid.uuid4()), **kwargs)
        projects = self.list_projects()
        projects.append(project)
        self.save_all(projects)
        return project

    def get_project(self, project_id: str) -> Project | None:
        for project in self.list_projects():
            if project.id == project_id:
                return project
        return None

    def update_project(self, updated: Project) -> None:
        projects = self.list_projects()
        for i, project in enumerate(projects):
            if project.id == updated.id:
                projects[i] = updated
                break
        self.save_all(projects)

    def remove_project(self, project_id: str) -> bool:
        projects = self.list_projects()
        new_projects = [p for p in projects if p.id != project_id]
        changed = len(new_projects) != len(projects)
        if changed:
            self.save_all(new_projects)
        return changed
