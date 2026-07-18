from race import Race

class Character:
    def __init__(self):
        self.name = None
        self.race = None
        self.spells = []
        self.AC = 0
        self.level = 1
        self.background = None
        self.class_type = None
    pass

    def set_name(self, name: str):
        self.name = name

    def add_race(self, race: Race):
        self.race = race

    def __str__(self):
        return (
                f"Name: {self.name}\n"
                f"{self.race}\n"
                )
