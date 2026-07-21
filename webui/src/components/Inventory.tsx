import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { catalogApi } from '../api/catalog'
import { characterApi } from '../api/characters'
import { useCharacterMutation } from '../hooks/useCharacter'
import type { Character, InventoryEntry, Item } from '../types'
import { errorMessage } from './common'
import { useToast } from './Toast'
import { FieldCaption, Panel, PanelTitle } from './sheet'

function isWeapon(kind: string | undefined, category: string | undefined) {
  return kind === 'weapon' || category === 'simple' || category === 'martial'
}

function isArmor(kind: string | undefined) {
  return kind === 'armor'
}

function isShield(kind: string | undefined, category: string | undefined) {
  return kind === 'shield' || category === 'shield'
}

function weightOf(entry: InventoryEntry): number {
  const w = entry.item.weight
  if (typeof w !== 'number') return 0
  return w * entry.quantity
}

/**
 * "EQUIPPED ITEMS" table for page 2: shows equipped armor, shield and
 * weapons with AC / count / weight columns, mirroring the printed sheet.
 */
export function EquippedTable({ character }: { character: Character }) {
  const { showToast } = useToast()
  const equipArmorMutation = useCharacterMutation(character.id, (armor_id: string | null) =>
    characterApi.equipArmor(character.id, armor_id),
  )
  const equipShieldMutation = useCharacterMutation(character.id, (shield_id: string | null) =>
    characterApi.equipShield(character.id, shield_id),
  )
  const unequipWeaponMutation = useCharacterMutation(character.id, (weaponId: string) =>
    characterApi.unequipWeapon(character.id, weaponId),
  )

  const rows: Array<{
    id: string
    name: string
    ac?: number | string
    qty: number
    weight?: number
    onRemove?: () => void
  }> = []

  if (character.equipped_armor) {
    const a = character.equipped_armor
    rows.push({
      id: `armor-${a.id}`,
      name: a.name,
      ac: (a.ac_bonus as number | undefined) ?? '',
      qty: 1,
      weight: typeof a.weight === 'number' ? a.weight : undefined,
      onRemove: () =>
        equipArmorMutation.mutate(null, { onError: (err) => showToast(errorMessage(err)) }),
    })
  }
  if (character.equipped_shield) {
    const s = character.equipped_shield
    rows.push({
      id: `shield-${s.id}`,
      name: s.name,
      ac: (s.ac_bonus as number | undefined) ?? 2,
      qty: 1,
      weight: typeof s.weight === 'number' ? s.weight : undefined,
      onRemove: () =>
        equipShieldMutation.mutate(null, { onError: (err) => showToast(errorMessage(err)) }),
    })
  }
  for (const w of character.equipped_weapons) {
    rows.push({
      id: `weapon-${w.id}`,
      name: w.name,
      ac: '',
      qty: 1,
      weight: typeof w.weight === 'number' ? w.weight : undefined,
      onRemove: () =>
        unequipWeaponMutation.mutate(w.id, { onError: (err) => showToast(errorMessage(err)) }),
    })
  }

  const totalWeight = rows.reduce((sum, r) => sum + (r.weight ?? 0), 0)

  return (
    <Panel title="Equipment">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-[10px] uppercase tracking-wide text-slate-500">
            <th className="pb-1">Equipped items</th>
            <th className="pb-1 text-center">AC</th>
            <th className="pb-1 text-center">#</th>
            <th className="pb-1 text-right">Weight</th>
            <th className="pb-1" />
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id} className="border-t border-slate-200">
              <td className="py-1">{r.name}</td>
              <td className="py-1 text-center tabular-nums">{r.ac ?? ''}</td>
              <td className="py-1 text-center tabular-nums">{r.qty}</td>
              <td className="py-1 text-right tabular-nums">
                {r.weight !== undefined ? r.weight : ''}
              </td>
              <td className="py-1 text-right">
                {r.onRemove && (
                  <button
                    type="button"
                    onClick={r.onRemove}
                    className="rounded-sm border border-slate-400 px-1 text-[10px] uppercase text-slate-600 hover:bg-slate-100"
                  >
                    ×
                  </button>
                )}
              </td>
            </tr>
          ))}
          {rows.length === 0 && (
            <tr>
              <td colSpan={5} className="py-2 text-xs italic text-slate-400">
                Nothing equipped.
              </td>
            </tr>
          )}
        </tbody>
        <tfoot>
          <tr className="border-t border-slate-800">
            <td className="pt-1 text-[10px] uppercase text-slate-500">Total</td>
            <td />
            <td />
            <td className="pt-1 text-right tabular-nums">{totalWeight}</td>
            <td />
          </tr>
        </tfoot>
      </table>
    </Panel>
  )
}

/** Big "INVENTORY" panel with group buckets (weapons, armor, other) and totals. */
export function InventoryPanel({ character }: { character: Character }) {
  const { showToast } = useToast()
  const [query, setQuery] = useState('')

  const itemsQuery = useQuery({
    queryKey: ['catalog', 'equipment', query],
    queryFn: async () => {
      const [weapons, armors, items] = await Promise.all([
        catalogApi.weapons(query),
        catalogApi.armors(query),
        catalogApi.items(query),
      ])
      type Entry = { id: string; name: string; kind?: string }
      const merged: Entry[] = [
        ...weapons.map((w) => ({ id: w.id, name: w.name, kind: 'weapon' })),
        ...armors.map((a) => ({
          id: a.id,
          name: a.name,
          kind: a.category === 'shield' ? 'shield' : 'armor',
        })),
        ...items.map((i) => ({ id: i.id, name: i.name, kind: i.kind })),
      ]
      merged.sort((a, b) => a.name.localeCompare(b.name))
      return merged
    },
  })

  const addMutation = useCharacterMutation(character.id, (itemId: string) =>
    characterApi.addItem(character.id, itemId, 1),
  )
  const removeMutation = useCharacterMutation(character.id, (itemId: string) =>
    characterApi.removeItem(character.id, itemId, 1),
  )
  const equipWeaponMutation = useCharacterMutation(character.id, (weaponId: string) =>
    characterApi.equipWeapon(character.id, weaponId),
  )
  const equipArmorMutation = useCharacterMutation(character.id, (armorId: string | null) =>
    characterApi.equipArmor(character.id, armorId),
  )
  const equipShieldMutation = useCharacterMutation(character.id, (shieldId: string | null) =>
    characterApi.equipShield(character.id, shieldId),
  )

  function onError(err: unknown) {
    showToast(errorMessage(err))
  }

  const groups = useMemo(() => {
    const weapons: InventoryEntry[] = []
    const armor: InventoryEntry[] = []
    const other: InventoryEntry[] = []
    for (const e of character.inventory) {
      if (isWeapon(e.item.kind, e.item.category)) weapons.push(e)
      else if (isArmor(e.item.kind) || isShield(e.item.kind, e.item.category)) armor.push(e)
      else other.push(e)
    }
    return { weapons, armor, other }
  }, [character.inventory])

  const overallCount = character.inventory.reduce((s, e) => s + e.quantity, 0)
  const overallWeight = character.inventory.reduce((s, e) => s + weightOf(e), 0)

  return (
    <Panel title="Inventory">
      <InventoryGroup
        heading="Backpack / Carried"
        entries={groups.other}
        canEquip={() => false}
        onEquip={() => undefined}
        onRemove={(id) => removeMutation.mutate(id, { onError })}
        item={(e) => makeItemActions(e.item)}
      />
      <InventoryGroup
        heading="Weapons"
        entries={groups.weapons}
        canEquip={() => true}
        onEquip={(id) => equipWeaponMutation.mutate(id, { onError })}
        onRemove={(id) => removeMutation.mutate(id, { onError })}
        item={(e) => makeItemActions(e.item)}
      />
      <InventoryGroup
        heading="Armor & Shields"
        entries={groups.armor}
        canEquip={() => true}
        onEquip={(id, entry) => {
          if (isShield(entry.item.kind, entry.item.category)) {
            equipShieldMutation.mutate(id, { onError })
          } else {
            equipArmorMutation.mutate(id, { onError })
          }
        }}
        onRemove={(id) => removeMutation.mutate(id, { onError })}
        item={(e) => makeItemActions(e.item)}
      />

      <div className="mt-3 flex items-center justify-between border-t-2 border-slate-800 pt-2">
        <PanelTitle>Overall Weight</PanelTitle>
        <span className="tabular-nums text-sm font-semibold">
          {overallCount} items · {overallWeight}
        </span>
      </div>

      <div className="mt-3">
        <FieldCaption>Add item</FieldCaption>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search items…"
          className="mt-0.5 w-full rounded-sm border border-slate-400 px-2 py-1 text-xs"
        />
        {itemsQuery.data && itemsQuery.data.length > 0 && (
          <ul className="mt-1 max-h-40 overflow-y-auto rounded-sm border border-slate-300 text-xs">
            {itemsQuery.data.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => addMutation.mutate(item.id, { onError })}
                  className="w-full px-2 py-1 text-left hover:bg-slate-100"
                >
                  {item.name}
                  {item.kind ? <span className="text-slate-400"> ({item.kind})</span> : null}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Panel>
  )
}

function makeItemActions(_item: Item) {
  return null
}

function InventoryGroup({
  heading,
  entries,
  canEquip,
  onEquip,
  onRemove,
}: {
  heading: string
  entries: InventoryEntry[]
  canEquip: (e: InventoryEntry) => boolean
  onEquip: (id: string, entry: InventoryEntry) => void
  onRemove: (id: string) => void
  item: (e: InventoryEntry) => React.ReactNode
}) {
  const total = entries.reduce((s, e) => s + e.quantity, 0)
  const weight = entries.reduce((s, e) => s + weightOf(e), 0)
  if (entries.length === 0) return null
  return (
    <div className="mb-3">
      <div className="flex items-center justify-between border-b border-slate-400 pb-0.5">
        <PanelTitle>{heading}</PanelTitle>
        <span className="text-[10px] tabular-nums text-slate-500">
          #{total} · wt {weight}
        </span>
      </div>
      <table className="w-full text-xs">
        <tbody>
          {entries.map((e) => (
            <tr key={e.item.id} className="border-b border-slate-200 last:border-b-0">
              <td className="py-1">{e.item.name}</td>
              <td className="py-1 text-center tabular-nums">{e.quantity}</td>
              <td className="py-1 text-right tabular-nums text-slate-500">{weightOf(e)}</td>
              <td className="py-1 pl-2 text-right">
                <div className="flex justify-end gap-1">
                  {canEquip(e) && (
                    <button
                      type="button"
                      onClick={() => onEquip(e.item.id, e)}
                      className="rounded-sm border border-slate-400 px-1.5 text-[10px] uppercase hover:bg-slate-100"
                    >
                      Equip
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => onRemove(e.item.id)}
                    className="rounded-sm border border-red-400 px-1.5 text-[10px] uppercase text-red-700 hover:bg-red-50"
                  >
                    ×
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/** Static "COINS" strip mirroring page 2. Coin data isn't stored in the
 * model yet so the boxes are decorative but keep the sheet's layout. */
export function CoinsRow() {
  return (
    <Panel title="Coins">
      <div className="grid grid-cols-5 gap-2 text-center">
        {(['CP', 'SP', 'EP', 'GP', 'PP'] as const).map((c) => (
          <div key={c}>
            <input
              type="number"
              placeholder="0"
              className="w-full rounded-sm border border-slate-400 px-1 py-1 text-center text-sm tabular-nums"
            />
            <FieldCaption className="mt-0.5">{c}</FieldCaption>
          </div>
        ))}
      </div>
    </Panel>
  )
}
