from dataclasses import dataclass, field
import pytest
from app.services.rules import weapons


@dataclass
class FakeCharacter:
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    inventory_items: list = field(default_factory=list)


def test_finesse_prefers_higher_ability():
    c = FakeCharacter(strength=10, dexterity=18)
    assert weapons.attack_ability(c, {"category": "martial_melee", "properties": ["finesse"]}) == "dexterity"

    c2 = FakeCharacter(strength=18, dexterity=10)
    assert weapons.attack_ability(c2, {"category": "martial_melee", "properties": ["finesse"]}) == "strength"


def test_non_finesse_melee_uses_strength():
    c = FakeCharacter(strength=16, dexterity=12)
    data = {"category": "martial_melee", "properties": ["heavy", "two_handed"]}
    assert weapons.attack_ability(c, data) == "strength"


def test_ranged_weapon_uses_dexterity():
    c = FakeCharacter(strength=16, dexterity=12)
    data = {"category": "martial_ranged", "properties": ["ammunition", "heavy", "two_handed"]}
    assert weapons.attack_ability(c, data) == "dexterity"


def test_attack_bonus_combines_mod_prof_magic():
    c = FakeCharacter(dexterity=18)
    bonus = weapons.attack_bonus(c, "rapier", proficient=True, proficiency_bonus=2, magic_bonus=1)
    assert bonus == 4 + 2 + 1


def test_attack_bonus_without_proficiency():
    c = FakeCharacter(dexterity=18)
    bonus = weapons.attack_bonus(c, "rapier", proficient=False, proficiency_bonus=2)
    assert bonus == 4


def test_damage_returns_correct_dice_and_type():
    c = FakeCharacter(dexterity=18)
    result = weapons.damage(c, "rapier", magic_bonus=1)
    assert result == {"dice": "1d8", "modifier": 5, "damage_type": "piercing", "mastery": "vex"}


def test_versatile_damage_uses_two_handed_die():
    c = FakeCharacter(strength=16)
    result = weapons.damage(c, "longsword", use_versatile=True)
    assert result["dice"] == "1d10"


def test_versatile_raises_if_weapon_lacks_property():
    c = FakeCharacter(strength=16)
    with pytest.raises(ValueError):
        weapons.damage(c, "dagger", use_versatile=True)


def test_unknown_weapon_raises():
    c = FakeCharacter()
    with pytest.raises(ValueError):
        weapons.attack_bonus(c, "does_not_exist")
