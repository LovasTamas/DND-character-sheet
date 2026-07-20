"""File-backed save/load for `Character`, per PLAN_webui_backend.md §8.

Single-user, single-JSON-file-per-character MVP. Callers (API layer,
tests) should go through `save`/`load` rather than opening files
directly, so the on-disk format stays an implementation detail of this
module.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from sheet_project.engine.character import Character


def save(character: Character, path: str | Path) -> None:
    """Write `character` to `path` as its `to_save_dict()` JSON.

    Writes to a temp file first, then atomically replaces `path` (POSIX
    `os.replace`), so a crash mid-write never leaves a corrupt save file.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(character.to_save_dict(), f, indent=2)

    os.replace(tmp_path, path)


def load(path: str | Path) -> Character:
    """Read a save file and rebuild the `Character` via `from_save_dict`."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Character.from_save_dict(data)
