import type { Character } from '../types'

function Badges({ items }: { items: string[] }) {
  if (items.length === 0) {
    return <span className="text-sm text-slate-400">—</span>
  }
  return (
    <div className="flex flex-wrap gap-1">
      {items.map((item) => (
        <span
          key={item}
          className="rounded-full border border-slate-300 bg-slate-50 px-2 py-0.5 text-xs font-medium text-slate-700"
        >
          {item}
        </span>
      ))}
    </div>
  )
}

export function Proficiencies({ character }: { character: Character }) {
  const { proficiencies } = character
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
        Proficiencies
      </h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">
            Armor
          </p>
          <Badges items={proficiencies.armor} />
        </div>
        <div>
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">
            Weapons
          </p>
          <Badges items={proficiencies.weapons} />
        </div>
        <div>
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">
            Tools
          </p>
          <Badges items={proficiencies.tools} />
        </div>
        <div>
          <p className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">
            Languages
          </p>
          <Badges items={proficiencies.languages} />
        </div>
      </div>
    </section>
  )
}
