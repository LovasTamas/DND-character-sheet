from abc import ABC, abstractmethod
from sheet_project.engine.rest_type import RESTTYPE

class FeatureBase(ABC):
    def __init__(self, data):
        super().__init__()
        self.id = data["id"]
        self.name = data["name"]
        self.description = data["desc"]
        self.type = data["type"]

        self.data = data

    @abstractmethod
    def rest(self, rest_type: RESTTYPE):
        pass

    @abstractmethod
    def use(self):
        pass


class Feature(FeatureBase):
    def __init__(self, data):
        super().__init__(data)

    def rest(self, rest_type: RESTTYPE):
        pass

    def use(self):
        pass