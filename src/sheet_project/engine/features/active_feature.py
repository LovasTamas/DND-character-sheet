from .feature import FeatureBase


class ActiveFeature(FeatureBase):

    def __init__(self, data):
        super().__init__(data)

        self.activation = data.get("activation")
        self.resource = data.get("resource")
        self.effect = data.get("effect")

        self.max_use = 0
        self.remaining_use = 0

    def max_uses(self, level: int) -> int:
        amount = self.resource["amount"]
        applicable_levels = [lvl for lvl in amount.keys() if int(lvl) <= level]
        if not applicable_levels:
            return 0
        best_level = max(applicable_levels, key=int)
        return amount[best_level]

    def set_values(self, level: int):
        new_max = self.max_uses(level)

        if self.max_use == 0:
            self.remaining_use = new_max
        else:
            gained = new_max - self.max_use
            if gained > 0:
                self.remaining_use = min(new_max, self.remaining_use + gained)

        self.max_use = new_max

    def use(self) -> bool:
        if self.remaining_use > 0:
            self.remaining_use -= 1
            return True
        return False

    def rest(self, rest_type):
        recharge = self.resource.get("recharge", {})
        amount = recharge.get(rest_type.value, 0)

        if amount == -1:
            self.remaining_use = self.max_use
        elif amount > 0:
            self.remaining_use = min(self.max_use, self.remaining_use + amount)