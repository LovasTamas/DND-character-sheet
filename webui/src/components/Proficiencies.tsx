import type { Character } from '../types'
import { FieldCaption, Panel } from './sheet'

/** Small helper: does the proficiency list mention this armor category? */
function hasArmor(list: string[], category: string) {
  const lc = list.map((s) => s.toLowerCase())
  return lc.includes(category) || lc.some((s) => s.startsWith(category))
}

/**
 * "Equipment & Training Proficiencies" panel from page 1: armor training
 * checkboxes for light/medium/heavy/shields plus flat lists of weapons and
 * tools. Languages live on page 2 to match the printed sheet.
 */
export function TrainingProficiencies({ character }: { character: Character }) {
  const { proficiencies } = character
  const armorList = proficiencies.armor

  return (
    <Panel title="Equipment & Training Proficiencies">
      <div>
        <FieldCaption className="whitespace-nowrap">Armor Training</FieldCaption>
        <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1">
          <ArmorCheck label="Light" checked={hasArmor(armorList, 'light')} />
          <ArmorCheck label="Medium" checked={hasArmor(armorList, 'medium')} />
          <ArmorCheck label="Heavy" checked={hasArmor(armorList, 'heavy')} />
          <ArmorCheck label="Shields" checked={hasArmor(armorList, 'shield')} />
        </div>
      </div>

      <div className="mt-3">
        <FieldCaption>Weapons</FieldCaption>
        <ProfList items={proficiencies.weapons} />
      </div>

      <div className="mt-3">
        <FieldCaption>Tools</FieldCaption>
        <ProfList items={proficiencies.tools} />
      </div>
    </Panel>
  )
}

function ArmorCheck({ label, checked }: { label: string; checked: boolean }) {
  return (
    <label className="flex items-center gap-1 text-[10px] uppercase tracking-widest text-slate-700">
      <input
        type="checkbox"
        readOnly
        checked={checked}
        aria-label={`${label} armor training`}
        className="h-3 w-3 border border-slate-800"
      />
      {label}
    </label>
  )
}

function ProfList({ items }: { items: string[] }) {
  if (items.length === 0) return <p className="text-xs italic text-slate-400">None</p>
  return (
    <ul className="mt-0.5 text-xs text-slate-800">
      {items.map((it) => (
        <li key={it}>{it}</li>
      ))}
    </ul>
  )
}

/** Languages panel used on page 2. */
export function Languages({ character }: { character: Character }) {
  return (
    <Panel title="Languages">
      <ProfList items={character.proficiencies.languages} />
    </Panel>
  )
}
