"""Character collection endpoints: list, create, read, delete.

Per docs/webui-architecture.md#Characters.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, status

from sheet_project.engine.backgrounds.background_loader import BackgroundLoader
from sheet_project.engine.character import Character
from sheet_project.engine.classes.class_loader import ClassLoader
from sheet_project.engine.races.race_loader import RaceLoader

from .. import deps
from ..errors import not_found
from ..schemas import CreateCharacterRequest

router = APIRouter(prefix="/characters", tags=["characters"])


def _known_ids(items: List[dict]) -> set:
    return {item["id"] for item in items}


@router.get("")
def list_characters() -> List[dict]:
    return deps.list_character_summaries()


@router.post("", status_code=status.HTTP_201_CREATED)
def create_character(body: CreateCharacterRequest) -> dict:
    if body.class_name.lower() not in _known_ids(ClassLoader.list_classes()):
        raise not_found(
            f"Unknown class '{body.class_name}'", code="unknown_class", field="class_name"
        )
    if body.race_name is not None and body.race_name.lower() not in _known_ids(RaceLoader.list_races()):
        raise not_found(f"Unknown race '{body.race_name}'", code="unknown_race", field="race_name")
    if body.background_name is not None and body.background_name.lower() not in _known_ids(
        BackgroundLoader.list_backgrounds()
    ):
        raise not_found(
            f"Unknown background '{body.background_name}'",
            code="unknown_background",
            field="background_name",
        )

    character = Character(
        name=body.name,
        class_name=body.class_name,
        background_name=body.background_name,
        race_name=body.race_name,
    )
    char_id = deps.generate_id()
    deps.save_character(char_id, character)
    return deps.character_response(char_id, character)


@router.get("/{character_id}")
def get_character(character_id: str) -> dict:
    character = deps.load_character(character_id)
    return deps.character_response(character_id, character)


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_character(character_id: str) -> None:
    deps.delete_character(character_id)
