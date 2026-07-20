from sheet_project.engine.classes.abilities import ABILITIES
from sheet_project.engine.classes.proficiencies import SKILLPROF, SKILL_TO_ABILITY
from sheet_project.engine.classes.class_loader import ClassLoader
from sheet_project.engine.features.active_feature import ActiveFeature
from sheet_project.engine.rest_type import RESTTYPE


class Character:
    def __init__(self, name: str, class_name: str):

        self.name = name
        self.cl_loader = ClassLoader(class_name)

        self.level = 1
        self.character_class = self.cl_loader.load_class(self.level)

        self.ability_points = {a: 0 for a in ABILITIES}
        self.ability_modifiers = {a: 0 for a in ABILITIES}
        self.saving_throw_values = {a: 0 for a in ABILITIES}
        self.skills = {a: 0 for a in SKILLPROF}

        self.skill_profs = set()

        self.current_hp = 0
        self.initiative = 0
        self.passive_perception = 0

        self.update_automatic_values()

        self.features = dict(self.character_class.features)
        self.choices = {}

        self._initialize_features()

    def _initialize_features(self):
        for feature in self.features.values():
            if isinstance(feature, ActiveFeature):
                feature.set_values(self.level)

    def update_automatic_values(self):
        self.calculate_ability_modifiers()
        self.calculate_saving_throw_values()
        self.calculate_skills()
        self.calculate_passive_perception()

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
            self.ability_modifiers[ability] = (score - 10) // 2
        self.initiative = self.ability_modifiers[ABILITIES.DEXTERITY]

    def calculate_saving_throw_values(self):
        for ability in ABILITIES:
            value = self.ability_modifiers[ability]

            if ability in self.character_class.saving_throw_profs:
                value += self.proficiency_bonus

            self.saving_throw_values[ability] = value

    def add_skill_prof(self, skill: SKILLPROF):
        self.skill_profs.add(skill)
        self.update_automatic_values()

    def remove_skill_prof(self, skill: SKILLPROF):
        self.skill_profs.discard(skill)
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
        self.update_automatic_values()
        self.features = dict(self.character_class.features)
        self._initialize_features()

    def set_ability(self, ability:ABILITIES, value: int):
        if value > 20 or 0 > value:
            return
        self.ability_points[ability] = value
        self.update_automatic_values()

    def calculate_skills(self):
        for skill in self.skills.keys():
            self.skills[skill] = self.ability_modifiers[SKILL_TO_ABILITY[skill]]
            if skill in self.skill_profs:
                self.skills[skill] += self.proficiency_bonus

    def calculate_passive_perception(self):
        self.passive_perception = 13+self.skills[SKILLPROF.PERCEPTION]

    def apply_modifiers(self):
        pass
