"""Pydantic request-body models.

Per docs/webui-architecture.md#Serialization-boundary these describe
*request* bodies only (validation + OpenAPI docs) - response shapes are
whatever `Character.to_dict()` produces plus the injected `id`.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class CreateCharacterRequest(BaseModel):
    name: str
    class_name: str
    race_name: Optional[str] = None
    background_name: Optional[str] = None


class NameUpdate(BaseModel):
    name: str


class ClassUpdate(BaseModel):
    class_name: str


class RaceUpdate(BaseModel):
    race_name: Optional[str] = None


class BackgroundUpdate(BaseModel):
    background_name: Optional[str] = None


class SubclassUpdate(BaseModel):
    subclass_id: Optional[str] = None


class LevelUpdate(BaseModel):
    level: int


class AbilityScoreUpdate(BaseModel):
    value: int


class SkillProfUpdate(BaseModel):
    proficient: bool


class HpUpdate(BaseModel):
    value: int


class TemporaryHpUpdate(BaseModel):
    value: int


class AmountRequest(BaseModel):
    amount: int


class ChoiceUpdate(BaseModel):
    value: Any


class InventoryAddRequest(BaseModel):
    item_id: str
    quantity: int = 1


class EquipWeaponRequest(BaseModel):
    weapon_id: str


class EquipArmorRequest(BaseModel):
    armor_id: Optional[str] = None


class EquipShieldRequest(BaseModel):
    shield_id: Optional[str] = None


# Body for PATCH /background-ability-bonuses is a bare mapping, e.g.
# {"strength": 2, "wisdom": 1} - modeled as a plain dict, validated in
# the route handler itself (ability names checked against ABILITIES).
BackgroundAbilityBonusesUpdate = Dict[str, int]
