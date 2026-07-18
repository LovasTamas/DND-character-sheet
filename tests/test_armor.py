from dataclasses import dataclass, field
from app.services.rules import armor


@dataclass
class FakeItem:
    item_key: str
    item_type: str
    equipped: bool = False
    quantity: int = 1
    magic_bonus: int = 0


@dataclass
class FakeCharacter:
    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10
    inventory_items: list = field(default_factory=list)


def test_unarmored_uses_full_dex():
    c = FakeCharacter(dexterity=16)
    assert armor.armor_class(c) == 13


def test_light_armor_adds_full_dex():
    c = FakeCharacter(dexterity=16, inventory_items=[FakeItem("leather", "armor", equipped=True)])
    assert armor.armor_class(c) == 11 + 3


def test_medium_armor_caps_dex_at_2():
    c = FakeCharacter(dexterity=18, inventory_items=[FakeItem("breastplate", "armor", equipped=True)])
    assert armor.armor_class(c) == 14 + 2


def test_heavy_armor_ignores_dex():
    c = FakeCharacter(dexterity=18, inventory_items=[FakeItem("chain_mail", "armor", equipped=True)])
    assert armor.armor_class(c) == 16


def test_shield_stacks_with_body_armor():
    c = FakeCharacter(inventory_items=[
        FakeItem("chain_mail", "armor", equipped=True),
        FakeItem("shield", "shield", equipped=True),
    ])
    assert armor.armor_class(c) == 18


def test_unequipped_armor_is_ignored():
    c = FakeCharacter(dexterity=16, inventory_items=[FakeItem("chain_mail", "armor", equipped=False)])
    assert armor.armor_class(c) == 13  # falls back to unarmored


def test_magic_bonus_applies():
    c = FakeCharacter(dexterity=16, inventory_items=[FakeItem("leather", "armor", equipped=True, magic_bonus=1)])
    assert armor.armor_class(c) == 11 + 3 + 1
