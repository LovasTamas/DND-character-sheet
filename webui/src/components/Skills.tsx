import { characterApi } from '../api/characters'
import { useCharacterMutation } from '../hooks/useCharacter'
import { ABILITY_ABBR } from '../types'
import type { Character, Skill } from '../types'
import { errorMessage } from './common'
import { useToast } from './Toast'

function signed(n: number) {
  return n >= 0 ? `+${n}` : `${n}`
}

function skillLabel(id: string) {
  return id
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

export function Skills({ character }: { character: Character }) {
  const { showToast } = useToast()

  const skillMutation = useCharacterMutation(
    character.id,
    ({ skill, proficient }: { skill: string; proficient: boolean }) =>
      characterApi.setSkillProficient(character.id, skill, proficient),
  )

  function toggle(skill: Skill) {
    skillMutation.mutate(
      { skill: skill.id, proficient: !skill.proficient },
      { onError: (err) => showToast(errorMessage(err)) },
    )
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
        Skills
      </h2>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
            <th className="pb-1">Prof.</th>
            <th className="pb-1">Skill</th>
            <th className="pb-1">Ability</th>
            <th className="pb-1">Bonus</th>
          </tr>
        </thead>
        <tbody>
          {character.skills.map((skill) => {
            const editable = !skill.sources.some(
              (s) => s === 'class' || s === 'background',
            )
            const lockedSource = skill.sources.find(
              (s) => s === 'class' || s === 'background',
            )
            return (
              <tr key={skill.id} className="border-t border-slate-100">
                <td className="py-1.5">
                  <input
                    type="checkbox"
                    checked={skill.proficient}
                    disabled={!editable}
                    onChange={() => editable && toggle(skill)}
                    aria-label={`${skillLabel(skill.id)} proficiency`}
                  />
                </td>
                <td className="py-1.5">
                  {skillLabel(skill.id)}
                  {!editable && lockedSource && (
                    <span
                      title={`Granted by ${lockedSource}`}
                      className="ml-2 inline-block rounded-full border border-slate-300 bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium uppercase text-slate-600"
                    >
                      {lockedSource}
                    </span>
                  )}
                </td>
                <td className="py-1.5 text-xs text-slate-500">
                  ({ABILITY_ABBR[skill.ability]})
                </td>
                <td className="py-1.5 tabular-nums">{signed(skill.bonus)}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </section>
  )
}
