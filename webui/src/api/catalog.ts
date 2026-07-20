import { apiGet } from './client'
import type {
  CatalogArmor,
  CatalogEntry,
  CatalogItem,
  CatalogWeapon,
  FightingStyle,
} from '../types'

export const catalogApi = {
  classes: () => apiGet<CatalogEntry[]>('/catalog/classes'),
  races: () => apiGet<CatalogEntry[]>('/catalog/races'),
  backgrounds: () => apiGet<CatalogEntry[]>('/catalog/backgrounds'),
  subclasses: (classId: string) =>
    apiGet<CatalogEntry[]>(`/catalog/subclasses?class_id=${encodeURIComponent(classId)}`),
  feats: () => apiGet<CatalogEntry[]>('/catalog/feats'),
  weapons: (q = '') => apiGet<CatalogWeapon[]>(`/catalog/weapons?q=${encodeURIComponent(q)}`),
  armors: (q = '') => apiGet<CatalogArmor[]>(`/catalog/armors?q=${encodeURIComponent(q)}`),
  items: (q = '') => apiGet<CatalogItem[]>(`/catalog/items?q=${encodeURIComponent(q)}`),
  fightingStyles: () => apiGet<FightingStyle[]>('/catalog/fighting-styles'),
}
