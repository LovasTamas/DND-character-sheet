from abc import ABC

class Race(ABC):
    def __init__(self, race_type):
        super().__init__()
        self.race_type = race_type