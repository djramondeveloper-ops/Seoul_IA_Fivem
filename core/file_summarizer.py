from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FileSummary:
    path: str
    role: str = ""
    probable_features: list[str] = field(default_factory=list)
    detected_events: list[str] = field(default_factory=list)
    detected_exports: list[str] = field(default_factory=list)
    detected_dependencies: list[str] = field(default_factory=list)
    key_symbols: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    truncated: bool = False


class FileSummarizer:
    MAX_READ_CHARS = 12000

    EVENT_PATTERNS = [
        r'''RegisterNetEvent\(["\']([^"\']+)''',
        r'''TriggerServerEvent\(["\']([^"\']+)''',
        r'''TriggerClientEvent\(["\']([^"\']+)''',
        r'''RegisterNUICallback\(["\']([^"\']+)''',
        r'''onNet\(["\']([^"\']+)''',
        r'''emitNet\(["\']([^"\']+)''',
        r'''SendNUIMessage\(''',
    ]
    EXPORT_PATTERNS = [
        r'''exports\(["\']([^"\']+)''',
        r'''exports\.([A-Za-z0-9_]+)''',
    ]
    DEPENDENCY_PATTERNS = [
        r'''exports\[?["\']([^"\']+)["\']\]?''',
        r'''@([A-Za-z0-9_\-]+)/''',
        r'''require\(["\']([^"\']+)''',
    ]
    SYMBOL_PATTERNS = [
        r'''\bfunction\s+([A-Za-z0-9_]+)''',
        r'''\blocal\s+function\s+([A-Za-z0-9_]+)''',
        r'''\bconst\s+([A-Za-z0-9_]+)\s*=''',
        r'''\blet\s+([A-Za-z0-9_]+)\s*=''',
        r'''\bvar\s+([A-Za-z0-9_]+)\s*=''',
    ]

    def summarize_many(self, base_dir: str | Path, files: list[str]) -> list[FileSummary]:
        base_dir = Path(base_dir)
        summaries: list[FileSummary] = []
        for rel in files or []:
            summary = self.summarize_file(base_dir, rel)
            if summary:
                summaries.append(summary)
        return summaries

    def summarize_file(self, base_dir: str | Path, rel_path: str) -> FileSummary | None:
        base_dir = Path(base_dir)
        path = base_dir / rel_path
        if not path.exists() or not path.is_file():
            return None
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return FileSummary(path=rel_path, notes=["Não foi possível ler o arquivo."])

        truncated = len(raw) > self.MAX_READ_CHARS
        text = raw[: self.MAX_READ_CHARS]
        lower = text.lower()
        suffix = path.suffix.lower()

        role = self._detect_role(rel_path, lower, suffix)
        features = self._detect_features(rel_path, lower, suffix)
        events = self._collect(self.EVENT_PATTERNS, text, max_items=8)
        exports = self._collect(self.EXPORT_PATTERNS, text, max_items=6)
        deps = self._collect(self.DEPENDENCY_PATTERNS, text, max_items=8)
        symbols = self._collect(self.SYMBOL_PATTERNS, text, max_items=8)
        notes = self._build_notes(rel_path, lower, suffix)
        if truncated:
            notes.append("Resumo parcial: arquivo grande, leitura limitada no primeiro passe.")

        return FileSummary(
            path=rel_path,
            role=role,
            probable_features=features,
            detected_events=events,
            detected_exports=exports,
            detected_dependencies=deps,
            key_symbols=symbols,
            notes=notes,
            truncated=truncated,
        )

    def render_many(self, summaries: list[FileSummary]) -> str:
        if not summaries:
            return "Nenhum resumo por arquivo foi gerado."
        blocks: list[str] = []
        for item in summaries:
            lines = [f"- {item.path}"]
            if item.role:
                lines.append(f"  função provável: {item.role}")
            if item.probable_features:
                lines.append("  indícios de função: " + ", ".join(item.probable_features[:5]))
            if item.detected_events:
                lines.append("  eventos/callbacks: " + ", ".join(item.detected_events[:5]))
            if item.detected_exports:
                lines.append("  exports: " + ", ".join(item.detected_exports[:4]))
            if item.detected_dependencies:
                lines.append("  dependências citadas: " + ", ".join(item.detected_dependencies[:5]))
            if item.key_symbols:
                lines.append("  símbolos-chave: " + ", ".join(item.key_symbols[:5]))
            if item.notes:
                lines.append("  notas: " + " | ".join(item.notes[:3]))
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks)

    def _collect(self, patterns: list[str], text: str, max_items: int = 8) -> list[str]:
        found: list[str] = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                if match.groups():
                    value = next((g for g in match.groups() if g), match.group(0))
                else:
                    value = match.group(0)
                value = str(value).strip()
                if value == "SendNUIMessage(":
                    value = "SendNUIMessage"
                if not value or value in found:
                    continue
                found.append(value)
                if len(found) >= max_items:
                    return found
        return found

    def _detect_role(self, rel_path: str, lower: str, suffix: str) -> str:
        rel_lower = rel_path.lower()
        if rel_lower.endswith("fxmanifest.lua") or rel_lower.endswith("__resource.lua"):
            return "manifesta dependências, scripts e metadados do resource"
        if suffix == ".html":
            return "estrutura visual da NUI"
        if suffix == ".css":
            return "estilo visual da NUI"
        if suffix == ".js":
            if "fetch(`https://" in lower or "nui" in lower or "sendnuimessage" in lower:
                return "ponte da interface NUI com o jogo"
            return "lógica de interface ou cliente web"
        if suffix == ".json":
            return "dados ou configuração serializada"
        if "client" in rel_lower or "isduplicityversion" in lower or "playerpedid" in lower:
            return "lógica client-side no FiveM"
        if "server" in rel_lower or "source)" in lower or "getplayername" in lower:
            return "lógica server-side no FiveM"
        if "config" in rel_lower:
            return "configuração central do resource"
        if "shared" in rel_lower:
            return "constantes ou utilidades compartilhadas"
        return "arquivo de suporte do escopo atual"

    def _detect_features(self, rel_path: str, lower: str, suffix: str) -> list[str]:
        features: list[str] = []
        checks = [
            ("nui", ["registernuicallback", "sendnuimessage", "window.addeventlistener", "fetch(`https://"]),
            ("callbacks", ["createcallback", "triggercallback", "lib.callback", "promise.new"]),
            ("eventos de rede", ["registernetevent", "triggerserverevent", "triggerclientevent", "onnet", "emitnet"]),
            ("database", ["oxmysql", "mysql.", "exports.oxmysql", "ghmattimysql"]),
            ("qbcore", ["qbcore", "exports['qb-core']", 'exports["qb-core"]', "getcoreobject"]),
            ("ox_lib", ["@ox_lib/init.lua", "lib.notify", "lib.registercontext", "lib.callback"]),
            ("menu", ["registercommand", "openmenu", "setnuifocus"]),
            ("vehicle", ["vehicle", "setvehicle", "spawnvehicle", "veh"]),
            ("player state", ["playerdata", "playerpedid", "statebag", "localplayer.state"]),
        ]
        joined = lower + " " + rel_path.lower()
        for label, needles in checks:
            if any(n in joined for n in needles):
                features.append(label)
        if suffix == ".css" and "display:" in lower:
            features.append("layout visual")
        if suffix == ".html" and "<script" in lower:
            features.append("entrada de ui")
        return features[:8]

    def _build_notes(self, rel_path: str, lower: str, suffix: str) -> list[str]:
        notes: list[str] = []
        if suffix == ".lua" and "citizen.createthread" in lower:
            notes.append("Possui thread; vale revisar loops e waits depois.")
        if "while true do" in lower:
            notes.append("Loop infinito detectado; conferir otimização e waits.")
        if "registercommand" in lower:
            notes.append("Define comando; importante para fluxo de uso/admin.")
        if "registernuicallback" in lower or "sendnuimessage" in lower:
            notes.append("Faz ponte com NUI; client web e client lua precisam ser analisados juntos.")
        if "oxmysql" in lower or "mysql." in lower:
            notes.append("Toca banco; validar queries e criação de tabelas no próximo passe.")
        if rel_path.lower().endswith("config.lua"):
            notes.append("Arquivo de configuração; costuma explicar comportamento global do resource.")
        return notes[:5]
