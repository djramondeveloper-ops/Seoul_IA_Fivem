"""Automatic FiveM framework and integration detection (read-only)."""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path

FRAMEWORKS = {
    "qbox": {"resources": {"qbx_core": 95}, "patterns": [("exports.qbx_core", 35), ("@qbx_core", 30)]},
    "qbcore": {"resources": {"qb-core": 95}, "patterns": [("exports['qb-core']", 35), ('exports["qb-core"]', 35), ("QBCore.Functions", 15)]},
    "esx": {"resources": {"es_extended": 95}, "patterns": [("exports['es_extended']", 35), ("ESX.GetPlayerFromId", 20)]},
    "vrp": {"resources": {"vrp": 85}, "patterns": [("Proxy.getInterface", 25), ("vRP.getUserId", 25)]},
}
INTEGRATIONS = {
    "inventory": ("ox_inventory", "qb-inventory", "qs-inventory", "codem-inventory"),
    "target": ("ox_target", "qb-target", "qtarget"),
    "database": ("oxmysql", "mysql-async", "ghmattimysql"),
    "voice": ("pma-voice", "mumble-voip", "saltychat"),
    "banking": ("oxlyn-banking", "renewed-banking", "qb-banking"),
    "police": ("rcore_police", "qbx_police", "qb-policejob"),
    "medical": ("op-ambulancejob", "qbx_ambulancejob", "qb-ambulancejob"),
}
SKIP = {".git", "node_modules", ".venv", "__pycache__", "cache"}

def detect_frameworks(project_path: str | Path, max_files: int = 2000) -> dict:
    root = Path(project_path).resolve()
    if not root.is_dir():
        raise ValueError(f"Invalid project directory: {root}")
    resources: dict[str, Path] = {}
    for manifest in root.rglob("fxmanifest.lua"):
        if any(part in SKIP for part in manifest.relative_to(root).parts):
            continue
        resources.setdefault(manifest.parent.name.lower(), manifest.parent)
    for manifest in root.rglob("__resource.lua"):
        if any(part in SKIP for part in manifest.relative_to(root).parts):
            continue
        resources.setdefault(manifest.parent.name.lower(), manifest.parent)
    scores = {name: 0 for name in FRAMEWORKS}
    evidence = {name: [] for name in FRAMEWORKS}
    for name, spec in FRAMEWORKS.items():
        for resource, weight in spec["resources"].items():
            if resource in resources:
                scores[name] += weight
                evidence[name].append(f"Resource found: {resource}")
    scanned = 0
    for path in root.rglob("*"):
        if scanned >= max_files:
            break
        if not path.is_file() or path.suffix.lower() not in {".lua", ".cfg"}:
            continue
        if any(part in SKIP for part in path.relative_to(root).parts):
            continue
        if path.stat().st_size > 250_000:
            continue
        scanned += 1
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name, spec in FRAMEWORKS.items():
            for pattern, weight in spec["patterns"]:
                if pattern in content and f"Code reference: {pattern}" not in evidence[name]:
                    scores[name] += weight
                    evidence[name].append(f"Code reference: {pattern}")
    detected = [
        {"framework": name, "score": scores[name], "confidence": "high" if scores[name] >= 85 else "medium" if scores[name] >= 35 else "low", "evidence": evidence[name]}
        for name in FRAMEWORKS if scores[name] > 0
    ]
    detected.sort(key=lambda x: x["score"], reverse=True)
    return {
        "project": str(root),
        "frameworks": detected,
        "primary_framework": detected[0]["framework"] if detected and detected[0]["score"] >= 85 else None,
        "hybrid_or_bridge_possible": len([x for x in detected if x["score"] >= 35]) > 1,
        "integrations": {group: [r for r in names if r in resources] for group, names in INTEGRATIONS.items()},
        "resources_found": len(resources),
        "files_scanned": scanned,
        "scan_limited": scanned >= max_files,
        "note": "Heuristic evidence only; confirm actual APIs, exports and bridges before editing.",
    }
