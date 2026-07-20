import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from './client'
import type {
  Ability,
  Character,
  CharacterSummary,
  HitDiceSpendResult,
} from '../types'

export interface CreateCharacterBody {
  name: string
  class_name: string
  race_name?: string
  background_name?: string
}

export const characterApi = {
  list: () => apiGet<CharacterSummary[]>('/characters'),
  create: (body: CreateCharacterBody) => apiPost<Character>('/characters', body),
  get: (id: string) => apiGet<Character>(`/characters/${id}`),
  remove: (id: string) => apiDelete<void>(`/characters/${id}`),

  setName: (id: string, name: string) =>
    apiPatch<Character>(`/characters/${id}/name`, { name }),
  setClass: (id: string, class_name: string) =>
    apiPatch<Character>(`/characters/${id}/class`, { class_name }),
  setRace: (id: string, race_name: string | null) =>
    apiPatch<Character>(`/characters/${id}/race`, { race_name }),
  setBackground: (id: string, background_name: string | null) =>
    apiPatch<Character>(`/characters/${id}/background`, { background_name }),
  setSubclass: (id: string, subclass_id: string | null) =>
    apiPatch<Character>(`/characters/${id}/subclass`, { subclass_id }),
  setLevel: (id: string, level: number) =>
    apiPatch<Character>(`/characters/${id}/level`, { level }),
  setAbility: (id: string, ability: Ability, value: number) =>
    apiPatch<Character>(`/characters/${id}/ability/${ability}`, { value }),
  setBackgroundAbilityBonuses: (
    id: string,
    bonuses: Partial<Record<Ability, number>>,
  ) => apiPatch<Character>(`/characters/${id}/background-ability-bonuses`, bonuses),
  setSkillProficient: (id: string, skill: string, proficient: boolean) =>
    apiPatch<Character>(`/characters/${id}/skill/${skill}`, { proficient }),
  setHp: (id: string, value: number) =>
    apiPatch<Character>(`/characters/${id}/hp`, { value }),
  setTemporaryHp: (id: string, value: number) =>
    apiPatch<Character>(`/characters/${id}/temporary-hp`, { value }),
  damage: (id: string, amount: number) =>
    apiPost<Character>(`/characters/${id}/damage`, { amount }),
  heal: (id: string, amount: number) =>
    apiPost<Character>(`/characters/${id}/heal`, { amount }),
  spendHitDie: (id: string) =>
    apiPost<HitDiceSpendResult>(`/characters/${id}/hit-dice/spend`),
  restShort: (id: string) => apiPost<Character>(`/characters/${id}/rest/short`),
  restLong: (id: string) => apiPost<Character>(`/characters/${id}/rest/long`),
  useFeature: (id: string, featureId: string) =>
    apiPost<Character>(`/characters/${id}/feature/${featureId}/use`),
  setChoice: (id: string, featureId: string, value: string) =>
    apiPatch<Character>(`/characters/${id}/choice/${featureId}`, { value }),
  addItem: (id: string, item_id: string, quantity = 1) =>
    apiPost<Character>(`/characters/${id}/inventory`, { item_id, quantity }),
  removeItem: (id: string, itemId: string, quantity = 1) =>
    apiDelete<Character>(
      `/characters/${id}/inventory/${itemId}?quantity=${quantity}`,
    ),
  equipWeapon: (id: string, weapon_id: string) =>
    apiPost<Character>(`/characters/${id}/equipped/weapons`, { weapon_id }),
  unequipWeapon: (id: string, weaponId: string) =>
    apiDelete<Character>(`/characters/${id}/equipped/weapons/${weaponId}`),
  equipArmor: (id: string, armor_id: string | null) =>
    apiPut<Character>(`/characters/${id}/equipped/armor`, { armor_id }),
  equipShield: (id: string, shield_id: string | null) =>
    apiPut<Character>(`/characters/${id}/equipped/shield`, { shield_id }),
}
