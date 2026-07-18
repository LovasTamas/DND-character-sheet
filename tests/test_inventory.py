from dataclasses import dataclass, field
from app.services.rules import inventory


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
    inventory_items: list = field(default_factory=list)


def test_carrying_capacity_formula():
    assert inventory.carrying_capacity(10) == 150
    assert inventory.carrying_capacity(16) == 240


def test_total_weight_sums_quantities():
    c = FakeCharacter(inventory_items=[
        FakeItem("rations_1day", "gear", quantity=10),  # 2 lb each
        FakeItem("torch", "gear", quantity=5),  # 1 lb each
    ])
    assert inventory.total_weight(c) == 25


def test_not_encumbered_under_capacity():
    c = FakeCharacter(strength=10, inventory_items=[FakeItem("leather", "armor", equipped=True)])
    status = inventory.encumbrance_status(c)
    assert status["encumbered"] is False
    assert status["speed_penalty"] == 0


def test_encumbered_over_capacity():
    c = FakeCharacter(strength=8, inventory_items=[
        FakeItem("plate", "armor", equipped=True),
        FakeItem("chain_mail", "armor"),
    ])
    status = inventory.encumbrance_status(c)
    assert status["capacity"] == 120
    assert status["total_weight"] == 120  # 65 + 55
    assert status["encumbered"] is False  # exactly at capacity is fine

    c.inventory_items.append(FakeItem("splint", "armor"))
    status2 = inventory.encumbrance_status(c)
    assert status2["encumbered"] is True
    assert status2["speed_penalty"] == 10
