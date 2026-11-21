
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ContextReport:
    estimated_tokens: int
    max_tokens: int
    usage_percent: int
    status: str
    was_limited: bool = False
    selected_files_before: list[str] = field(default_factory=list)
    selected_files_after: list[str] = field(default_factory=list)
    removed_files: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class ContextMeter:
    DEFAULT_MAX_TOKENS = 6000
    SAFE_USAGE_PERCENT = 70
    WARNING_USAGE_PERCENT = 85

    FILE_TOKEN_BUDGETS = {
        "entender a estrutura": 6000,
        "procurar problemas": 7000,
        "planejar uma refatoração segura": 8500,
        "planejar uma melhoria funcional": 7500,
        "revisar NUI": 7000,
        "comparar com framework": 7500,
    }

    def estimate_tokens(self, text: str) -> int:
        text = text or ""
        return max(1, (len(text) + 3) // 4)

    def estimate_inspection(self, inspection, objective: str = "") -> ContextReport:
        max_tokens = self.FILE_TOKEN_BUDGETS.get((objective or "").strip().lower(), self.DEFAULT_MAX_TOKENS)
        snapshot = self._snapshot_text(inspection)
        estimated_tokens = self.estimate_tokens(snapshot)
        usage_percent = min(999, round((estimated_tokens / max_tokens) * 100)) if max_tokens else 0
        status = self._status_for(usage_percent)
        return ContextReport(
            estimated_tokens=estimated_tokens,
            max_tokens=max_tokens,
            usage_percent=usage_percent,
            status=status,
            selected_files_before=list(inspection.context_files or []),
            selected_files_after=list(inspection.context_files or []),
        )

    def limit(self, inspection, objective: str = "") -> ContextReport:
        report = self.estimate_inspection(inspection, objective=objective)
        current = list(inspection.context_files or [])
        if not current:
            report.notes.append("Nenhum arquivo contextual foi selecionado pelo scoper.")
            return report

        if report.usage_percent <= self.WARNING_USAGE_PERCENT:
            report.notes.append("Contexto dentro do orçamento inicial.")
            return report

        report.notes.append("Contexto alto detectado; redução automática aplicada.")
        original = list(current)
        while len(current) > 1:
            current.pop()
            temp = self._clone_with_files(inspection, current)
            test = self.estimate_inspection(temp, objective=objective)
            if test.usage_percent <= self.WARNING_USAGE_PERCENT:
                report = test
                report.was_limited = True
                report.selected_files_before = original
                report.selected_files_after = list(current)
                report.removed_files = [f for f in original if f not in current]
                report.notes.append("Arquivos menos prioritários foram removidos do primeiro passe.")
                inspection.context_files = list(current)
                return report

        final = self.estimate_inspection(self._clone_with_files(inspection, current[:1]), objective=objective)
        final.was_limited = True
        final.selected_files_before = original
        final.selected_files_after = current[:1]
        final.removed_files = [f for f in original if f not in current[:1]]
        final.notes.append("Fallback agressivo aplicado para proteger o contexto.")
        inspection.context_files = current[:1]
        return final

    def render(self, report: ContextReport) -> str:
        blocks = [
            "📊 Contexto estimado",
            f"- Tokens estimados: {report.estimated_tokens}",
            f"- Orçamento máximo: {report.max_tokens}",
            f"- Uso estimado: {report.usage_percent}%",
            f"- Status: {report.status}",
        ]
        if report.was_limited:
            blocks.append("- Limitação automática: sim")
        if report.selected_files_after:
            blocks.append("Arquivos finais no primeiro passe:\n- " + "\n- ".join(report.selected_files_after))
        if report.removed_files:
            blocks.append("Arquivos removidos para reduzir contexto:\n- " + "\n- ".join(report.removed_files))
        if report.notes:
            blocks.append("Notas do context meter:\n- " + "\n- ".join(report.notes))
        return "\n\n".join(blocks)

    def _clone_with_files(self, inspection, context_files: list[str]):
        from copy import deepcopy
        cloned = deepcopy(inspection)
        cloned.context_files = list(context_files)
        return cloned

    def _snapshot_text(self, inspection) -> str:
        parts = [
            inspection.name,
            inspection.rel_path,
            inspection.tree,
            inspection.manifest_text,
            inspection.structure_summary,
            inspection.scope_strategy,
            inspection.file_summaries_text,
            "\n".join(inspection.key_files or []),
            "\n".join(inspection.context_files or []),
            "\n".join(inspection.warnings or []),
        ]
        return "\n\n".join(p for p in parts if p)

    def _status_for(self, usage_percent: int) -> str:
        if usage_percent <= self.SAFE_USAGE_PERCENT:
            return "OK"
        if usage_percent <= self.WARNING_USAGE_PERCENT:
            return "ALTO"
        return "CRÍTICO"
