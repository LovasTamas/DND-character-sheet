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

type BonusMode = 'split' | 'even'

function detectMode(bonuses: Partial<Record<Ability, number>>): BonusMode {
  return Object.values(bonuses).some((v) => v === 2) ? 'split' : 'even'
}

function detectSplit(
  bonuses: Partial<Record<Ability, number>>,
): { primary: Ability | ''; secondary: Ability | '' } {
  let primary: Ability | '' = ''
  let secondary: Ability | '' = ''
  for (const [ability, value] of Object.entries(bonuses) as [Ability, number][]) {
    if (value === 2) primary = ability
    else if (value === 1) secondary = ability
  }
  return { primary, secondary }
}

/** Background ability bonus distribution panel; separate box below the ability columns. */
export function BackgroundBonuses({ character }: { character: Character }) {
  const options = character.background?.ability_options ?? []
  const [mode, setMode] = useState<BonusMode>(() => detectMode(character.background_ability_bonuses))
  const initialSplit = detectSplit(character.background_ability_bonuses)
  const [primary, setPrimary] = useState<Ability | ''>(initialSplit.primary)
  const [secondary, setSecondary] = useState<Ability | ''>(initialSplit.secondary)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const nextMode = detectMode(character.background_ability_bonuses)
    setMode(nextMode)
    const split = detectSplit(character.background_ability_bonuses)
    setPrimary(split.primary)
    setSecondary(split.secondary)
  }, [character.background_ability_bonuses])

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
    let bonuses: Partial<Record<Ability, number>>
    if (mode === 'even') {
      bonuses = Object.fromEntries(options.map((a) => [a, 1])) as Partial<Record<Ability, number>>
    } else {
      if (!primary || !secondary) {
        setError('Pick a +2 ability and a different +1 ability.')
        return
      }
      if (primary === secondary) {
        setError('The +2 and +1 abilities must be different.')
        return
      }
      bonuses = { [primary]: 2, [secondary]: 1 }
    }
    mutation.mutate(bonuses, { onError: (err) => setError(errorMessage(err)) })
  }

  const optionLabels = options.map((o) => ABILITY_ABBR[o]).join(', ')

  return (
    <Panel title="Background ability bonuses">
      <p className="mb-2 text-[10px] uppercase tracking-widest text-slate-500">
        Choose how to distribute bonuses among: {optionLabels}
      </p>
      <div className="mb-3 flex flex-wrap gap-3 text-xs text-slate-700">
        <label className="flex items-center gap-1">
          <input
            type="radio"
            name={`bg-mode-${character.id}`}
            checked={mode === 'split'}
            onChange={() => setMode('split')}
          />
          +2 / +1 (two abilities)
        </label>
        <label className="flex items-center gap-1">
          <input
            type="radio"
            name={`bg-mode-${character.id}`}
            checked={mode === 'even'}
            onChange={() => setMode('even')}
          />
          +1 / +1 / +1 (all three)
        </label>
      </div>

      {mode === 'split' ? (
        <div className="flex flex-wrap items-end gap-2">
          <label className="block text-center">
            <FieldCaption>+2</FieldCaption>
            <select
              value={primary}
              onChange={(e) => setPrimary(e.target.value as Ability | '')}
              className="rounded-sm border border-slate-400 px-1 py-0.5 text-xs"
            >
              <option value="">—</option>
              {options.map((ability) => (
                <option key={ability} value={ability}>
                  {ABILITY_ABBR[ability]}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-center">
            <FieldCaption>+1</FieldCaption>
            <select
              value={secondary}
              onChange={(e) => setSecondary(e.target.value as Ability | '')}
              className="rounded-sm border border-slate-400 px-1 py-0.5 text-xs"
            >
              <option value="">—</option>
              {options
                .filter((a) => a !== primary)
                .map((ability) => (
                  <option key={ability} value={ability}>
                    {ABILITY_ABBR[ability]}
                  </option>
                ))}
            </select>
          </label>
          <button
            type="button"
            onClick={submit}
            className="rounded-sm border border-slate-800 bg-slate-800 px-3 py-1 text-xs font-semibold uppercase text-white hover:bg-slate-700"
          >
            Save
          </button>
        </div>
      ) : (
        <div className="flex flex-wrap items-end gap-2">
          <p className="text-xs text-slate-600">
            +1 to each of: {optionLabels}
          </p>
          <button
            type="button"
            onClick={submit}
            className="rounded-sm border border-slate-800 bg-slate-800 px-3 py-1 text-xs font-semibold uppercase text-white hover:bg-slate-700"
          >
            Save
          </button>
        </div>
      )}
      <ErrorText message={error} />
    </Panel>
  )
}

/** re-export for the Sheet page */
export const ABILITY_LEFT: Ability[] = ['strength', 'dexterity', 'constitution']
export const ABILITY_RIGHT: Ability[] = ['intelligence', 'wisdom', 'charisma']
export { ABILITIES }
