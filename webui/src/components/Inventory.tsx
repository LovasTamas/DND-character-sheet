import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { catalogApi } from '../api/catalog'
import { characterApi } from '../api/characters'
import { useCharacterMutation } from '../hooks/useCharacter'
import type { Character } from '../types'
import { errorMessage } from './common'
import { useToast } from './Toast'

function isWeapon(kind: string | undefined, category: string | undefined) {
  return kind === 'weapon' || category === 'simple' || category === 'martial'
}

function isArmor(kind: string | undefined) {
  return kind === 'armor'
}

function isShield(kind: string | undefined, category: string | undefined) {
  return kind === 'shield' || category === 'shield'
}

export function Inventory({ character }: { character: Character }) {
  const { showToast } = useToast()
  const [query, setQuery] = useState('')

  const itemsQuery = useQuery({
    queryKey: ['catalog', 'items', query],
    queryFn: () => catalogApi.items(query),
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
  const unequipWeaponMutation = useCharacterMutation(character.id, (weaponId: string) =>
    characterApi.unequipWeapon(character.id, weaponId),
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

  const armorItems = character.inventory.filter((e) => isArmor(e.item.kind))
  const shieldItems = character.inventory.filter((e) =>
    isShield(e.item.kind, e.item.category),
  )

  return (
    <section className="grid gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-2">
      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Inventory
        </h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
              <th className="pb-1">Name</th>
              <th className="pb-1">Kind</th>
              <th className="pb-1">Qty</th>
              <th className="pb-1">Weight</th>
              <th className="pb-1" />
            </tr>
          </thead>
          <tbody>
            {character.inventory.map((entry) => {
              const totalWeight =
                entry.item.weight !== undefined ? entry.item.weight * entry.quantity : undefined
              const canEquip =
                isWeapon(entry.item.kind, entry.item.category) ||
                isArmor(entry.item.kind) ||
                isShield(entry.item.kind, entry.item.category)
              return (
                <tr key={entry.item.id} className="border-t border-slate-100">
                  <td className="py-1.5">{entry.item.name}</td>
                  <td className="py-1.5 text-xs text-slate-500">{entry.item.kind ?? '—'}</td>
                  <td className="py-1.5 tabular-nums">{entry.quantity}</td>
                  <td className="py-1.5 tabular-nums text-xs text-slate-500">
                    {totalWeight !== undefined ? `${totalWeight}` : '—'}
                  </td>
                  <td className="py-1.5 text-right">
                    <div className="flex justify-end gap-1">
                      {canEquip && isWeapon(entry.item.kind, entry.item.category) && (
                        <button
                          type="button"
                          onClick={() =>
                            equipWeaponMutation.mutate(entry.item.id, { onError })
                          }
                          className="rounded-md border border-slate-300 px-2 py-0.5 text-xs hover:bg-slate-50"
                        >
                          Equip
                        </button>
                      )}
                      {isArmor(entry.item.kind) && (
                        <button
                          type="button"
                          onClick={() =>
                            equipArmorMutation.mutate(entry.item.id, { onError })
                          }
                          className="rounded-md border border-slate-300 px-2 py-0.5 text-xs hover:bg-slate-50"
                        >
                          Equip
                        </button>
                      )}
                      {isShield(entry.item.kind, entry.item.category) && (
                        <button
                          type="button"
                          onClick={() =>
                            equipShieldMutation.mutate(entry.item.id, { onError })
                          }
                          className="rounded-md border border-slate-300 px-2 py-0.5 text-xs hover:bg-slate-50"
                        >
                          Equip
                        </button>
                      )}
                      <button
                        type="button"
                        onClick={() => removeMutation.mutate(entry.item.id, { onError })}
                        className="rounded-md border border-red-300 px-2 py-0.5 text-xs text-red-700 hover:bg-red-50"
                      >
                        Remove
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
            {character.inventory.length === 0 && (
              <tr>
                <td colSpan={5} className="py-2 text-sm text-slate-500">
                  No items carried.
                </td>
              </tr>
            )}
          </tbody>
        </table>

        <div className="mt-3">
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">
            Add item
          </label>
          <div className="mt-1 flex gap-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search items…"
              className="w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
            />
          </div>
          {itemsQuery.data && itemsQuery.data.length > 0 && (
            <ul className="mt-1 max-h-40 overflow-y-auto rounded-md border border-slate-200 text-sm">
              {itemsQuery.data.map((item) => (
                <li key={item.id}>
                  <button
                    type="button"
                    onClick={() => addMutation.mutate(item.id, { onError })}
                    className="w-full px-2 py-1 text-left hover:bg-slate-50"
                  >
                    {item.name}
                    {item.kind ? ` (${item.kind})` : ''}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
          Equipped
        </h2>

        <div className="mb-3">
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Weapons</p>
          <ul className="mt-1 space-y-1">
            {character.equipped_weapons.map((weapon) => (
              <li
                key={weapon.id}
                className="flex items-center justify-between rounded-md border border-slate-200 px-2 py-1 text-sm"
              >
                <span>{weapon.name}</span>
                <button
                  type="button"
                  onClick={() => unequipWeaponMutation.mutate(weapon.id, { onError })}
                  className="rounded-md border border-slate-300 px-2 py-0.5 text-xs hover:bg-slate-50"
                >
                  Unequip
                </button>
              </li>
            ))}
            {character.equipped_weapons.length === 0 && (
              <li className="text-sm text-slate-400">—</li>
            )}
          </ul>
        </div>

        <div className="mb-3">
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">
            Armor
          </label>
          <select
            value={character.equipped_armor?.id ?? ''}
            onChange={(e) =>
              equipArmorMutation.mutate(e.target.value === '' ? null : e.target.value, {
                onError,
              })
            }
            className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
          >
            <option value="">—</option>
            {armorItems.map((entry) => (
              <option key={entry.item.id} value={entry.item.id}>
                {entry.item.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium uppercase tracking-wide text-slate-500">
            Shield
          </label>
          <select
            value={character.equipped_shield?.id ?? ''}
            onChange={(e) =>
              equipShieldMutation.mutate(e.target.value === '' ? null : e.target.value, {
                onError,
              })
            }
            className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1 text-sm"
          >
            <option value="">—</option>
            {shieldItems.map((entry) => (
              <option key={entry.item.id} value={entry.item.id}>
                {entry.item.name}
              </option>
            ))}
          </select>
        </div>
      </div>
    </section>
  )
}
