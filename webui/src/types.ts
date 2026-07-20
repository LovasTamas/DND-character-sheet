// Hand-maintained mirror of the backend Character JSON contract.
// See docs/webui-architecture.md §"Character JSON shape".

export type Ability =
  | 'strength'
  | 'dexterity'
  | 'constitution'
  | 'intelligence'
  | 'wisdom'
  | 'charisma'

export const ABILITIES: Ability[] = [
  'strength',
  'dexterity',
  'constitution',
  'intelligence',
  'wisdom',
  'charisma',
]

export const ABILITY_ABBR: Record<Ability, string> = {
  strength: 'STR',
  dexterity: 'DEX',
  constitution: 'CON',
  intelligence: 'INT',
  wisdom: 'WIS',
  charisma: 'CHA',
}

export interface CatalogEntry {
  id: string
  name: string
}

export interface CatalogWeapon extends CatalogEntry {
  category?: string
  type?: string
}

export interface CatalogArmor extends CatalogEntry {
  category?: string
}

export interface CatalogItem extends CatalogEntry {
  kind?: string
}

export interface FightingStyle extends CatalogEntry {
  desc?: string
}

export interface CharacterClass {
  id: string
  name: string
  hit_die: string
  saving_throw_profs: Ability[]
  wep_profs: string[]
  armor_profs: string[]
}

export interface CharacterRace {
  id: string
  name: string
  size: string
  speed: number
  creature_type: string
}

export interface CharacterBackground {
  id: string
  name: string
  ability_options: Ability[]
}

export interface SubclassRef {
  id: string | null
  name: string | null
}

export interface AbilityBlock {
  score: number
  effective: number
  modifier: number
  save: number
  save_proficient: boolean
}

export type Abilities = Record<Ability, AbilityBlock>

export interface Skill {
  id: string
  ability: Ability
  bonus: number
  proficient: boolean
  sources: string[]
}

export interface Vitals {
  current_hp: number
  max_hp: number
  temporary_hp: number
  ac: number
  speed: number
  initiative: number
  proficiency_bonus: number
  passive_perception: number
  size: string
  hit_die: string
  hit_dice_total: number
  hit_dice_remaining: number
}

export type FeatureKind = 'passive' | 'active' | 'choice'

export interface FeatureRecharge {
  short_rest?: number
  long_rest?: number
}

export interface Feature {
  id: string
  name: string
  desc: string
  kind: FeatureKind
  source: string
  activation?: string
  max_use?: number
  remaining_use?: number
  recharge?: FeatureRecharge
  choice?: { source: string; amount: number }
  chosen_value?: string | null
  unlocked?: boolean
  unlock_level?: number
}

export interface Item {
  id: string
  name: string
  category?: string
  kind?: string
  type?: string
  weight?: number
  ac_bonus?: number
  [key: string]: unknown
}

export interface InventoryEntry {
  item: Item
  quantity: number
}

export interface Proficiencies {
  armor: string[]
  weapons: string[]
  tools: string[]
  languages: string[]
}

export interface Character {
  id: string
  name: string
  level: number
  class: CharacterClass
  race: CharacterRace | null
  background: CharacterBackground | null
  subclass: SubclassRef
  subclass_options: CatalogEntry[]
  subclass_unlock_level: number
  abilities: Abilities
  background_ability_bonuses: Partial<Record<Ability, number>>
  skills: Skill[]
  vitals: Vitals
  features: Feature[]
  inventory: InventoryEntry[]
  equipped_weapons: Item[]
  equipped_armor: Item | null
  equipped_shield: Item | null
  proficiencies: Proficiencies
}

export interface CharacterSummary {
  id: string
  name: string
  level: number
  class_name: string
  race_name: string | null
  background_name: string | null
}

export interface ApiErrorBody {
  error: {
    code: string
    message: string
    field?: string
  }
}

export interface HitDiceSpendResult {
  die: string
  remaining: number
  character: Character
}
