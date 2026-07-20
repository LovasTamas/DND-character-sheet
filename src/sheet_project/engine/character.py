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
from sheet_project.engine.features.choice_feature import ChoiceFeature
from sheet_project.engine.races.race_loader import RaceLoader
from sheet_project.engine.rest_type import RESTTYPE
from sheet_project.engine.serialization import serialize_dataclass, serialize_feature, serialize_value
from sheet_project.engine.subclasses.subclass_loader import SubclassLoader


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
        self.temporary_hp = 0
        self.initiative = 0
        self.passive_perception = 0
        self.speed = self.race.speed if self.race else 30
        self.size = self.race.size if self.race else "medium"
        self.creature_type = self.race.creature_type if self.race else "humanoid"

        self.hit_dice_remaining = self.level

        self.subclass: str | None = None

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
        existing_ids = {entry.item.id for entry in self.inventory}
        for equipment in resolved:
            if equipment.id not in existing_ids:
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

    @property
    def hit_dice_total(self):
        return self.level

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

    def set_temporary_hp(self, value: int):
        self.temporary_hp = max(0, value)

    def take_damage(self, amount: int):
        if amount <= 0:
            return
        absorbed = min(self.temporary_hp, amount)
        self.temporary_hp -= absorbed
        self.current_hp = max(0, self.current_hp - (amount - absorbed))

    def heal(self, amount: int):
        if amount <= 0:
            return
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    def use_feature(self, feature_id: str) -> bool:
        feature = self.features.get(feature_id)
        if isinstance(feature, ActiveFeature):
            return feature.use()
        return False

    def rest(self, rest_type: RESTTYPE):
        for feature in self.features.values():
            if isinstance(feature, ActiveFeature):
                feature.rest(rest_type)

        if rest_type == RESTTYPE.LONG:
            self.current_hp = self.max_hp
            self.temporary_hp = 0
            # MVP: restore hit dice to full. The 2024 rule (restore half,
            # rounded down, min 1) is deferred - see PLAN_webui_backend.md §5.
            self.hit_dice_remaining = self.hit_dice_total

    def spend_hit_die(self) -> str | None:
        """Spend one hit die for a short-rest heal. Returns the die (e.g. "d10")
        for the caller to roll and pass into `heal`; the engine never rolls."""
        if self.hit_dice_remaining <= 0:
            return None
        self.hit_dice_remaining -= 1
        return self.character_class.hit_die

    def level_up(self, new_level: int):
        levels_gained = max(0, new_level - self.level)
        self.level = new_level
        self.character_class = self.cl_loader.load_class(self.level)
        self.features = self._merge_features()
        self.hit_dice_remaining = min(
            self.hit_dice_total, self.hit_dice_remaining + levels_gained
        )
        self.update_automatic_values()
        self._initialize_features()

    def set_name(self, name: str):
        self.name = name

    def set_class(self, class_name: str):
        self.cl_loader = ClassLoader(class_name)
        self.character_class = self.cl_loader.load_class(self.level)
        self.subclass = None
        self.features = self._merge_features()
        self._prune_stale_choices()
        self.update_automatic_values()
        self._initialize_features()

    def set_race(self, race_name: str | None):
        self.race = RaceLoader(race_name).load_race() if race_name is not None else None
        self.speed = self.race.speed if self.race else 30
        self.size = self.race.size if self.race else "medium"
        self.creature_type = self.race.creature_type if self.race else "humanoid"
        self.features = self._merge_features()
        self._prune_stale_choices()
        self.update_automatic_values()
        self._initialize_features()

    def set_background(self, background_name: str | None):
        self.background = (
            BackgroundLoader(background_name).load_background()
            if background_name is not None else None
        )
        self.skill_profs_from_background = (
            set(self.background.skill_profs) if self.background else set()
        )
        self.tool_profs = (
            {self.background.tool_prof}
            if self.background and self.background.tool_prof is not None else set()
        )
        self.languages = set(self.background.languages) if self.background else set()
        self.background_ability_bonuses = {}
        self.features = self._merge_features()
        self._prune_stale_choices()
        self._seed_inventory_from_background()
        self.update_automatic_values()
        self._initialize_features()

    def _prune_stale_choices(self):
        self.choices = {
            feature_id: value
            for feature_id, value in self.choices.items()
            if feature_id in self.features
        }

    def set_subclass(self, subclass_id: str | None) -> bool:
        class_id = self.character_class.class_name
        if self.level < SubclassLoader.unlock_level(class_id):
            return False

        if subclass_id is not None:
            available_ids = {
                option["id"] for option in SubclassLoader().list_for_class(class_id)
            }
            if subclass_id not in available_ids:
                return False

        self.subclass = subclass_id
        self.choices[f"{class_id}_subclass"] = subclass_id
        return True

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

    def _feature_source(self, feature_id: str) -> str:
        if feature_id in self.character_class.features:
            return "class"
        if self.race and feature_id in self.race.features:
            return "race"
        if self.background and feature_id == self.background.feat.id:
            return "background"
        return "unknown"

    def _skill_sources(self, skill: SKILLPROF) -> list[str]:
        sources = []
        if skill in self.skill_profs_from_class:
            sources.append("class")
        if skill in self.skill_profs_from_background:
            sources.append("background")
        if skill in self.skill_profs_from_player:
            sources.append("player")
        return sources

    def to_dict(self) -> dict:
        """The single, stable JSON representation of this character.

        See docs/webui-architecture.md#character-json-shape for the
        authoritative schema this method emits.
        """
        class_id = self.character_class.class_name
        subclass_unlock_level = SubclassLoader.unlock_level(class_id)
        subclass_options = (
            SubclassLoader().list_for_class(class_id)
            if self.level >= subclass_unlock_level else []
        )
        subclass_name = next(
            (option["name"] for option in subclass_options if option["id"] == self.subclass),
            None,
        )

        return {
            "name": self.name,
            "level": self.level,
            "class": {
                "id": class_id,
                "name": self.character_class.name,
                "hit_die": self.character_class.hit_die,
                "saving_throw_profs": serialize_value(self.character_class.saving_throw_profs),
                "wep_profs": serialize_value(self.character_class.weapon_profs),
                "armor_profs": serialize_value(self.character_class.armor_profs),
            },
            "race": (
                {
                    "id": self.race.id,
                    "name": self.race.name,
                    "size": self.race.size,
                    "speed": self.race.speed,
                    "creature_type": self.race.creature_type,
                }
                if self.race else None
            ),
            "background": (
                {
                    "id": self.background.id,
                    "name": self.background.name,
                    "ability_options": serialize_value(self.background.ability_options),
                }
                if self.background else None
            ),
            "subclass": {"id": self.subclass, "name": subclass_name},
            "subclass_options": subclass_options,
            "subclass_unlock_level": subclass_unlock_level,
            "abilities": {
                ability.value: {
                    "score": self.ability_points[ability],
                    "effective": (
                        self.ability_points[ability]
                        + self.background_ability_bonuses.get(ability, 0)
                    ),
                    "modifier": self.ability_modifiers[ability],
                    "save": self.saving_throw_values[ability],
                    "save_proficient": ability in self.character_class.saving_throw_profs,
                }
                for ability in ABILITIES
            },
            "background_ability_bonuses": serialize_value(self.background_ability_bonuses),
            "skills": [
                {
                    "id": skill.value,
                    "ability": SKILL_TO_ABILITY[skill].value,
                    "bonus": self.skills[skill],
                    "proficient": skill in self.skill_profs,
                    "sources": self._skill_sources(skill),
                }
                for skill in SKILLPROF
            ],
            "vitals": {
                "current_hp": self.current_hp,
                "max_hp": self.max_hp,
                "temporary_hp": self.temporary_hp,
                "ac": self.ac,
                "speed": self.speed,
                "initiative": self.initiative,
                "proficiency_bonus": self.proficiency_bonus,
                "passive_perception": self.passive_perception,
                "size": self.size,
                "hit_die": self.character_class.hit_die,
                "hit_dice_total": self.hit_dice_total,
                "hit_dice_remaining": self.hit_dice_remaining,
            },
            "features": [
                {
                    **serialize_feature(feature, self.choices),
                    "source": self._feature_source(feature.id),
                }
                for feature in self.features.values()
            ],
            "inventory": [
                {"item": serialize_dataclass(entry.item), "quantity": entry.quantity}
                for entry in self.inventory
            ],
            "equipped_weapons": [serialize_dataclass(w) for w in self.equipped_weapons],
            "equipped_armor": (
                serialize_dataclass(self.equipped_armor) if self.equipped_armor else None
            ),
            "equipped_shield": (
                serialize_dataclass(self.equipped_shield) if self.equipped_shield else None
            ),
            "proficiencies": {
                "armor": serialize_value(self.character_class.armor_profs),
                "weapons": serialize_value(self.character_class.weapon_profs),
                "tools": serialize_value(self.tool_profs),
                "languages": serialize_value(self.languages),
            },
        }

    def to_save_dict(self) -> dict:
        """Input state only - no derived fields. See PLAN_webui_backend.md §8."""
        return {
            "name": self.name,
            "level": self.level,
            "class_name": self.character_class.class_name,
            "race_name": self.race.id if self.race else None,
            "background_name": self.background.id if self.background else None,
            "subclass": self.subclass,
            "ability_points": serialize_value(self.ability_points),
            "background_ability_bonuses": serialize_value(self.background_ability_bonuses),
            "skill_profs_from_player": serialize_value(self.skill_profs_from_player),
            "current_hp": self.current_hp,
            "temporary_hp": self.temporary_hp,
            "hit_dice_remaining": self.hit_dice_remaining,
            "choices": dict(self.choices),
            "inventory": [
                {"item_id": entry.item.id, "quantity": entry.quantity}
                for entry in self.inventory
            ],
            "equipped_weapon_ids": [weapon.id for weapon in self.equipped_weapons],
            "equipped_armor_id": self.equipped_armor.id if self.equipped_armor else None,
            "equipped_shield_id": self.equipped_shield.id if self.equipped_shield else None,
            "feature_remaining_use": {
                feature_id: feature.remaining_use
                for feature_id, feature in self.features.items()
                if isinstance(feature, ActiveFeature)
            },
        }

    @classmethod
    def from_save_dict(cls, data: dict) -> "Character":
        """Rebuild a Character by re-playing the same public methods used
        during normal play, so any invariant enforced there also holds here.
        """
        character = cls(
            data["name"],
            data["class_name"],
            data.get("background_name"),
            data.get("race_name"),
        )

        if data["level"] != character.level:
            character.level_up(data["level"])

        for ability_name, value in data.get("ability_points", {}).items():
            character.set_ability(ABILITIES(ability_name), value)

        background_bonuses = data.get("background_ability_bonuses")
        if background_bonuses:
            character.set_background_ability_bonuses(
                {ABILITIES(a): v for a, v in background_bonuses.items()}
            )

        for skill_name in data.get("skill_profs_from_player", []):
            character.add_skill_prof(SKILLPROF(skill_name))

        character.set_hp(data.get("current_hp", character.current_hp))
        character.set_temporary_hp(data.get("temporary_hp", 0))

        # No public setter covers restoring a saved hit-dice count directly
        # (spend_hit_die only decrements); clamp-assign it here instead.
        character.hit_dice_remaining = min(
            data.get("hit_dice_remaining", character.hit_dice_remaining),
            character.hit_dice_total,
        )

        subclass_key = f"{character.character_class.class_name}_subclass"
        for feature_id, value in data.get("choices", {}).items():
            if feature_id == subclass_key:
                character.set_subclass(value)
                continue
            feature = character.features.get(feature_id)
            if isinstance(feature, ChoiceFeature):
                feature.choose(character, value)

        # The constructor already seeded the background's starting equipment
        # into `inventory`; replace it with the saved entries so quantities
        # don't stack on top of the seed on every reload.
        character.inventory = []
        for entry in data.get("inventory", []):
            character.add_item(entry["item_id"], entry.get("quantity", 1))

        for weapon_id in data.get("equipped_weapon_ids", []):
            character.equip_weapon(weapon_id)

        if data.get("equipped_armor_id"):
            character.equip_armor(data["equipped_armor_id"])

        if data.get("equipped_shield_id"):
            character.equip_shield(data["equipped_shield_id"])

        # Likewise, remaining feature charges have no single public setter;
        # assign directly, clamped to the freshly computed max.
        for feature_id, remaining in data.get("feature_remaining_use", {}).items():
            feature = character.features.get(feature_id)
            if isinstance(feature, ActiveFeature):
                feature.remaining_use = min(remaining, feature.max_use)

        return character
