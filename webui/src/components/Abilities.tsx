import { useEffect, useState } from 'react'
import { characterApi } from '../api/characters'
import { useCharacterMutation } from '../hooks/useCharacter'
import { ABILITIES, ABILITY_ABBR } from '../types'
import type { Ability, Character, Skill } from '../types'
import { ErrorText, errorMessage } from './common'
import { useToast } from './Toast'
import { BigNumber, FieldCaption, Panel, ProfDot, signed } from './sheet'

/** Skills the PDF nests underneath each ability box on page 1. CON has none;
 * on the printed sheet the CON box carries the Heroic Inspiration slot instead. */
const SKILLS_BY_ABILITY: Record<Ability, string[]> = {
  strength: ['athletics'],
  dexterity: ['acrobatics', 'sleight_of_hand', 'stealth'],
  constitution: [],
  intelligence: ['arcana', 'history', 'investigation', 'nature', 'religion'],
  wisdom: ['animal_handling', 'insight', 'medicine', 'perception', 'survival'],
  charisma: ['deception', 'intimidation', 'performance', 'persuasion'],
}

function clampScore(value: number) {
  return Math.max(0, Math.min(20, value))
}

function skillLabel(id: string) {
  return id
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

export function AbilityColumn({
  character,
  abilities,
}: {
  character: Character
  abilities: Ability[]
}) {
  return (
    <div className="space-y-3">
      {abilities.map((a) => (
        <AbilityBlock key={a} character={character} ability={a} />
      ))}
    </div>
  )
}

function AbilityBlock({ character, ability }: { character: Character; ability: Ability }) {
  const block = character.abilities[ability]
  const [draft, setDraft] = useState(block.score)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => setDraft(block.score), [block.score])

  const mutation = useCharacterMutation(character.id, (value: number) =>
    characterApi.setAbility(character.id, ability, value),
  )

  function commit(value: number) {
    const v = clampScore(value)
    setDraft(v)
    setError(null)
    mutation.mutate(v, {
      onError: (err) => {
        setDraft(block.score)
        setError(errorMessage(err))
      },
    })
  }

  const skillIds = SKILLS_BY_ABILITY[ability]
  const skillsForAbility = character.skills.filter((s) => skillIds.includes(s.id))

  return (
    <Panel title={ability}>
      <div className="grid grid-cols-[auto_1fr] items-center gap-2">
        {/* Modifier — the big number that dominates the ability box on the PDF */}
        <div className="flex flex-col items-center rounded-sm border border-slate-800 bg-slate-50 px-3 py-2">
          <BigNumber value={signed(block.modifier)} />
          <FieldCaption className="mt-1">Modifier</FieldCaption>
        </div>
        {/* Score input */}
        <div className="flex flex-col items-center rounded-sm border border-slate-800 bg-white px-3 py-2">
          <input
            type="number"
            min={0}
            max={20}
            value={draft}
            onChange={(e) => setDraft(Number(e.target.value))}
            onBlur={(e) => commit(Number(e.target.value))}
            className="w-full border-0 bg-transparent text-center text-2xl font-bold tabular-nums text-slate-900 focus:outline-none"
          />
          <FieldCaption className="mt-1">Score</FieldCaption>
        </div>
      </div>
      <ErrorText message={error} />

      <div className="mt-2 divide-y divide-slate-200 border-t border-slate-200">
        <SaveRow character={character} ability={ability} />
        {skillsForAbility.map((skill) => (
          <SkillRow key={skill.id} character={character} skill={skill} />
        ))}
        {ability === 'constitution' && <HeroicInspirationRow />}
      </div>
    </Panel>
  )
}

function SaveRow({ character, ability }: { character: Character; ability: Ability }) {
  const { showToast } = useToast()
  const block = character.abilities[ability]
  // Saves derive from class prof list; not user-toggleable in current API so display-only dot.
  const savePropf = block.save_proficient
  return (
    <div className="flex items-center gap-2 py-1">
      <ProfDot
        state={savePropf ? 'proficient' : 'none'}
        title={savePropf ? 'Proficient save' : 'Not proficient'}
        onClick={() => showToast('Saving-throw proficiency is granted by class.')}
      />
      <span className="w-10 text-right tabular-nums text-sm font-semibold">
        {signed(block.save)}
      </span>
      <span className="text-xs uppercase tracking-wide text-slate-600">Saving Throw</span>
    </div>
  )
}

function SkillRow({ character, skill }: { character: Character; skill: Skill }) {
  const { showToast } = useToast()
  const lockedBy = skill.sources.find((s) => s === 'class' || s === 'background')
  const editable = !lockedBy
  const mutation = useCharacterMutation(
    character.id,
    ({ id, proficient }: { id: string; proficient: boolean }) =>
      characterApi.setSkillProficient(character.id, id, proficient),
  )

  function toggle() {
    if (!editable) {
      showToast(`Granted by ${lockedBy}; can't toggle.`)
      return
    }
    mutation.mutate(
      { id: skill.id, proficient: !skill.proficient },
      { onError: (err) => showToast(errorMessage(err)) },
    )
  }

  return (
    <div className="flex items-center gap-2 py-1">
      <ProfDot
        state={skill.proficient ? 'proficient' : 'none'}
        onClick={toggle}
        disabled={!editable && !skill.proficient}
        title={
          lockedBy
            ? `Granted by ${lockedBy}`
            : skill.proficient
              ? 'Proficient — click to remove'
              : 'Click to make proficient'
        }
      />
      <span className="w-10 text-right tabular-nums text-sm font-semibold">
        {signed(skill.bonus)}
      </span>
      <span className="flex-1 text-xs text-slate-800">
        {skillLabel(skill.id)}
        <span className="ml-1 text-[10px] uppercase text-slate-400">
          {ABILITY_ABBR[skill.ability]}
        </span>
      </span>
    </div>
  )
}

function HeroicInspirationRow() {
  const [checked, setChecked] = useState(false)
  return (
    <div className="flex items-center gap-2 py-1">
      <input
        type="checkbox"
        aria-label="Heroic Inspiration"
        checked={checked}
        onChange={(e) => setChecked(e.target.checked)}
        className="h-4 w-4 border border-slate-800"
      />
      <span className="text-xs uppercase tracking-wide text-slate-600">Heroic Inspiration</span>
    </div>
  )
}

/** Background ability bonus distribution panel; separate box below the ability columns. */
export function BackgroundBonuses({ character }: { character: Character }) {
  const options = character.background?.ability_options ?? []
  const [distribution, setDistribution] = useState<Partial<Record<Ability, number>>>(
    character.background_ability_bonuses,
  )
  const [error, setError] = useState<string | null>(null)

  useEffect(() => setDistribution(character.background_ability_bonuses), [
    character.background_ability_bonuses,
  ])

  const mutation = useCharacterMutation(
    character.id,
    (bonuses: Partial<Record<Ability, number>>) =>
      characterApi.setBackgroundAbilityBonuses(character.id, bonuses),
  )

  if (!character.background) {
    return (
      <Panel title="Background ability bonuses">
        <p className="text-xs text-slate-500">Pick a background to distribute ability bonuses.</p>
      </Panel>
    )
  }

  function submit() {
    setError(null)
    const cleaned = Object.fromEntries(
      Object.entries(distribution).filter(([, v]) => (v ?? 0) > 0),
    ) as Partial<Record<Ability, number>>
    mutation.mutate(cleaned, { onError: (err) => setError(errorMessage(err)) })
  }

  return (
    <Panel title="Background ability bonuses">
      <p className="mb-2 text-[10px] uppercase tracking-widest text-slate-500">
        Distribute +2/+1 or +1/+1/+1 among: {options.map((o) => ABILITY_ABBR[o]).join(', ')}
      </p>
      <div className="flex flex-wrap items-end gap-2">
        {options.map((ability) => (
          <label key={ability} className="block text-center">
            <FieldCaption>{ABILITY_ABBR[ability]}</FieldCaption>
            <input
              type="number"
              min={0}
              max={2}
              value={distribution[ability] ?? 0}
              onChange={(e) =>
                setDistribution((prev) => ({ ...prev, [ability]: Number(e.target.value) }))
              }
              className="w-14 rounded-sm border border-slate-400 px-1 py-0.5 text-center tabular-nums"
            />
          </label>
        ))}
        <button
          type="button"
          onClick={submit}
          className="rounded-sm border border-slate-800 bg-slate-800 px-3 py-1 text-xs font-semibold uppercase text-white hover:bg-slate-700"
        >
          Save
        </button>
      </div>
      <ErrorText message={error} />
    </Panel>
  )
}

/** re-export for the Sheet page */
export const ABILITY_LEFT: Ability[] = ['strength', 'dexterity', 'constitution']
export const ABILITY_RIGHT: Ability[] = ['intelligence', 'wisdom', 'charisma']
export { ABILITIES }
