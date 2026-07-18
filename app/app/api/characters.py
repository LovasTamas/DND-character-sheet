from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.character import (
    CharacterCreate, CharacterUpdate, CharacterOut,
    SkillProficiencyIn, SavingThrowProficiencyIn,
)
from app.services import character_service

router = APIRouter(prefix="/characters", tags=["characters"])


def _to_out(character) -> CharacterOut:
    out = CharacterOut.model_validate(character)
    out.derived = character_service.compute_derived_stats(character)
    return out


@router.get("", response_model=list[CharacterOut])
def list_characters(db: Session = Depends(get_db)):
    return [_to_out(c) for c in character_service.list_characters(db)]


@router.get("/{character_id}", response_model=CharacterOut)
def get_character(character_id: int, db: Session = Depends(get_db)):
    character = character_service.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return _to_out(character)


@router.post("", response_model=CharacterOut, status_code=201)
def create_character(data: CharacterCreate, db: Session = Depends(get_db)):
    character = character_service.create_character(db, data)
    return _to_out(character)


@router.patch("/{character_id}", response_model=CharacterOut)
def update_character(character_id: int, data: CharacterUpdate, db: Session = Depends(get_db)):
    character = character_service.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    character = character_service.update_character(db, character, data)
    return _to_out(character)


@router.delete("/{character_id}", status_code=204)
def delete_character(character_id: int, db: Session = Depends(get_db)):
    character = character_service.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    character_service.delete_character(db, character)


@router.put("/{character_id}/skills", response_model=CharacterOut)
def set_skill_proficiency(character_id: int, data: SkillProficiencyIn, db: Session = Depends(get_db)):
    character = character_service.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    try:
        character = character_service.set_skill_proficiency(db, character, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_out(character)


@router.put("/{character_id}/saving-throws", response_model=CharacterOut)
def set_saving_throw_proficiency(character_id: int, data: SavingThrowProficiencyIn, db: Session = Depends(get_db)):
    character = character_service.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    try:
        character = character_service.set_saving_throw_proficiency(db, character, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_out(character)
