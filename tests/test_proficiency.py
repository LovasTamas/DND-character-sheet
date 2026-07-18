import pytest
from app.services.rules import proficiency


@pytest.mark.parametrize("level,expected", [
    (1, 2), (4, 2), (5, 3), (8, 3), (9, 4),
    (12, 4), (13, 5), (16, 5), (17, 6), (20, 6),
])
def test_proficiency_bonus(level, expected):
    assert proficiency.proficiency_bonus(level) == expected


def test_proficiency_bonus_out_of_range():
    with pytest.raises(ValueError):
        proficiency.proficiency_bonus(0)
    with pytest.raises(ValueError):
        proficiency.proficiency_bonus(21)
