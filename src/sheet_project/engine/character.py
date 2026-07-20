from __future__ import annotations

from sheet_project.engine.classes.abilities import ABILITIES
from sheet_project.engine.classes.proficiencies import ARMORPROF, SKILLPROF, SKILL_TO_ABILITY
from sheet_project.engine.backgrounds.background_loader import BackgroundLoader
from sheet_project.engine.classes.class_loader import ClassLoader
from sheet_project.engine.equipment.armor import Armor
from sheet_project.engine.equipment.inventory_entry import InventoryEntry
from sheet_project.engine.equipment.item import Item
from sheet_project.engine.equipment.resolver import EquipmentResolver
from sheet_project.engine.equipment.weapon import Weapon
from sheet_project.engine.features.active_feature import ActiveFeature
from sheet_project.engine.races.race_loader import RaceLoader
from sheet_project.engine.rest_type import RESTTYPE


class Character:
    def __init__(
        self,
        name: str,
        class_name: str,
        background_name: str | None = None,
        race_name: str | None = None
    ):

        self.name = name
        self.cl_loader = ClassLoader(class_name)

        self.level = 1
        self.character_class = self.cl_loader.load_class(self.level)
        self.background = (
            BackgroundLoader(background_name).load_background()
            if background_name is not None else None
        )
        self.race = (
            RaceLoader(race_name).load_race()
            if race_name is not None else None
        )

        self.ability_points = {a: 0 for a in ABILITIES}
        self.ability_modifiers = {a: 0 for a in ABILITIES}
        self.saving_throw_values = {a: 0 for a in ABILITIES}
        self.skills = {a: 0 for a in SKILLPROF}
        self.background_ability_bonuses: dict[ABILITIES, int] = {}

        self.skill_profs_from_class: set[SKILLPROF] = set()
        self.skill_profs_from_background: set[SKILLPROF] = (
            set(self.background.skill_profs) if self.background else set()
        )
        self.skill_profs_from_player: set[SKILLPROF] = set()
        self.skill_profs: set[SKILLPROF] = set()

        self.tool_profs: set[str] = (
            {self.background.tool_prof}
            if self.background and self.background.tool_prof is not None else set()
        )
        self.languages: set[str] = (
            set(self.background.languages) if self.background else set()
        )

        self.current_hp = 0
        self.initiative = 0
        self.passive_perception = 0
        self.speed = self.race.speed if self.race else 30
        self.size = self.race.size if self.race else "medium"
        self.creature_type = self.race.creature_type if self.race else "humanoid"

        self.features = self._merge_features()
        self.choices = {}

        self.inventory: list[InventoryEntry] = []
        self.equipped_weapons: list[Weapon] = []
        self.equipped_armor: Armor | None = None
        self.equipped_shield: Armor | None = None
        self.ac: int = 10

        self._seed_inventory_from_background()

        self.update_automatic_values()

        self._initialize_features()

    def _initialize_features(self):
        for feature in self.features.values():
            if isinstance(feature, ActiveFeature):
                feature.set_values(self.level)

    def _merge_features(self):
        return {
            **self.character_class.features,
            **(self.race.features if self.race else {}),
            **(
                {self.background.feat.id: self.background.feat}
                if self.background else {}
            ),
        }

    def _seed_inventory_from_background(self):
        if self.background is None:
            return
        resolved = EquipmentResolver().resolve(self.background.equipment)
        for equipment in resolved:
            self.add_item(equipment)

    def _recompute_skill_prof_union(self):
        self.skill_profs = (
            self.skill_profs_from_class
            | self.skill_profs_from_background
            | self.skill_profs_from_player
        )

    def update_automatic_values(self):
        self._recompute_skill_prof_union()
        self.calculate_ability_modifiers()
        self.calculate_saving_throw_values()
        self.calculate_skills()
        self.calculate_ac()
        self.calculate_passive_perception()
        self.apply_modifiers()

    @property
    def proficiency_bonus(self):
        return 2 + (self.level - 1) // 4

    @property
    def max_hp(self):
        return self.character_class.hitpoints.calculate(
            self.level,
            self.ability_modifiers
        )

    def calculate_ability_modifiers(self):
        for ability, score in self.ability_points.items():
            score += self.background_ability_bonuses.get(ability, 0)
            self.ability_modifiers[ability] = (score - 10) // 2
        self.initiative = self.ability_modifiers[ABILITIES.DEXTERITY]

    def calculate_saving_throw_values(self):
        for ability in ABILITIES:
            value = self.ability_modifiers[ability]

            if ability in self.character_class.saving_throw_profs:
                value += self.proficiency_bonus

            self.saving_throw_values[ability] = value

    def add_skill_prof(self, skill: SKILLPROF):
        self.skill_profs_from_player.add(skill)
        self.update_automatic_values()

    def remove_skill_prof(self, skill: SKILLPROF):
        self.skill_profs_from_player.discard(skill)
        self.update_automatic_values()

    def set_hp(self, hp: int):
        if hp >= 0 and self.max_hp >= hp:
            self.current_hp = hp

    def use_feature(self, feature_id: str) -> bool:
        feature = self.features.get(feature_id)
        if isinstance(feature, ActiveFeature):
            return feature.use()
        return False

    def rest(self, rest_type: RESTTYPE):
        for feature in self.features.values():
            if isinstance(feature, ActiveFeature):
                feature.rest(rest_type)

    def level_up(self, new_level: int):
        self.level = new_level
        self.character_class = self.cl_loader.load_class(self.level)
        self.features = self._merge_features()
        self.update_automatic_values()
        self._initialize_features()

    def set_ability(self, ability:ABILITIES, value: int):
        if value > 20 or 0 > value:
            return
        self.ability_points[ability] = value
        self.update_automatic_values()

    def set_background_ability_bonuses(self, bonuses: dict):
        if self.background is None:
            return False

        allowed_abilities = set(self.background.ability_options)
        if not set(bonuses.keys()).issubset(allowed_abilities):
            return False

        values = list(bonuses.values())
        if any(value not in {1, 2} for value in values):
            return False
        if sum(values) != 3:
            return False
        if values.count(2) > 1:
            return False

        self.background_ability_bonuses = dict(bonuses)
        self.update_automatic_values()
        return True

    def calculate_skills(self):
        for skill in self.skills.keys():
            self.skills[skill] = self.ability_modifiers[SKILL_TO_ABILITY[skill]]
            if skill in self.skill_profs:
                self.skills[skill] += self.proficiency_bonus

    def calculate_passive_perception(self):
        self.passive_perception = 13+self.skills[SKILLPROF.PERCEPTION]

    def calculate_ac(self):
        dex_mod = self.ability_modifiers[ABILITIES.DEXTERITY]

        if self.equipped_armor is None:
            base = 10 + dex_mod
        elif self.equipped_armor.dex_bonus == "full":
            base = self.equipped_armor.base_ac + dex_mod
        elif self.equipped_armor.dex_bonus == "max_2":
            base = self.equipped_armor.base_ac + min(dex_mod, 2)
        else:  # "none"
            base = self.equipped_armor.base_ac

        if self.equipped_shield is not None:
            base += self.equipped_shield.ac_bonus

        self.ac = base

    def add_item(self, item_or_id: str | Weapon | Armor | Item, quantity: int = 1):
        item = (
            EquipmentResolver().resolve([item_or_id])[0]
            if isinstance(item_or_id, str) else item_or_id
        )

        for entry in self.inventory:
            if entry.item.id == item.id:
                entry.quantity += quantity
                return
        self.inventory.append(InventoryEntry(item, quantity))

    def remove_item(self, item_id: str, quantity: int = 1):
        for entry in self.inventory:
            if entry.item.id == item_id:
                entry.quantity -= quantity
                if entry.quantity <= 0:
                    self.inventory.remove(entry)
                return

    def _find_in_inventory(self, item_id: str):
        for entry in self.inventory:
            if entry.item.id == item_id:
                return entry.item
        return None

    def equip_weapon(self, weapon_id: str):
        weapon = self._find_in_inventory(weapon_id)
        if weapon is None:
            return
        self.equipped_weapons.append(weapon)

    def unequip_weapon(self, weapon_id: str):
        for weapon in self.equipped_weapons:
            if weapon.id == weapon_id:
                self.equipped_weapons.remove(weapon)
                return

    def equip_armor(self, armor_id: str):
        armor = self._find_in_inventory(armor_id)
        if armor is None or armor.category not in (
            ARMORPROF.LIGHT, ARMORPROF.MEDIUM, ARMORPROF.HEAVY
        ):
            return
        self.equipped_armor = armor
        self.update_automatic_values()

    def unequip_armor(self):
        self.equipped_armor = None
        self.update_automatic_values()

    def equip_shield(self, armor_id: str):
        armor = self._find_in_inventory(armor_id)
        if armor is None or armor.category != ARMORPROF.SHIELD:
            return
        self.equipped_shield = armor
        self.update_automatic_values()

    def unequip_shield(self):
        self.equipped_shield = None
        self.update_automatic_values()

    def apply_modifiers(self):
        for feature in self.features.values():
            for modifier in feature.data.get("modifiers", []):
                self._apply_single_modifier(modifier)

    def _resolve_modifier_value(self, value):
        if isinstance(value, int):
            return value
        if not isinstance(value, str):
            return None
        if value == "proficiency_bonus":
            return self.proficiency_bonus
        if value == "level":
            return self.level
        if value.startswith("ability_modifier."):
            return self.ability_modifiers[ABILITIES(value.removeprefix("ability_modifier."))]
        return None

    def _apply_single_modifier(self, modifier):
        value = self._resolve_modifier_value(modifier.get("value"))
        if value is None:
            return

        target = modifier.get("target", "")
        op = modifier.get("op")

        direct_targets = {
            "initiative": "initiative",
            "passive_perception": "passive_perception",
            "ac": "ac",
        }
        if target in direct_targets:
            self._apply_attribute_modifier(direct_targets[target], op, value)
            return

        target_prefixes = {
            "ability.": (self.ability_modifiers, ABILITIES),
            "skill.": (self.skills, SKILLPROF),
            "save.": (self.saving_throw_values, ABILITIES),
        }
        for prefix, (target_dict, enum_type) in target_prefixes.items():
            if target.startswith(prefix):
                try:
                    key = enum_type(target.removeprefix(prefix))
                except ValueError:
                    return
                self._apply_dict_modifier(target_dict, key, op, value)
                return

    def _apply_attribute_modifier(self, attribute, op, value):
        if not hasattr(self, attribute):
            return
        current_value = getattr(self, attribute)
        if op == "add":
            setattr(self, attribute, current_value + value)
        elif op == "set":
            setattr(self, attribute, value)

    def _apply_dict_modifier(self, target_dict, key, op, value):
        if key not in target_dict:
            return
        if op == "add":
            target_dict[key] += value
        elif op == "set":
            target_dict[key] = value
