from __future__ import annotations

from core.models import TaskIntent


class TaskRouter:
    KEYWORDS: dict[str, list[str]] = {
        "bug": [
            "erro", "bug", "nao funciona", "não funciona", "quebrado", "falha", "crash",
            "traceback", "exception", "nil value", "attempt to index", "stack", "problem",
            "problema", "corrigir", "debug", "arrumar", "consertar", "fix",
        ],
        "structure": [
            "estrutura", "entender", "organização", "organizacao", "arquitetura", "mapear",
            "como funciona", "visão geral", "visao geral", "analisar resource",
        ],
        "refactor": [
            "refator", "refactor", "reorganizar", "modularizar", "separar", "limpar",
            "melhorar estrutura", "reduzir acoplamento",
        ],
        "improve": [
            "melhorar", "adicionar", "implementar", "criar", "nova feature", "novo sistema",
            "otimizar", "expandir", "evoluir",
        ],
        "nui": [
            "nui", "ui", "interface", "html", "css", "js", "frontend", "layout",
            "menu", "visual", "design", "webview",
        ],
        "compare": [
            "comparar", "comparação", "comparacao", "diferença", "diferenca", "framework",
            "referência", "referencia", "qbcore", "fork",
        ],
    }

    OBJECTIVE_MAP: dict[str, str] = {
        "bug": "procurar problemas",
        "structure": "entender a estrutura",
        "refactor": "planejar uma refatoração segura",
        "improve": "planejar uma melhoria funcional",
        "nui": "revisar NUI",
        "compare": "comparar com framework",
        "unknown": "entender a estrutura",
    }

    SCOPE_MAP: dict[str, str] = {
        "bug": "resource",
        "structure": "resource",
        "refactor": "resource",
        "improve": "resource",
        "nui": "folder",
        "compare": "resource",
        "unknown": "resource",
    }

    def route(self, text: str) -> TaskIntent:
        normalized = self._normalize(text)
        scores: dict[str, list[str]] = {}

        for task_type, keywords in self.KEYWORDS.items():
            matched = [kw for kw in keywords if kw in normalized]
            if matched:
                scores[task_type] = matched

        if not scores:
            return TaskIntent(
                raw_user_input=text or "",
                task_type="unknown",
                objective=self.OBJECTIVE_MAP["unknown"],
                confidence=0.35,
                reason="Nenhuma palavra-chave forte detectada. Fallback seguro para análise estrutural.",
                matched_keywords=[],
                suggested_scope=self.SCOPE_MAP["unknown"],
                requires_framework_reference=False,
            )

        ordered = sorted(
            scores.items(),
            key=lambda item: (len(item[1]), self._task_priority(item[0])),
            reverse=True,
        )
        task_type, matched = ordered[0]
        confidence = min(0.95, 0.45 + (0.10 * len(matched)))
        if len(ordered) > 1 and len(ordered[1][1]) == len(matched):
            confidence = max(0.4, confidence - 0.12)
            reason = (
                f"Tarefa mista detectada. Predomínio de '{task_type}', mas também houve sinais de "
                f"'{ordered[1][0]}'. Palavras-chave: {', '.join(matched[:6])}"
            )
        else:
            reason = f"Detectado padrão de tarefa '{task_type}' por palavras-chave: {', '.join(matched[:6])}"

        return TaskIntent(
            raw_user_input=text or "",
            task_type=task_type,
            objective=self.OBJECTIVE_MAP.get(task_type, self.OBJECTIVE_MAP["unknown"]),
            confidence=round(confidence, 2),
            reason=reason,
            matched_keywords=matched,
            suggested_scope=self.SCOPE_MAP.get(task_type, "resource"),
            requires_framework_reference=(task_type == "compare"),
        )

    def objective_for(self, text: str) -> tuple[str, TaskIntent]:
        routed = self.route(text)
        return routed.objective, routed

    def _normalize(self, text: str) -> str:
        return " ".join((text or "").strip().lower().split())

    def _task_priority(self, task_type: str) -> int:
        order = ["bug", "nui", "compare", "refactor", "improve", "structure", "unknown"]
        try:
            return len(order) - order.index(task_type)
        except ValueError:
            return 0
