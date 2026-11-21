from __future__ import annotations
import os
from typing import Iterable


def clear_screen() -> None:
    """Clear the terminal in a cross-platform way."""
    os.system("cls" if os.name == "nt" else "clear")


def ask(label: str, default: str | None = None) -> str:
    if default is None or default == "":
        return input(f"{label}: ").strip()
    value = input(f"{label} [{default}]: ").strip()
    return value or default


def ask_bool(label: str, default: bool = True) -> bool:
    suffix = "S/n" if default else "s/N"
    value = input(f"{label} [{suffix}]: ").strip().lower()
    if not value:
        return default
    return value in {"s", "sim", "y", "yes"}


def ask_choice(title: str, options: list[str]) -> int:
    print(f"\n{title}")
    for i, option in enumerate(options, start=1):
        print(f"[{i}] {option}")
    while True:
        raw = input("Escolha: ").strip()
        if raw.isdigit():
            idx = int(raw)
            if 1 <= idx <= len(options):
                return idx - 1
        print("Opção inválida.")


def ask_multiline(label: str) -> str:
    print(f"{label} (linha vazia para concluir)")
    lines: list[str] = []
    while True:
        line = input().rstrip("\n")
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def pause() -> None:
    input("\nPressione Enter para continuar...")


def print_block(title: str, body: str) -> None:
    print(f"\n--- {title} ---")
    print(body)


def render_header(title: str, rows: Iterable[tuple[str, str]] | None = None, subtitle: str = "") -> None:
    width = 58
    clear_screen()
    print("=" * width)
    print("                     SEOUL IA FIVEM")
    print("=" * width)
    if subtitle:
        print(subtitle)
        print("-" * width)
    if rows:
        for key, value in rows:
            print(f"{key:<13}: {value}")
        print("=" * width)
