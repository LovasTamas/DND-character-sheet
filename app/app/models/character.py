import enum
from sqlalchemy import (
    Column, Integer, String, Boolean, ForeignKey, Enum, Text
)
from sqlalchemy.orm import relationship

from app.database.db import Base


class AbilityName(str, enum.Enum):
    strength = "strength"
    dexterity = "dexterity"
    constitution = "constitution"
    intelligence = "intelligence"
    wisdom = "wisdom"
    charisma = "charisma"


class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    level = Column(Integer, nullable=False, default=1)

    species = Column(String, nullable=True)
    class_name = Column(String, nullable=True)
    subclass = Column(String, nullable=True)
    background = Column(String, nullable=True)
    alignment = Column(String, nullable=True)

    # Raw ability scores (before modifiers are derived)
    strength = Column(Integer, nullable=False, default=10)
    dexterity = Column(Integer, nullable=False, default=10)
    constitution = Column(Integer, nullable=False, default=10)
    intelligence = Column(Integer, nullable=False, default=10)
    wisdom = Column(Integer, nullable=False, default=10)
    charisma = Column(Integer, nullable=False, default=10)

    # Hit points
    max_hp_override = Column(Integer, nullable=True)  # null => derive from rules engine
    current_hp = Column(Integer, nullable=False, default=0)
    temp_hp = Column(Integer, nullable=False, default=0)

    # Death saves
    death_save_successes = Column(Integer, nullable=False, default=0)
    death_save_failures = Column(Integer, nullable=False, default=0)

    inspiration = Column(Boolean, nullable=False, default=False)
    exhaustion = Column(Integer, nullable=False, default=0)
    notes = Column(Text, nullable=True)

    skills = relationship(
        "CharacterSkill", back_populates="character", cascade="all, delete-orphan"
    )
    saving_throw_proficiencies = relationship(
        "SavingThrowProficiency", back_populates="character", cascade="all, delete-orphan"
    )


class CharacterSkill(Base):
    __tablename__ = "character_skills"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    skill_name = Column(String, nullable=False)  # e.g. "acrobatics"
    proficient = Column(Boolean, nullable=False, default=False)
    expertise = Column(Boolean, nullable=False, default=False)
    temp_bonus = Column(Integer, nullable=False, default=0)

    character = relationship("Character", back_populates="skills")


class SavingThrowProficiency(Base):
    __tablename__ = "saving_throw_proficiencies"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    ability = Column(Enum(AbilityName), nullable=False)

    character = relationship("Character", back_populates="saving_throw_proficiencies")
