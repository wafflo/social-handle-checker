from __future__ import annotations

from importlib.resources import files
from pathlib import Path

WORDLIST_PACKAGE = "social_handle_checker.data.wordlists"


def list_builtin_wordlists() -> list[str]:
    base = files(WORDLIST_PACKAGE)
    names: list[str] = []
    for entry in base.iterdir():
        if entry.name.endswith(".txt"):
            names.append(entry.name.removesuffix(".txt"))
    return sorted(names)


def load_builtin_wordlist(name: str) -> list[str]:
    target = files(WORDLIST_PACKAGE).joinpath(f"{name}.txt")
    if not target.is_file():
        available = ", ".join(list_builtin_wordlists())
        raise FileNotFoundError(f"Unknown built-in wordlist '{name}'. Available: {available}")
    return [line.strip() for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_user_wordlist(path: str | Path) -> list[str]:
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(f"Wordlist not found: {target}")
    return [line.strip() for line in target.read_text(encoding="utf-8").splitlines() if line.strip()]
