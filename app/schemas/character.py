from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AbilityScoresIn(BaseModel):
    strength: int = Field(10, ge=1, le=30)
    dexterity: int = Field(10, ge=1, le=30)
    constitution: int = Field(10, ge=1, le=30)
    intelligence: int = Field(10, ge=1, le=30)
    wisdom: int = Field(10, ge=1, le=30)
    charisma: int = Field(10, ge=1, le=30)


class CharacterCreate(BaseModel):
    name: str
    level: int = Field(1, ge=1, le=20)
    species: Optional[str] = None
    class_name: Optional[str] = None
    subclass: Optional[str] = None
    background: Optional[str] = None
    alignment: Optional[str] = None
    abilities: AbilityScoresIn = AbilityScoresIn()


class CharacterUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[int] = Field(None, ge=1, le=20)
    species: Optional[str] = None
    class_name: Optional[str] = None
    subclass: Optional[str] = None
    background: Optional[str] = None
    alignment: Optional[str] = None
    strength: Optional[int] = Field(None, ge=1, le=30)
    dexterity: Optional[int] = Field(None, ge=1, le=30)
    constitution: Optional[int] = Field(None, ge=1, le=30)
    intelligence: Optional[int] = Field(None, ge=1, le=30)
    wisdom: Optional[int] = Field(None, ge=1, le=30)
    charisma: Optional[int] = Field(None, ge=1, le=30)
    current_hp: Optional[int] = None
    temp_hp: Optional[int] = None
    inspiration: Optional[bool] = None
    exhaustion: Optional[int] = Field(None, ge=0, le=6)
    notes: Optional[str] = None


class SkillProficiencyIn(BaseModel):
    skill_name: str
    proficient: bool = False
    expertise: bool = False
    temp_bonus: int = 0


class SavingThrowProficiencyIn(BaseModel):
    ability: str  # one of AbilityName values


class InventoryItemIn(BaseModel):
    item_key: str
    item_type: str  # weapon | armor | shield | gear
    quantity: int = Field(1, ge=1)
    equipped: bool = False
    attuned: bool = False
    magic_bonus: int = 0


class InventoryItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_key: str
    item_type: str
    quantity: int
    equipped: bool
    attuned: bool
    magic_bonus: int


class CurrencyUpdate(BaseModel):
    copper: Optional[int] = Field(None, ge=0)
    silver: Optional[int] = Field(None, ge=0)
    electrum: Optional[int] = Field(None, ge=0)
    gold: Optional[int] = Field(None, ge=0)
    platinum: Optional[int] = Field(None, ge=0)


class DerivedStats(BaseModel):
    """Computed by the rules engine — never set directly by the client."""
    ability_modifiers: dict[str, int]
    proficiency_bonus: int
    max_hp: int
    initiative: int
    armor_class: int
    passive_perception: int
    skills: dict[str, int]
    saving_throws: dict[str, int]
    carrying_capacity: int
    total_weight: float
    encumbered: bool
    speed_penalty: int


class CharacterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    level: int
    species: Optional[str]
    class_name: Optional[str]
    subclass: Optional[str]
    background: Optional[str]
    alignment: Optional[str]
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    current_hp: int
    temp_hp: int
    inspiration: bool
    exhaustion: int
    notes: Optional[str]
    copper: int
    silver: int
    electrum: int
    gold: int
    platinum: int
    inventory_items: list[InventoryItemOut] = []
    derived: Optional[DerivedStats] = None
