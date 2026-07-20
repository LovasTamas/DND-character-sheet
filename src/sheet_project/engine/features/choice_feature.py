from .feature import FeatureBase


class ChoiceFeature(FeatureBase):

    def __init__(self, data):
        super().__init__(data)

        self.choice = data["choice"]

    def choose(self, character, value):

        character.choices[self.id] = value

    def use(self):
        pass

    def rest(self):
        pass