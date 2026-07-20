import { useEffect, useState } from 'react'
import { characterApi } from '../api/characters'
import { useCharacterMutation } from '../hooks/useCharacter'
import { ABILITIES, ABILITY_ABBR } from '../types'
import type { Ability, Character } from '../types'
import { ErrorText, errorMessage } from './common'

function clampScore(value: number) {
  return Math.max(0, Math.min(20, value))
}

function signed(n: number) {
  return n >= 0 ? `+${n}` : `${n}`
}

export function Abilities({ character }: { character: Character }) {
  const [scoreDrafts, setScoreDrafts] = useState<Record<Ability, number>>(
    () =>
      Object.fromEntries(
        ABILITIES.map((a) => [a, character.abilities[a].score]),
      ) as Record<Ability, number>,
  )
  const [scoreErrors, setScoreErrors] = useState<Partial<Record<Ability, string>>>({})

  useEffect(() => {
    setScoreDrafts(
      Object.fromEntries(
        ABILITIES.map((a) => [a, character.abilities[a].score]),
      ) as Record<Ability, number>,
    )
  }, [character.abilities])

  const abilityMutation = useCharacterMutation(
    character.id,
    ({ ability, value }: { ability: Ability; value: number }) =>
      characterApi.setAbility(character.id, ability, value),
  )

  function commitScore(ability: Ability, value: number) {
    const clamped = clampScore(value)
    setScoreDrafts((prev) => ({ ...prev, [ability]: clamped }))
    setScoreErrors((prev) => ({ ...prev, [ability]: undefined }))
    abilityMutation.mutate(
      { ability, value: clamped },
      {
        onError: (err) => {
          setScoreDrafts((prev) => ({ ...prev, [ability]: character.abilities[ability].score }))
          setScoreErrors((prev) => ({ ...prev, [ability]: errorMessage(err) }))
        },
      },
    )
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
        Abilities &amp; saving throws
      </h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
            <th className="pb-1">Ability</th>
            <th className="pb-1">Score</th>
            <th className="pb-1">Effective</th>
            <th className="pb-1">Mod</th>
            <th className="pb-1">Save</th>
            <th className="pb-1">Prof.</th>
          </tr>
        </thead>
        <tbody>
          {ABILITIES.map((ability) => {
            const block = character.abilities[ability]
            return (
              <tr key={ability} className="border-t border-slate-100">
                <td className="py-1.5 font-medium">{ABILITY_ABBR[ability]}</td>
                <td className="py-1.5">
                  <input
                    type="number"
                    min={0}
                    max={20}
                    value={scoreDrafts[ability]}
                    onChange={(e) =>
                      setScoreDrafts((prev) => ({
                        ...prev,
                        [ability]: Number(e.target.value),
                      }))
                    }
                    onBlur={(e) => commitScore(ability, Number(e.target.value))}
                    className="w-16 rounded-md border border-slate-300 px-2 py-1 tabular-nums"
                  />
                  <ErrorText message={scoreErrors[ability]} />
                </td>
                <td className="py-1.5 tabular-nums">{block.effective}</td>
                <td className="py-1.5 tabular-nums">{signed(block.modifier)}</td>
                <td className="py-1.5 tabular-nums">{signed(block.save)}</td>
                <td className="py-1.5">
                  {block.save_proficient ? (
                    <span
                      title="Proficient saving throw"
                      className="inline-flex items-center gap-1 rounded-full border border-indigo-300 bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700"
                    >
                      <span aria-hidden>&#9670;</span> Prof
                    </span>
                  ) : (
                    <span className="text-xs text-slate-400">—</span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      <BackgroundAsiPanel character={character} />
    </section>
  )
}

function BackgroundAsiPanel({ character }: { character: Character }) {
  const options = character.background?.ability_options ?? []
  const [distribution, setDistribution] = useState<Partial<Record<Ability, number>>>(
    character.background_ability_bonuses,
  )
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setDistribution(character.background_ability_bonuses)
  }, [character.background_ability_bonuses])

  const mutation = useCharacterMutation(
    character.id,
    (bonuses: Partial<Record<Ability, number>>) =>
      characterApi.setBackgroundAbilityBonuses(character.id, bonuses),
  )

  if (!character.background) {
    return (
      <p className="mt-4 border-t border-slate-100 pt-3 text-sm text-slate-500">
        Pick a background to distribute ability bonuses.
      </p>
    )
  }

  function setBonus(ability: Ability, value: number) {
    setDistribution((prev) => ({ ...prev, [ability]: value }))
  }

  function submit() {
    setError(null)
    const cleaned = Object.fromEntries(
      Object.entries(distribution).filter(([, v]) => (v ?? 0) > 0),
    ) as Partial<Record<Ability, number>>
    mutation.mutate(cleaned, {
      onError: (err) => setError(errorMessage(err)),
    })
  }

  return (
    <div className="mt-4 border-t border-slate-100 pt-3">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        Background ability bonuses
      </h3>
      <p className="mt-1 text-xs text-slate-500">
        Distribute +2/+1 or +1/+1/+1 among: {options.map((o) => ABILITY_ABBR[o]).join(', ')}
      </p>
      <div className="mt-2 flex flex-wrap gap-3">
        {options.map((ability) => (
          <label key={ability} className="block text-center">
            <span className="block text-xs text-slate-500">{ABILITY_ABBR[ability]}</span>
            <input
              type="number"
              min={0}
              max={2}
              value={distribution[ability] ?? 0}
              onChange={(e) => setBonus(ability, Number(e.target.value))}
              className="mt-1 w-16 rounded-md border border-slate-300 px-2 py-1 text-center tabular-nums"
            />
          </label>
        ))}
        <button
          type="button"
          onClick={submit}
          className="self-end rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
        >
          Save
        </button>
      </div>
      <ErrorText message={error} />
    </div>
  )
}
