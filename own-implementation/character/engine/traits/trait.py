from abc import ABC, abstractmethod

class Trait(ABC):
    def __init__(self, name, desc):
        super().__init__()
        self.name = name
        self.description = desc

    def __str__(self):
        return f"{self.name}: {' '.join(self.description)}"
    
    @abstractmethod
    def short_rest(self):
        pass
    
    @abstractmethod
    def long_rest(self):
        pass

    @abstractmethod
    def set_modifier(self, value):
        pass

    @abstractmethod
    def get_modifier(self):
        pass

    @abstractmethod
    def use_trait(self):
        pass
    
    @abstractmethod
    def level_up(self):
        pass
