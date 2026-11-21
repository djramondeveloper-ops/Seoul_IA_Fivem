from core.task_router import TaskRouter
from core.resource_manager import ResourceManager


def test_router_returns_task_intent():
    objective, intent = TaskRouter().objective_for("quero revisar a nui e achar o erro")
    assert objective
    assert intent.task_type in {"bug", "nui", "compare", "structure", "refactor", "improve", "unknown"}
    assert 0 <= intent.confidence <= 1


def test_resource_manager_constructs():
    manager = ResourceManager()
    assert manager is not None
