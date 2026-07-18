class Feature:
    def __init__(self, name, entries):
        self.name = name
        self.entries = entries

    def __str__(self):
        return f"{self.name}: {' '.join(self.entries)}"


class Race:
    def __init__(self, json_object):
        self.parse_race(json_object)

    def __str__(self):
        traits = "\n".join(
            str(feature)
            for feature in self.class_traits
        )
        return (
            f"Race: {self.name}\n"
            f"Size: {self.size}\n"
            f"Speed: {self.speed} ft.\n"
            f"Class traits: {traits}\n"
        )

    def parse_race(self, json_object):
        self.name = json_object['name']
        self.size = json_object['size'][-1]
        self.speed = json_object['speed']
        self.class_traits = []
        self.parse_traits(json_object['entries'])

    def parse_traits(self, entries):
        for entry in entries:
            feature = Feature(entry['name'], entry['entries'])
            self.class_traits.append(feature)
