"""Dependency-injected persistence: directory management, id generation,
character-by-id lookup, save-with-id, and list summaries.

Per docs/webui-architecture.md#Persistence: one JSON file per character
at `CHARACTERS_DIR/{id}.json`, filename = id = uuid4 hex assigned on
create. The file contents are `Character.to_save_dict()` (via
`sheet_project.engine.persistence.save`), which does NOT include the id
- the id lives only in the filename, so listing summaries can read the
save files directly without hydrating a full `Character`.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import List

from sheet_project.engine import persistence
from sheet_project.engine.character import Character

from .config import settings
from .errors import ApiError


def characters_dir() -> Path:
    d = settings.characters_dir
    d.mkdir(parents=True, exist_ok=True)
    return d


def generate_id() -> str:
    return uuid.uuid4().hex


def character_path(char_id: str) -> Path:
    return characters_dir() / f"{char_id}.json"


def character_exists(char_id: str) -> bool:
    return character_path(char_id).is_file()


def load_character(char_id: str) -> Character:
    """Load a character by id, raising 404 ApiError if the save file is missing."""
    path = character_path(char_id)
    if not path.is_file():
        raise ApiError(404, "character_not_found", f"Character '{char_id}' not found", field="id")
    return persistence.load(path)


def save_character(char_id: str, character: Character) -> None:
    persistence.save(character, character_path(char_id))


def delete_character(char_id: str) -> None:
    path = character_path(char_id)
    if not path.is_file():
        raise ApiError(404, "character_not_found", f"Character '{char_id}' not found", field="id")
    path.unlink()


def character_response(char_id: str, character: Character) -> dict:
    """The full character JSON body: `to_dict()` plus the injected `id`."""
    return {"id": char_id, **character.to_dict()}


def list_character_summaries() -> List[dict]:
    """List summaries for the character-list screen without hydrating a
    full `Character` - the save file already has the fields we need.
    """
    summaries = []
    for path in sorted(characters_dir().glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        summaries.append(
            {
                "id": path.stem,
                "name": data.get("name"),
                "level": data.get("level"),
                "class_name": data.get("class_name"),
                "race_name": data.get("race_name"),
                "background_name": data.get("background_name"),
            }
        )
    return summaries
