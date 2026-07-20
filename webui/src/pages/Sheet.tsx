import { useNavigate, useParams } from 'react-router-dom'
import { useCharacterQuery } from '../hooks/useCharacter'
import {
  ABILITY_LEFT,
  ABILITY_RIGHT,
  AbilityColumn,
  BackgroundBonuses,
} from '../components/Abilities'
import { ClassFeatures, SpeciesAndFeats, WeaponsAndDamage } from '../components/Features'
import { CoinsRow, EquippedTable, InventoryPanel } from '../components/Inventory'
import { Header } from '../components/Header'
import { HpActions } from '../components/HpActions'
import { Languages, TrainingProficiencies } from '../components/Proficiencies'
import { Panel, PanelTitle } from '../components/sheet'
import { TopStats } from '../components/TopStats'

export function Sheet() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: character, isLoading, isError } = useCharacterQuery(id ?? '')

  if (!id) return null

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-8">
        <p className="text-slate-500">Loading character…</p>
      </div>
    )
  }
  if (isError || !character) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-8">
        <p className="text-red-700">Failed to load this character.</p>
        <button
          type="button"
          onClick={() => navigate('/')}
          className="mt-4 rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-50"
        >
          Back to characters
        </button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-[1200px] space-y-6 px-4 py-6">
      <button
        type="button"
        onClick={() => navigate('/')}
        className="text-sm font-medium text-indigo-700 hover:underline"
      >
        ← Characters
      </button>

      {/* ─── PAGE 1 ───────────────────────────────────────────────────── */}
      <article
        aria-label="Character sheet — page 1"
        className="space-y-3 rounded-md bg-white p-4 shadow-md ring-1 ring-slate-300"
      >
        <BrandStrip />
        <Header character={character} />

        <div className="grid gap-3 lg:grid-cols-12">
          {/* Left column: STR / DEX / CON blocks + Equipment training */}
          <div className="space-y-3 lg:col-span-3">
            <AbilityColumn character={character} abilities={ABILITY_LEFT} />
            <TrainingProficiencies character={character} />
          </div>

          {/* Middle column: INT / WIS / CHA blocks + background bonuses */}
          <div className="space-y-3 lg:col-span-3">
            <AbilityColumn character={character} abilities={ABILITY_RIGHT} />
            <BackgroundBonuses character={character} />
          </div>

          {/* Right column: top stats strip, weapons, class features, species+feats */}
          <div className="space-y-3 lg:col-span-6">
            <TopStats character={character} />
            <WeaponsAndDamage character={character} />
            <ClassFeatures character={character} />
            <SpeciesAndFeats character={character} />
          </div>
        </div>

        <HpActions character={character} />
      </article>

      {/* ─── PAGE 2 ───────────────────────────────────────────────────── */}
      <article
        aria-label="Character sheet — page 2"
        className="space-y-3 rounded-md bg-white p-4 shadow-md ring-1 ring-slate-300"
      >
        <BrandStrip />

        <div className="grid gap-3 lg:grid-cols-12">
          <div className="space-y-3 lg:col-span-8">
            <SpellcastingPlaceholder />
            <PersonalityPlaceholder />
          </div>
          <div className="space-y-3 lg:col-span-4">
            <Languages character={character} />
            <EquippedTable character={character} />
            <InventoryPanel character={character} />
            <CoinsRow />
          </div>
        </div>
      </article>
    </div>
  )
}

function BrandStrip() {
  return (
    <div className="border-b border-slate-800 pb-2 text-center">
      <h1 className="text-2xl font-black uppercase tracking-[0.35em] text-slate-800">
        Dungeons <span className="text-slate-500">&amp;</span> Dragons
        <span className="ml-1 align-top text-[10px]">®</span>
      </h1>
    </div>
  )
}

/** Placeholder spellcasting box — model doesn't carry spellbook data yet,
 * so this preserves the layout of page 2 without asserting fake numbers. */
function SpellcastingPlaceholder() {
  return (
    <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_2fr]">
      <Panel title="Spellcasting">
        <div className="space-y-2 text-xs">
          <div>
            <PanelTitle>Ability</PanelTitle>
            <div className="mt-0.5 h-6 border-b border-slate-400" />
          </div>
          <div>
            <PanelTitle>Modifier</PanelTitle>
            <div className="mt-0.5 h-6 border-b border-slate-400" />
          </div>
          <div>
            <PanelTitle>Spell Save DC</PanelTitle>
            <div className="mt-0.5 h-6 border-b border-slate-400" />
          </div>
          <div>
            <PanelTitle>Spell Attack Bonus</PanelTitle>
            <div className="mt-0.5 h-6 border-b border-slate-400" />
          </div>
        </div>
      </Panel>
      <Panel title="Spell Slots">
        <div className="grid grid-cols-3 gap-2 text-xs">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="rounded-sm border border-slate-400 px-2 py-1 text-center">
              <div className="text-[10px] uppercase tracking-widest text-slate-500">
                Level {i + 1}
              </div>
              <div className="mt-1 flex justify-center gap-0.5">
                {Array.from({ length: 4 }).map((_, j) => (
                  <input
                    key={j}
                    type="checkbox"
                    aria-label={`Level ${i + 1} slot ${j + 1}`}
                    className="h-2.5 w-2.5 border border-slate-500"
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}

function PersonalityPlaceholder() {
  const cells = ['Traits', 'Ideals', 'Bonds', 'Flaws'] as const
  return (
    <>
      <Panel title="Personality">
        <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
          {cells.map((label) => (
            <div key={label}>
              <div className="text-center text-[10px] font-bold uppercase tracking-widest text-slate-700">
                {label}
              </div>
              <textarea
                rows={4}
                className="mt-1 w-full resize-y rounded-sm border border-slate-400 px-1 py-0.5 text-xs"
              />
            </div>
          ))}
        </div>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-widest text-slate-700">
              Alignment
            </div>
            <input
              type="text"
              className="mt-1 w-full rounded-sm border border-slate-400 px-1 py-0.5 text-xs"
            />
          </div>
          <div>
            <div className="text-[10px] font-bold uppercase tracking-widest text-slate-700">
              Appearance
            </div>
            <textarea
              rows={2}
              className="mt-1 w-full resize-y rounded-sm border border-slate-400 px-1 py-0.5 text-xs"
            />
          </div>
        </div>
      </Panel>

      <Panel title="Cantrips & Prepared Spells">
        <p className="text-xs italic text-slate-400">
          Spellcasting isn't tracked in the model yet.
        </p>
      </Panel>
    </>
  )
}
