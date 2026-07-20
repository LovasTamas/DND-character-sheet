"""HTTP smoke test of the API surface, driven by FastAPI's TestClient.

Run with:
    PYTHONPATH=src .venv/bin/python src/sheet_project/tests/api_tester.py
"""
from __future__ import annotations

import os
import shutil
import tempfile

# CHARACTERS_DIR must be set BEFORE importing the app, since api.config
# builds its Settings() singleton at import time.
_tmp_characters_dir = tempfile.mkdtemp(prefix="dnd-api-test-characters-")
os.environ["CHARACTERS_DIR"] = _tmp_characters_dir

from fastapi.testclient import TestClient  # noqa: E402

from sheet_project.api.main import app  # noqa: E402

client = TestClient(app)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    try:
        run_tests()
    finally:
        shutil.rmtree(_tmp_characters_dir, ignore_errors=True)


def run_tests() -> None:
    # --- Catalog endpoints ---
    for path in (
        "/catalog/classes",
        "/catalog/races",
        "/catalog/backgrounds",
        "/catalog/feats",
        "/catalog/weapons",
        "/catalog/armors",
        "/catalog/items",
        "/catalog/fighting-styles",
    ):
        resp = client.get(f"/api/v1{path}")
        expect(resp.status_code == 200, f"GET {path} -> {resp.status_code}: {resp.text}")
        expect(isinstance(resp.json(), list), f"GET {path} did not return a list")

    resp = client.get("/api/v1/catalog/subclasses", params={"class_id": "fighter"})
    expect(resp.status_code == 200, f"GET subclasses -> {resp.status_code}")
    expect(isinstance(resp.json(), list), "subclasses is not a list")

    # --- Create character ---
    resp = client.post(
        "/api/v1/characters",
        json={
            "name": "Tomi",
            "class_name": "fighter",
            "race_name": "human",
            "background_name": "guard",
        },
    )
    expect(resp.status_code == 201, f"POST /characters -> {resp.status_code}: {resp.text}")
    body = resp.json()
    expect("id" in body and body["id"], "created character has no id")
    char_id = body["id"]

    # --- GET character shape ---
    resp = client.get(f"/api/v1/characters/{char_id}")
    expect(resp.status_code == 200, f"GET /characters/{{id}} -> {resp.status_code}")
    body = resp.json()
    for key in (
        "id",
        "name",
        "level",
        "class",
        "abilities",
        "skills",
        "vitals",
        "features",
        "inventory",
        "proficiencies",
    ):
        expect(key in body, f"character body missing key '{key}'")

    # --- PATCH /name ---
    resp = client.patch(f"/api/v1/characters/{char_id}/name", json={"name": "Tomi the Bold"})
    expect(resp.status_code == 200, f"PATCH /name -> {resp.status_code}: {resp.text}")
    expect(resp.json()["name"] == "Tomi the Bold", "name did not update")

    # --- PATCH /level ---
    resp = client.patch(f"/api/v1/characters/{char_id}/level", json={"level": 3})
    expect(resp.status_code == 200, f"PATCH /level -> {resp.status_code}: {resp.text}")
    expect(resp.json()["level"] == 3, "level did not update")

    # --- PATCH /ability/strength ---
    resp = client.patch(f"/api/v1/characters/{char_id}/ability/strength", json={"value": 15})
    expect(resp.status_code == 200, f"PATCH /ability/strength -> {resp.status_code}: {resp.text}")
    expect(resp.json()["abilities"]["strength"]["score"] == 15, "strength score did not update")

    # --- PATCH /hp ---
    resp = client.patch(f"/api/v1/characters/{char_id}/hp", json={"value": 1})
    expect(resp.status_code == 200, f"PATCH /hp -> {resp.status_code}: {resp.text}")
    expect(resp.json()["vitals"]["current_hp"] == 1, "current_hp did not update")

    # --- PATCH /temporary-hp ---
    resp = client.patch(f"/api/v1/characters/{char_id}/temporary-hp", json={"value": 5})
    expect(resp.status_code == 200, f"PATCH /temporary-hp -> {resp.status_code}: {resp.text}")
    expect(resp.json()["vitals"]["temporary_hp"] == 5, "temporary_hp did not update")

    # --- PATCH /skill/{skill} ---
    resp = client.patch(
        f"/api/v1/characters/{char_id}/skill/stealth", json={"proficient": True}
    )
    expect(resp.status_code == 200, f"PATCH /skill/stealth -> {resp.status_code}: {resp.text}")
    stealth = next(s for s in resp.json()["skills"] if s["id"] == "stealth")
    expect(stealth["proficient"] is True, "stealth proficiency did not update")

    # --- POST /damage & /heal ---
    resp = client.post(f"/api/v1/characters/{char_id}/damage", json={"amount": 1})
    expect(resp.status_code == 200, f"POST /damage -> {resp.status_code}: {resp.text}")
    expect(resp.json()["vitals"]["temporary_hp"] == 4, "damage did not absorb into temp hp first")

    resp = client.post(f"/api/v1/characters/{char_id}/heal", json={"amount": 100})
    expect(resp.status_code == 200, f"POST /heal -> {resp.status_code}: {resp.text}")
    max_hp = resp.json()["vitals"]["max_hp"]
    expect(resp.json()["vitals"]["current_hp"] == max_hp, "heal did not cap at max_hp")

    # --- POST /hit-dice/spend ---
    resp = client.get(f"/api/v1/characters/{char_id}")
    remaining_before = resp.json()["vitals"]["hit_dice_remaining"]
    resp = client.post(f"/api/v1/characters/{char_id}/hit-dice/spend")
    expect(resp.status_code == 200, f"POST /hit-dice/spend -> {resp.status_code}: {resp.text}")
    spend_body = resp.json()
    expect("die" in spend_body and spend_body["die"], "hit-dice/spend missing die")
    expect(spend_body["remaining"] == remaining_before - 1, "hit dice remaining not decremented")
    expect("character" in spend_body and spend_body["character"]["id"] == char_id, "spend missing character body")

    # --- POST /rest/short & /rest/long ---
    resp = client.post(f"/api/v1/characters/{char_id}/rest/short")
    expect(resp.status_code == 200, f"POST /rest/short -> {resp.status_code}: {resp.text}")

    resp = client.post(f"/api/v1/characters/{char_id}/rest/long")
    expect(resp.status_code == 200, f"POST /rest/long -> {resp.status_code}: {resp.text}")
    long_rest_body = resp.json()
    expect(
        long_rest_body["vitals"]["current_hp"] == long_rest_body["vitals"]["max_hp"],
        "long rest did not restore HP to max",
    )
    expect(
        long_rest_body["vitals"]["hit_dice_remaining"] == long_rest_body["vitals"]["hit_dice_total"],
        "long rest did not restore hit dice",
    )

    # --- Equip flow: add armor + shield to inventory, equip, assert AC changes ---
    resp = client.get(f"/api/v1/characters/{char_id}")
    ac_before = resp.json()["vitals"]["ac"]

    resp = client.post(
        f"/api/v1/characters/{char_id}/inventory", json={"item_id": "leather", "quantity": 1}
    )
    expect(resp.status_code == 200, f"POST /inventory (armor) -> {resp.status_code}: {resp.text}")

    resp = client.put(f"/api/v1/characters/{char_id}/equipped/armor", json={"armor_id": "leather"})
    expect(resp.status_code == 200, f"PUT /equipped/armor -> {resp.status_code}: {resp.text}")
    ac_after_armor = resp.json()["vitals"]["ac"]
    expect(ac_after_armor != ac_before, "equipping armor did not change AC")
    expect(resp.json()["equipped_armor"]["id"] == "leather", "equipped_armor not reflected")

    resp = client.post(
        f"/api/v1/characters/{char_id}/inventory", json={"item_id": "shield", "quantity": 1}
    )
    expect(resp.status_code == 200, f"POST /inventory (shield) -> {resp.status_code}: {resp.text}")

    resp = client.put(f"/api/v1/characters/{char_id}/equipped/shield", json={"shield_id": "shield"})
    expect(resp.status_code == 200, f"PUT /equipped/shield -> {resp.status_code}: {resp.text}")
    ac_after_shield = resp.json()["vitals"]["ac"]
    expect(ac_after_shield == ac_after_armor + 2, "equipping shield did not add its ac_bonus")
    expect(resp.json()["equipped_shield"]["id"] == "shield", "equipped_shield not reflected")

    # Equip conflict: item not in inventory -> 409
    resp = client.put(
        f"/api/v1/characters/{char_id}/equipped/armor", json={"armor_id": "chain_mail"}
    )
    expect(resp.status_code == 409, f"equip not-in-inventory should 409, got {resp.status_code}")
    expect(resp.json()["error"]["code"] == "item_not_in_inventory", "wrong error code for equip conflict")

    # --- Rule violations ---
    resp = client.patch(f"/api/v1/characters/{char_id}/ability/strength", json={"value": 99})
    expect(resp.status_code == 400, f"invalid ability score should 400, got {resp.status_code}")
    expect(resp.json()["error"]["code"] == "invalid_ability_score", "wrong error code for bad ability score")

    resp = client.get("/api/v1/characters/does-not-exist")
    expect(resp.status_code == 404, f"unknown character id should 404, got {resp.status_code}")
    expect(resp.json()["error"]["code"] == "character_not_found", "wrong error code for missing character")

    # --- GET /characters list includes created one ---
    resp = client.get("/api/v1/characters")
    expect(resp.status_code == 200, f"GET /characters -> {resp.status_code}")
    ids = [c["id"] for c in resp.json()]
    expect(char_id in ids, "created character missing from list")

    # --- DELETE then 404 ---
    resp = client.delete(f"/api/v1/characters/{char_id}")
    expect(resp.status_code == 204, f"DELETE /characters/{{id}} -> {resp.status_code}: {resp.text}")

    resp = client.get(f"/api/v1/characters/{char_id}")
    expect(resp.status_code == 404, f"GET deleted character should 404, got {resp.status_code}")

    print("ALL API TESTS PASSED")


if __name__ == "__main__":
    main()
