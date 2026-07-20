import type { Character } from '../types'
import { FieldCaption, PanelTitle, signed } from './sheet'

/**
 * Top-of-page-1 row on the right column with the sheet's four boxed stats:
 * PROFICIENCY BONUS, INITIATIVE, SPEED, SIZE, PASSIVE PERCEPTION.
 *
 * PROFICIENCY BONUS is shown as its own left-column block on the printed
 * sheet, but rendering it here keeps the whole "at-a-glance stats" band
 * aligned as a strip along the top of the sheet body.
 */
export function TopStats({ character }: { character: Character }) {
  const { vitals } = character
  return (
    <div className="grid grid-cols-2 divide-slate-800 rounded-sm border border-slate-800 sm:grid-cols-5 sm:divide-x">
      <StatCell title="Proficiency Bonus" value={signed(vitals.proficiency_bonus)} />
      <StatCell title="Initiative" value={signed(vitals.initiative)} />
      <StatCell title="Speed" value={`${vitals.speed} ft.`} />
      <StatCell title="Size" value={vitals.size} />
      <StatCell title="Passive Perception" value={vitals.passive_perception} />
    </div>
  )
}

function StatCell({ title, value }: { title: string; value: string | number }) {
  return (
    <div className="flex flex-col border-slate-300">
      <div className="border-b border-slate-800 bg-slate-50 px-2 py-1 text-center">
        <PanelTitle>{title}</PanelTitle>
      </div>
      <div className="flex flex-1 items-center justify-center px-2 py-2">
        <span className="text-2xl font-bold tabular-nums text-slate-900">{value}</span>
      </div>
    </div>
  )
}

/**
 * Empty state kept so we can re-export the caption helper for symmetry
 * with the other sheet-level primitives.
 */
export { FieldCaption }
