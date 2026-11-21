from __future__ import annotations
from pathlib import Path
from core.config_manager import ConfigManager
from core.env_manager import EnvironmentManager
from core.framework_manager import FrameworkManager
from core.auto_framework_detector import detect_frameworks
from core.git_manager import GitManager
from core.history_manager import HistoryManager
from core.io_utils import ask, ask_bool, ask_choice, ask_multiline, pause, print_block, render_header
from core.models import Project, Session, Settings
from core.ollama_manager import OllamaManager
from core.project_manager import ProjectManager
from core.prompt_builder import (
    build_advanced_prompt,
    build_create_resource_prompt,
    build_custom_resources_prompt,
    build_debug_prompt,
    build_followup_prompt,
    build_framework_compare_prompt,
    build_resource_review_prompt,
)
from core.aider_manager import AiderManager
from core.resource_manager import ResourceManager
from core.resource_scaffolder import ResourceScaffolder
from core.task_router import TaskRouter


class MainMenu:
    def __init__(self) -> None:
        self.config = ConfigManager()
        self.projects = ProjectManager(self.config)
        self.frameworks = FrameworkManager()
        self.env = EnvironmentManager()
        self.ollama = OllamaManager()
        self.git = GitManager()
        self.aider = AiderManager()
        self.resources = ResourceManager()
        self.router = TaskRouter()
        self.history = HistoryManager()

    def loop(self) -> None:
        while True:
            self._render_screen("Menu principal")
            settings = self.config.load_settings()
            options = [
                "Primeira configuração / verificar ambiente",
                "Cadastrar projeto",
                "Selecionar projeto ativo",
                "Excluir cadastro de projeto",
                "Ver projeto ativo",
                "Analisar meus scripts customizados",
                "Revisar um resource / pasta / arquivo",
                "Corrigir erro / debug guiado",
                "Criar resource novo",
                "Comparar resource com referência do framework",
                "Trocar modelo ativo",
                "Baixar / atualizar modelos recomendados",
                "Configurar referência do framework no projeto ativo",
                "Histórico recente / continuar última tarefa",
                "Identificar framework automaticamente",
            ]
            if settings.show_advanced_menu:
                options.append("Modo avançado (prompt livre)")
            options.append("Sair")
            choice = ask_choice("Menu principal", options)
            if choice == 0:
                self.setup_and_doctor()
            elif choice == 1:
                self.add_project()
            elif choice == 2:
                self.select_project()
            elif choice == 3:
                self.delete_project()
            elif choice == 4:
                self.show_active_project()
            elif choice == 5:
                self.run_custom_analysis()
            elif choice == 6:
                self.review_scope()
            elif choice == 7:
                self.debug_error()
            elif choice == 8:
                self.create_resource()
            elif choice == 9:
                self.compare_with_framework()
            elif choice == 10:
                self.switch_model()
            elif choice == 11:
                self.download_models()
            elif choice == 12:
                self.configure_project_reference()
            elif choice == 13:
                self.history_menu()
            elif choice == 14:
                self.detect_project_framework()
            else:
                if settings.show_advanced_menu and choice == 15:
                    self.advanced_mode()
                else:
                    print("Até mais.")
                    return

    def detect_project_framework(self) -> None:
        import json
        _, project = self._session_project()
        if not project:
            print("Selecione um projeto ativo primeiro.")
            pause()
            return
        try:
            result = detect_frameworks(project.repo_path)
            print_block("Detecção automática de framework", json.dumps(result, ensure_ascii=False, indent=2))
        except (OSError, ValueError) as exc:
            print(f"Falha na detecção: {exc}")
        pause()

    def _session_project(self) -> tuple[Session, Project | None]:
        session = self.config.load_session()
        project = self.projects.get_project(session.active_project_id) if session.active_project_id else None
        return session, project

    def _render_screen(self, title: str, subtitle: str = "") -> None:
        session, project = self._session_project()
        git_status = "-"
        framework = project.framework if project else "-"
        if project:
            dirty = self.git.status_short(project.repo_path)
            git_status = "alterado" if dirty else "limpo"
        rows = [
            ("Projeto ativo", project.name if project else "nenhum"),
            ("Framework", framework),
            ("Modelo ativo", session.active_model or "nenhum"),
            ("Git", git_status),
        ]
        if session.last_action_label:
            rows.append(("Última tarefa", session.last_action_label))
        render_header(title=title, rows=rows, subtitle=subtitle or title)

    def _choose_framework_name(self, default_name: str, project_path: str = "") -> str:
        names = self.frameworks.names()
        if default_name not in names:
            names = [default_name] + names
        if project_path:
            try:
                result = detect_frameworks(project_path)
                detected = {"qbox": "QBX", "qbcore": "QBCore", "esx": "ESX", "vrp": "vRP"}.get(result["primary_framework"])
                if detected in names:
                    print(f"Framework detectado automaticamente: {detected}")
                    if result["hybrid_or_bridge_possible"]:
                        print("Aviso: foram encontrados sinais de bridge ou multiplos frameworks.")
                    if ask_bool("Usar o framework detectado", True):
                        return detected
                else:
                    print("Nao foi possivel identificar o framework com confianca.")
            except (OSError, ValueError) as exc:
                print(f"Falha na deteccao: {exc}")
            print("Escolha manualmente caso a deteccao nao corresponda a sua base.")
        idx = ask_choice("Escolha o framework", names)
        return names[idx]

    def setup_and_doctor(self) -> None:
        self._render_screen("Configuração inicial")
        settings = self.config.load_settings()
        settings.ollama_api_base = ask("URL do Ollama", settings.ollama_api_base)
        settings.aider_command = ask("Comando do Aider", settings.aider_command)
        print("O framework da base será identificado automaticamente ao cadastrar um projeto.")
        if ask_bool("Definir framework padrão manualmente agora", False):
            settings.default_framework = self._choose_framework_name(settings.default_framework)
        settings.default_db = ask("Banco padrão", settings.default_db)
        settings.default_prefix = ask("Prefixo custom padrão", settings.default_prefix)
        settings.default_model = ask("Modelo rápido padrão", settings.default_model)
        settings.heavy_model = ask("Modelo forte padrão", settings.heavy_model)
        settings.safe_mode = ask_bool("Ativar modo seguro por padrão", settings.safe_mode)
        settings.auto_create_aiderignore = ask_bool("Criar .aiderignore automaticamente", settings.auto_create_aiderignore)
        settings.allow_non_git = ask_bool("Permitir projeto sem Git", settings.allow_non_git)
        settings.show_advanced_menu = ask_bool("Mostrar menu avançado", settings.show_advanced_menu)
        self.config.save_settings(settings)

        status = self.env.check(settings)
        self._render_screen("Verificação de ambiente")
        print_block("Ambiente", self._format_env_status(status))
        if status.issues:
            print_block("Como corrigir", self._install_help())
        pause()

    def _format_env_status(self, status) -> str:
        models = ", ".join(status.installed_models) if status.installed_models else "nenhum"
        lines = [
            f"Python: {status.python_version}",
            f"Git: {'OK' if status.git_found else 'FALTANDO'}",
            f"Ollama: {'OK' if status.ollama_found else 'FALTANDO'}",
            f"Ollama rodando: {'SIM' if status.ollama_running else 'NÃO'}",
            f"Aider: {'OK' if status.aider_found else 'FALTANDO'}",
            f"Modelos instalados: {models}",
        ]
        if status.issues:
            lines.append("Problemas:")
            lines.extend(f"- {item}" for item in status.issues)
        return "\n".join(lines)

    def _install_help(self) -> str:
        from core.paths import INTERNAL_DIR
        return (INTERNAL_DIR / "install_help.md").read_text(encoding="utf-8")

    def add_project(self) -> None:
        self._render_screen("Cadastrar projeto")
        settings = self.config.load_settings()
        name = ask("Nome do projeto")
        repo_path = ask("Caminho do repo").strip().strip('"').strip()
        if not Path(repo_path).exists():
            print("Esse caminho não existe.")
            pause()
            return

        framework = self._choose_framework_name(settings.default_framework, repo_path)
        database = ask("Banco", settings.default_db)
        custom_prefix = ask("Prefixo custom", settings.default_prefix)

        models = self.ollama.list_models()
        default_model = ask("Modelo rápido", settings.default_model if settings.default_model in models or not models else models[0])
        heavy_model = ask("Modelo forte", settings.heavy_model if settings.heavy_model in models or not models else default_model)
        notes = ask("Observações", f"Scripts com prefixo {custom_prefix} são custom do usuário.")

        if not self.git.is_git_repo(repo_path):
            if settings.allow_non_git:
                print("Aviso: o projeto não é um repositório Git. O modo seguro fica limitado.")
            else:
                if ask_bool("Projeto sem Git. Deseja inicializar um repositório agora", True):
                    code = self.git.init_repo(repo_path)
                    if code != 0:
                        print("Não foi possível inicializar o Git.")
                        pause()
                        return
                else:
                    print("Cadastro cancelado. Para evitar bagunça, o modo seguro exige Git.")
                    pause()
                    return

        reference_mode, reference_repo_url, reference_local_path = self._reference_setup_for_framework(framework, quick=True)
        project = self.projects.create_project(
            name=name,
            repo_path=str(Path(repo_path)),
            framework=framework,
            database=database,
            custom_prefix=custom_prefix,
            default_model=default_model,
            heavy_model=heavy_model,
            notes=notes,
            reference_mode=reference_mode,
            reference_repo_url=reference_repo_url,
            reference_local_path=reference_local_path,
        )
        session = self.config.load_session()
        session.active_project_id = project.id
        session.active_model = project.default_model
        self.config.save_session(session)
        print(f"Projeto '{project.name}' cadastrado e ativado.")
        pause()

    def delete_project(self) -> None:
        self._render_screen("Excluir cadastro de projeto")
        projects = self.projects.list_projects()
        if not projects:
            print("Nenhum projeto cadastrado.")
            pause()
            return
        idx = ask_choice("Selecione o cadastro a excluir (arquivos da base serão preservados)", [f"{p.name} ({p.repo_path})" for p in projects] + ["Cancelar"])
        if idx == len(projects):
            return
        project = projects[idx]
        print(f"Cadastro: {project.name} | Pasta preservada: {project.repo_path}")
        if not ask_bool("Confirmar exclusão SOMENTE do cadastro", False):
            print("Operação cancelada.")
            pause()
            return
        if self.projects.remove_project(project.id):
            session = self.config.load_session()
            if session.active_project_id == project.id:
                session.active_project_id = ""
                session.active_model = ""
                self.config.save_session(session)
            print("Cadastro removido. Os arquivos da base FiveM não foram apagados.")
        pause()

    def _reference_setup_for_framework(self, framework: str, quick: bool = False) -> tuple[str, str, str]:
        profile = self.frameworks.get(framework)
        options = [
            "Sem referência externa",
            "Usar repositório oficial como referência de padrão",
            "Usar meu fork como referência",
            "Usar referência personalizada",
        ]
        title = "Base de referência do framework"
        if quick:
            title += " (opcional)"
        idx = ask_choice(title, options)
        if idx == 0:
            return "none", "", ""
        if idx == 1:
            return "official", profile.get("official_repo", ""), profile.get("official_local_hint", "")
        if idx == 2:
            url = ask("URL do seu fork", profile.get("official_repo", ""))
            local_path = ask("Caminho local do fork (opcional)", "")
            return "fork", url, local_path
        url = ask("URL da referência personalizada", "")
        local_path = ask("Caminho local da referência (opcional)", "")
        return "custom", url, local_path

    def select_project(self) -> None:
        self._render_screen("Selecionar projeto ativo")
        projects = self.projects.list_projects()
        if not projects:
            print("Nenhum projeto cadastrado.")
            pause()
            return
        idx = ask_choice("Escolha o projeto ativo", [f"{p.name} ({p.repo_path})" for p in projects])
        session = self.config.load_session()
        session.active_project_id = projects[idx].id
        session.active_model = projects[idx].default_model
        self.config.save_session(session)
        print(f"Projeto ativo definido para: {projects[idx].name}")
        pause()

    def _require_project(self) -> tuple[Project | None, Session | None, Settings | None]:
        session = self.config.load_session()
        settings = self.config.load_settings()
        if not session.active_project_id:
            self._render_screen("Projeto não selecionado")
            print("Nenhum projeto ativo.")
            pause()
            return None, None, None
        project = self.projects.get_project(session.active_project_id)
        if not project:
            self._render_screen("Projeto não encontrado")
            print("Projeto ativo não encontrado.")
            pause()
            return None, None, None
        if not session.active_model:
            session.active_model = project.default_model
            self.config.save_session(session)
        return project, session, settings

    def show_active_project(self) -> None:
        project, session, _ = self._require_project()
        if not project:
            return
        self._render_screen("Projeto ativo")
        print_block(
            "Detalhes",
            f"Nome: {project.name}\n"
            f"Repo: {project.repo_path}\n"
            f"Framework: {project.framework}\n"
            f"Banco: {project.database}\n"
            f"Prefixo: {project.custom_prefix}\n"
            f"Modelo rápido: {project.default_model}\n"
            f"Modelo forte: {project.heavy_model}\n"
            f"Modelo ativo: {session.active_model}\n"
            f"Referência: {project.reference_mode or 'none'}\n"
            f"Notas: {project.notes or '-'}"
        )
        print_block("Git status (resumo)", self.git.status_short(project.repo_path) or "Repo limpo.")
        pause()

    def _preflight(self, project: Project, settings: Settings) -> bool:
        if not self.git.is_git_repo(project.repo_path) and not settings.allow_non_git:
            print("Projeto sem Git. O modo seguro bloqueou a execução.")
            return False
        if settings.safe_mode and self.git.has_problematic_deletions(project.repo_path):
            print_block(
                "Atenção",
                "O Git detectou alterações que podem confundir a IA (arquivos deletados, movidos ou não rastreados).\n"
                "Revise o status do repositório antes de continuar. O projeto atual sempre deve mandar mais que a referência de framework.",
            )
            if not ask_bool("Deseja continuar mesmo assim", False):
                return False
        return True

    def _launch_prompt(
        self,
        project: Project,
        session: Session,
        settings: Settings,
        prompt: str,
        action_label: str,
        target: str = "",
        working_dir: str | None = None,
        subtree_only: bool = False,
    ) -> None:
        self._render_screen("Executando tarefa", subtitle=action_label)
        if not self._preflight(project, settings):
            pause()
            return
        extra_ignore = self.frameworks.recommended_aiderignore(project.framework)
        print("Abrindo Aider...\n")
        result = self.aider.launch(
            project.repo_path,
            session.active_model,
            prompt,
            settings,
            working_dir=working_dir,
            subtree_only=subtree_only,
            read_files=getattr(self, '_pending_read_files', None),
            framework_ignore=extra_ignore,
        )
        self._pending_read_files = None
        history_id = self.history.append({
            "project_id": project.id,
            "project_name": project.name,
            "model": session.active_model,
            "action": action_label,
            "target": target,
            "prompt": prompt,
            "output": result.output[-12000:],
            "returncode": result.returncode,
            "auto_replied_prompts": result.auto_replied_prompts,
        })
        session.last_history_id = history_id
        session.last_action_label = action_label + (f" | {target}" if target else "")
        self.config.save_session(session)
        print(f"\nAider finalizado com código {result.returncode}.")
        if result.auto_replied_prompts:
            print(f"Perguntas de anexar arquivo respondidas automaticamente: {result.auto_replied_prompts}")
        pause()

    def run_custom_analysis(self) -> None:
        project, session, settings = self._require_project()
        if not project:
            return
        resources = self.resources.list_custom_resources(project.repo_path, project.custom_prefix)
        names = [f"{name} -> {path.relative_to(Path(project.repo_path)).as_posix()}" for name, path in resources]
        prompt = build_custom_resources_prompt(project, names)
        self._launch_prompt(project, session, settings, prompt, "Analisar scripts customizados", target=project.custom_prefix)

    def _pick_scope(self, project: Project, objective: str = "entender a estrutura", user_goal: str = "") -> tuple[str | None, object | None, str | None]:
        resource_name = ask("Nome do resource")
        if not resource_name:
            return None, None, None
        resource_path = self.resources.find_resource(project.repo_path, resource_name)
        if not resource_path:
            suggestions = self.resources.suggest_resources(project.repo_path, resource_name)
            msg = [f"Resource '{resource_name}' não encontrado."]
            if suggestions:
                msg.append("Sugestões:")
                msg.extend(f"- {item}" for item in suggestions)
            print_block("Resource não encontrado", "\n".join(msg))
            pause()
            return None, None, None
        scope_idx = ask_choice("Escopo", ["Resource inteiro", "Uma pasta do resource", "Um arquivo específico"])
        subpath = ""
        if scope_idx == 1:
            subpath = ask("Pasta relativa dentro do resource", "")
        elif scope_idx == 2:
            subpath = ask("Arquivo relativo dentro do resource", "")
        inspection = self.resources.inspect_resource(
            project.repo_path,
            resource_name,
            subpath,
            objective=objective,
            user_input=(user_goal or objective),
            lock_objective=True,
        )
        if not inspection:
            print("Não foi possível inspecionar o escopo informado.")
            pause()
            return None, None, None
        if scope_idx in {0, 1}:
            working_dir = str(Path(project.repo_path) / inspection.rel_path)
        else:
            working_dir = str(resource_path)
        return resource_name, inspection, working_dir

    def _ask_review_objective(self) -> tuple[str, str]:
        mode = ask_choice("Como definir o objetivo", ["Escolher manualmente", "Detectar automaticamente pelo seu pedido"])
        if mode == 0:
            objectives = [
                "entender a estrutura",
                "procurar problemas",
                "planejar uma refatoração segura",
                "planejar uma melhoria funcional",
                "revisar NUI",
            ]
            objective = objectives[ask_choice("Objetivo", objectives)]
            user_goal = ask_multiline("Explique em uma frase o que você quer analisar neste escopo (opcional)")
            return objective, user_goal

        user_goal = ask_multiline("Descreva em uma frase o que você quer que a IA faça neste escopo")
        objective, routed = self.router.objective_for(user_goal)
        print_block(
            "Roteamento automático",
            f"Tipo detectado: {routed.task_type}\n"
            f"Confiança: {routed.confidence}\n"
            f"Escopo sugerido: {routed.suggested_scope}\n"
            f"Motivo: {routed.reason}\n"
            f"Objetivo aplicado: {objective}",
        )
        return objective, user_goal

    def review_scope(self) -> None:
        project, session, settings = self._require_project()
        if not project:
            return
        self._render_screen("Revisar resource / pasta / arquivo")
        objective, user_goal = self._ask_review_objective()
        resource_name, inspection, working_dir = self._pick_scope(project, objective=objective, user_goal=user_goal)
        if not inspection:
            return
        extra = ask_multiline("Instruções extras (opcional)")
        use_heavy = ask_bool("Usar o modelo forte para esta análise", objective in {"entender a estrutura", "planejar uma refatoração segura"})
        if use_heavy:
            session.active_model = project.heavy_model
            self.config.save_session(session)
        prompt = build_resource_review_prompt(project, inspection, objective, extra)
        self._pending_read_files = inspection.context_files
        self._launch_prompt(project, session, settings, prompt, "Revisar escopo", target=inspection.rel_path, working_dir=working_dir, subtree_only=True)

    def debug_error(self) -> None:
        project, session, settings = self._require_project()
        if not project:
            return
        self._render_screen("Debug guiado")
        error_text = ask_multiline("Cole um resumo do erro")
        if not error_text:
            print("Nenhum erro informado.")
            pause()
            return

        inspection = None
        working_dir = None
        if ask_bool("Vincular este debug a um resource/pasta/arquivo do projeto", True):
            _, inspection, working_dir = self._pick_scope(project, objective="procurar problemas", user_goal=error_text)
            if inspection:
                self._pending_read_files = inspection.context_files

        extra = ask_multiline("Instruções extras (opcional)")
        prompt = build_debug_prompt(project, error_text, inspection=inspection, extra_instructions=extra)
        target = inspection.rel_path if inspection else None
        self._launch_prompt(project, session, settings, prompt, "Debug guiado", target=target, working_dir=working_dir, subtree_only=bool(inspection))

    def create_resource(self) -> None:
        project, session, settings = self._require_project()
        if not project:
            return
        self._render_screen("Criar resource novo")
        resource_name = ask("Nome do resource")
        if not resource_name:
            print("Nome do resource não informado.")
            pause()
            return

        flavors = ["básico", "com banco", "com NUI", "com banco + NUI", "admin/staff", "phone app"]
        idx = ask_choice("Tipo do resource", flavors)
        flavor = flavors[idx]
        extra = ask_multiline("Instruções extras (opcional)")

        scaffolder = ResourceScaffolder()
        try:
            result = scaffolder.scaffold(project, resource_name, flavor)
        except FileExistsError as exc:
            print(str(exc))
            pause()
            return
        except ValueError as exc:
            print(str(exc))
            pause()
            return

        body = [
            f"Pasta base: {result.target_root}",
            f"Resource criado em: {result.resource_path}",
            "",
            "Arquivos criados:",
        ]
        body.extend(f"- {item}" for item in result.created_files)
        if result.warnings:
            body.append("")
            body.append("Observações:")
            body.extend(f"- {item}" for item in result.warnings)
        print_block("Estrutura criada", "\n".join(body))

        if not ask_bool("Abrir IA agora para completar o resource", True):
            pause()
            return

        resource_root = Path(result.resource_path)
        self._pending_read_files = []
        for rel_path in result.created_files:
            try:
                scoped_rel = Path(rel_path).relative_to(result.resource_name).as_posix()
            except Exception:
                abs_path = (Path(result.target_root) / rel_path).resolve()
                scoped_rel = abs_path.relative_to(resource_root).as_posix()
            self._pending_read_files.append(scoped_rel)
        session.active_model = project.heavy_model
        self.config.save_session(session)
        prompt = build_create_resource_prompt(project, result.resource_name, flavor, extra)
        self._launch_prompt(
            project,
            session,
            settings,
            prompt,
            "Criar resource",
            target=result.resource_name,
            working_dir=result.resource_path,
            subtree_only=True,
        )

    def compare_with_framework(self) -> None:
        project, session, settings = self._require_project()
        if not project:
            return
        self._render_screen("Comparar com referência do framework")
        if project.reference_mode == "none":
            print("Esse projeto está sem referência de framework configurada.")
            if not ask_bool("Deseja configurar agora", True):
                return
            self.configure_project_reference()
            project, session, settings = self._require_project()
            if not project:
                return
        resource_name, inspection, working_dir = self._pick_scope(project, objective="comparar com framework")
        if not inspection:
            return
        extra = ask_multiline("Instruções extras (opcional)")
        prompt = build_framework_compare_prompt(project, inspection, extra)
        self._pending_read_files = inspection.context_files
        self._launch_prompt(project, session, settings, prompt, "Comparar com framework", target=inspection.rel_path, working_dir=working_dir, subtree_only=True)

    def switch_model(self) -> None:
        project, session, _ = self._require_project()
        if not project:
            return
        self._render_screen("Trocar modelo ativo")
        options = [
            f"Rápido ({project.default_model})",
            f"Forte ({project.heavy_model})",
            "Escolher manualmente",
        ]
        idx = ask_choice("Modelo ativo", options)
        if idx == 0:
            session.active_model = project.default_model
        elif idx == 1:
            session.active_model = project.heavy_model
        else:
            models = self.ollama.list_models()
            if not models:
                print("Nenhum modelo encontrado no Ollama.")
                pause()
                return
            midx = ask_choice("Escolha manualmente", models)
            session.active_model = models[midx]
        self.config.save_session(session)
        print(f"Modelo ativo definido para: {session.active_model}")
        pause()

    def download_models(self) -> None:
        self._render_screen("Baixar / atualizar modelos")
        settings = self.config.load_settings()
        options = [
            f"Baixar só o modelo rápido ({settings.default_model})",
            f"Baixar rápido + forte ({settings.default_model} + {settings.heavy_model})",
            "Baixar um modelo manualmente",
        ]
        idx = ask_choice("Modelos recomendados", options)
        if idx == 0:
            self.ollama.pull_model(settings.default_model)
        elif idx == 1:
            self.ollama.pull_model(settings.default_model)
            self.ollama.pull_model(settings.heavy_model)
        else:
            model = ask("Nome do modelo")
            if model:
                self.ollama.pull_model(model)
        pause()

    def configure_project_reference(self) -> None:
        project, _, _ = self._require_project()
        if not project:
            return
        self._render_screen("Configurar referência do framework")
        mode, url, local = self._reference_setup_for_framework(project.framework)
        project.reference_mode = mode
        project.reference_repo_url = url
        project.reference_local_path = local
        self.projects.update_project(project)
        print("Referência do framework atualizada.")
        pause()

    def history_menu(self) -> None:
        project, session, settings = self._require_project()
        if not project:
            return
        self._render_screen("Histórico recente")
        recent = self.history.list_recent(project.id, limit=12)
        if not recent:
            print("Nenhum histórico para este projeto ainda.")
            pause()
            return
        options = [f"{item.get('action')} | {item.get('target') or '-'} | {item.get('model')}" for item in recent]
        idx = ask_choice("Histórico recente", options)
        entry = recent[idx]
        self._render_screen("Detalhe do histórico", subtitle=entry.get("action", "Histórico"))
        print_block(
            "Última saída",
            f"Ação: {entry.get('action')}\nAlvo: {entry.get('target')}\nModelo: {entry.get('model')}\n\n"
            + (entry.get('output') or '')[-3000:],
        )
        if ask_bool("Deseja continuar essa tarefa", True):
            followup = ask_multiline("Nova instrução para continuar")
            if followup:
                prompt = build_followup_prompt(project, entry.get("prompt", ""), entry.get("output", ""), followup)
                self._launch_prompt(project, session, settings, prompt, "Continuar tarefa", target=entry.get("target", ""))
            else:
                print("Nenhuma instrução informada.")
                pause()
        else:
            pause()

    def advanced_mode(self) -> None:
        project, session, settings = self._require_project()
        if not project:
            return
        self._render_screen("Modo avançado")
        prompt = ask_multiline("Mensagem inicial para o Aider")
        if not prompt:
            print("Nenhuma mensagem informada.")
            pause()
            return
        self._launch_prompt(project, session, settings, build_advanced_prompt(project, prompt), "Modo avançado")
