from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScopedContext:
    objective: str
    strategy: str
    selected_files: list[str] = field(default_factory=list)
    omitted_files: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    budget: int = 0


class FileScoper:
    DEFAULT_BUDGET = 8
    OBJECTIVE_BUDGETS = {
        "entender a estrutura": 8,
        "procurar problemas": 10,
        "planejar uma refatoração segura": 12,
        "planejar uma melhoria funcional": 10,
        "revisar NUI": 10,
        "comparar com framework": 10,
    }

    def select(self, inspection, objective: str = "") -> ScopedContext:
        data = inspection.structure_data or {}
        objective = (objective or "entender a estrutura").strip().lower()
        budget = self.OBJECTIVE_BUDGETS.get(objective, self.DEFAULT_BUDGET)

        entry_points = self._get_list(data, "entry_points")
        config_files = self._get_list(data, "config_files")
        shared_files = self._get_list(data, "shared_files")
        client_files = self._get_list(data, "client_files")
        server_files = self._get_list(data, "server_files")
        ui_files = self._get_list(data, "ui_files")
        data_files = self._get_list(data, "data_files")
        key_files = list(inspection.key_files or [])

        selected: list[str] = []
        notes: list[str] = []

        if objective == "entender a estrutura":
            strategy = "priorizar pontos de entrada, config e shared; reduzir arquivos repetitivos"
            buckets = [entry_points, config_files, shared_files, client_files[:2], server_files[:2], ui_files[:1]]
            notes.append("Objetivo estrutural: evitar leitura de pastas inteiras quando bastam pontos de entrada.")
        elif objective == "procurar problemas":
            strategy = "cobrir fluxo real entre config, shared, client e server"
            buckets = [entry_points, config_files, shared_files, client_files[:3], server_files[:3], ui_files[:1], data_files[:1]]
            notes.append("Objetivo de problemas: manter visão cruzada de client/server para achar quebras de fluxo.")
        elif objective == "planejar uma refatoração segura":
            strategy = "abrir o fluxo principal e ampliar cobertura sem puxar tudo"
            buckets = [entry_points, config_files, shared_files, client_files[:4], server_files[:4], ui_files[:2], data_files[:1]]
            notes.append("Refatoração segura: inclui mais arquivos de borda para reduzir risco de mexer sem contexto.")
        elif objective == "planejar uma melhoria funcional":
            strategy = "focar no fluxo principal e nos arquivos mais prováveis de mudança"
            buckets = [entry_points, config_files, shared_files, client_files[:3], server_files[:3], ui_files[:2]]
            notes.append("Melhoria funcional: foco nos pontos com maior chance de alteração direta.")
        elif objective == "revisar nui":
            strategy = "priorizar ui_page, html/css/js e o acoplamento com client"
            buckets = [ui_files, client_files[:3], shared_files[:1], config_files[:2], entry_points]
            notes.append("Revisão NUI: a UI sozinha não basta; o client precisa entrar para mostrar o acoplamento.")
        elif objective == "comparar com framework":
            strategy = "usar entrada, config e fluxo principal para comparar convenções"
            buckets = [entry_points, config_files, shared_files, client_files[:3], server_files[:3], ui_files[:1]]
            notes.append("Comparação com framework: foco em convenções e organização principal, não em todos os arquivos.")
        else:
            strategy = "priorizar arquivos centrais do escopo"
            buckets = [entry_points, config_files, shared_files, client_files[:2], server_files[:2], ui_files[:1], key_files[:2]]

        for bucket in buckets:
            for item in bucket:
                self._push(selected, item, budget)
                if len(selected) >= budget:
                    break
            if len(selected) >= budget:
                break

        if not selected:
            for item in key_files:
                self._push(selected, item, budget)
                if len(selected) >= budget:
                    break
            if selected:
                notes.append("Fallback aplicado: o analyzer não conseguiu distinguir bem a estrutura, então usou arquivos-chave.")

        if inspection.structure_data.get("scope_type") == "file" and inspection.key_files:
            selected = [inspection.key_files[0]]
            strategy = "arquivo único selecionado; escopo já está totalmente restrito"
            notes.append("Como o alvo já é um arquivo, não existe ganho em expandir contexto agora.")

        ordered_universe: list[str] = []
        for group in [entry_points, config_files, shared_files, client_files, server_files, ui_files, data_files, key_files]:
            for item in group:
                if item not in ordered_universe:
                    ordered_universe.append(item)

        omitted = [item for item in ordered_universe if item not in selected]
        if omitted:
            notes.append(f"{len(omitted)} arquivos ficaram fora do primeiro passe para proteger contexto.")

        return ScopedContext(
            objective=objective,
            strategy=strategy,
            selected_files=selected,
            omitted_files=omitted[:20],
            notes=notes,
            budget=budget,
        )

    def render(self, scoped: ScopedContext) -> str:
        blocks = [
            f"Objetivo: {scoped.objective}",
            f"Estratégia de escopo: {scoped.strategy}",
            f"Orçamento inicial de arquivos: {scoped.budget}",
        ]
        if scoped.selected_files:
            blocks.append("Arquivos selecionados para o primeiro passe:\n- " + "\n- ".join(scoped.selected_files))
        if scoped.omitted_files:
            blocks.append("Arquivos deixados para depois:\n- " + "\n- ".join(scoped.omitted_files[:10]))
        if scoped.notes:
            blocks.append("Notas do scoper:\n- " + "\n- ".join(scoped.notes))
        return "\n\n".join(blocks)

    def _get_list(self, data: dict, key: str) -> list[str]:
        value = data.get(key, [])
        if isinstance(value, list):
            return [str(item) for item in value if str(item).strip()]
        return []

    def _push(self, bucket: list[str], item: str, budget: int) -> None:
        item = str(item).strip()
        if not item or item in bucket or len(bucket) >= budget:
            return
        bucket.append(item)
