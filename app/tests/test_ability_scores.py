import pytest
from app.services.rules import ability_scores


@pytest.mark.parametrize("score,expected", [
    (1, -5), (8, -1), (9, -1), (10, 0), (11, 0),
    (12, 1), (15, 2), (20, 5), (30, 10),
])
def test_modifier(score, expected):
    assert ability_scores.modifier(score) == expected


def test_saving_throw_not_proficient():
    assert ability_scores.saving_throw(14, proficiency_bonus=2, proficient=False) == 2


def test_saving_throw_proficient():
    assert ability_scores.saving_throw(14, proficiency_bonus=2, proficient=True) == 4


def test_saving_throw_with_temp_bonus():
    assert ability_scores.saving_throw(14, proficiency_bonus=2, proficient=True, temp_bonus=1) == 5
