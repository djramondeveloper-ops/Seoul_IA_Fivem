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

def test_qbx_profile_available():
    from core.framework_manager import FrameworkManager
    profile = FrameworkManager()
    assert "QBX" in profile.names()
    assert "qbx_core" in profile.get("QBX")["official_repo"]


def test_framework_auto_selection_qbx(tmp_path, monkeypatch):
    from menus.main_menu import MainMenu
    resource = tmp_path / "resources" / "qbx_core"
    resource.mkdir(parents=True)
    (resource / "fxmanifest.lua").write_text("fx_version 'cerulean'", encoding="utf-8")
    monkeypatch.setattr("menus.main_menu.ask_choice", lambda title, options: 0)
    monkeypatch.setattr("menus.main_menu.ask_bool", lambda title, default: True)
    menu = MainMenu()
    assert menu._choose_framework_name("QBCore", str(tmp_path)) == "QBX"
