from dataclasses import dataclass, field
from app.services.rules import skills


@dataclass
class FakeSkillRow:
    skill_name: str
    proficient: bool = False
    expertise: bool = False
    temp_bonus: int = 0


@dataclass
class FakeCharacter:
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    skills: list = field(default_factory=list)


def test_skill_value_no_proficiency():
    assert skills.skill_value("stealth", ability_score=14, proficiency_bonus=2) == 2


def test_skill_value_proficient():
    assert skills.skill_value("stealth", 14, 2, proficient=True) == 4


def test_skill_value_expertise():
    assert skills.skill_value("stealth", 14, 2, proficient=True, expertise=True) == 6


def test_skill_value_unknown_skill_raises():
    import pytest
    with pytest.raises(ValueError):
        skills.skill_value("juggling", 10, 2)


def test_all_skill_values_defaults_to_no_proficiency():
    char = FakeCharacter(dexterity=14)
    values = skills.all_skill_values(char, proficiency_bonus=2)
    assert values["stealth"] == 2  # +2 dex mod, no proficiency
    assert len(values) == len(skills.SKILL_ABILITY_MAP)


def test_all_skill_values_applies_proficiency_row():
    char = FakeCharacter(wisdom=16, skills=[FakeSkillRow("perception", proficient=True)])
    values = skills.all_skill_values(char, proficiency_bonus=3)
    assert values["perception"] == 3 + 3  # +3 wis mod, +3 proficiency


def test_passive_score():
    assert skills.passive_score(5) == 15
