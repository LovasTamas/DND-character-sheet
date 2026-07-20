import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { catalogApi } from '../api/catalog'
import { characterApi } from '../api/characters'
import { useCharacterMutation } from '../hooks/useCharacter'
import type { Character, Feature, Item } from '../types'
import { errorMessage } from './common'
import { useToast } from './Toast'
import { Panel, signed } from './sheet'

const ACTION_GLYPH: Record<string, string> = {
  action: '●',
  bonus_action: '▲',
  reaction: '◆',
  limited: '■',
}

function activationGlyph(activation?: string) {
  if (!activation) return ''
  const key = activation.toLowerCase().replace(/\s+/g, '_')
  return ACTION_GLYPH[key] ?? ''
}

/** WEAPONS & DAMAGE box, matching the PDF weapons table with attack bonus,
 * damage and notes columns computed from equipped weapons. */
export function WeaponsAndDamage({ character }: { character: Character }) {
  const strMod = character.abilities.strength.modifier
  const dexMod = character.abilities.dexterity.modifier
  const pb = character.vitals.proficiency_bonus

  return (
    <Panel title="Weapons & Damage · Cantrips">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-[10px] uppercase tracking-wide text-slate-500">
            <th className="pb-1">Name</th>
            <th className="pb-1 text-center">Bonus</th>
            <th className="pb-1">Damage</th>
            <th className="pb-1">Notes</th>
          </tr>
        </thead>
        <tbody>
          {character.equipped_weapons.map((w) => (
            <WeaponRow key={w.id} weapon={w} strMod={strMod} dexMod={dexMod} pb={pb} />
          ))}
          {Array.from({ length: Math.max(0, 4 - character.equipped_weapons.length) }).map(
            (_, i) => (
              <tr key={`empty-${i}`} className="border-t border-slate-200">
                <td className="py-2" colSpan={4}>
                  &nbsp;
                </td>
              </tr>
            ),
          )}
        </tbody>
      </table>
    </Panel>
  )
}

function WeaponRow({
  weapon,
  strMod,
  dexMod,
  pb,
}: {
  weapon: Item
  strMod: number
  dexMod: number
  pb: number
}) {
  const props = (weapon.properties as string[] | undefined) ?? []
  const damage = (weapon.damage as
    | { dice?: string; damage_type?: string; ability?: string }
    | undefined) ?? {}
  const dice = damage.dice ?? '—'
  const damageType = damage.damage_type ?? (weapon.damage_type as string | undefined) ?? ''
  const versatile =
    (weapon.versatile_damage as string | undefined) ?? (weapon.versatile as string | undefined)
  const mastery = weapon.mastery as string | undefined

  const isFinesse = props.includes('finesse')
  const isRanged = weapon.type === 'ranged' || weapon.category === 'ranged'
  const abilityMod = isRanged || isFinesse ? Math.max(strMod, dexMod) : strMod
  const attackBonus = abilityMod + pb

  return (
    <tr className="border-t border-slate-200">
      <td className="py-1.5 font-medium text-slate-900">{weapon.name}</td>
      <td className="py-1.5 text-center tabular-nums">{signed(attackBonus)}</td>
      <td className="py-1.5 tabular-nums text-slate-700">
        {dice}
        {versatile && ` (${versatile})`}
        {damageType && ` / ${damageType}`}
      </td>
      <td className="py-1.5 text-slate-700">
        {[mastery, `Dmg mod. ${signed(abilityMod)}`].filter(Boolean).join(' · ')}
      </td>
    </tr>
  )
}

/** CLASS FEATURES list panel; renders class-source features only. */
export function ClassFeatures({ character }: { character: Character }) {
  const { showToast } = useToast()
  const features = character.features.filter((f) => f.source === 'class')

  const useFeatureMutation = useCharacterMutation(character.id, (featureId: string) =>
    characterApi.useFeature(character.id, featureId),
  )
  const choiceMutation = useCharacterMutation(
    character.id,
    ({ featureId, value }: { featureId: string; value: string }) =>
      characterApi.setChoice(character.id, featureId, value),
  )

  return (
    <Panel
      title="Class Features"
      right={
        <span className="text-[9px] uppercase tracking-wider text-slate-500">
          ● Action &nbsp; ▲ Bonus &nbsp; ◆ Reaction &nbsp; ■ Limited
        </span>
      }
    >
      <ul className="divide-y divide-slate-200">
        {features.map((f) => (
          <FeatureLine
            key={f.id}
            feature={f}
            onUse={() =>
              useFeatureMutation.mutate(f.id, {
                onError: (err) => showToast(errorMessage(err)),
              })
            }
            onChoose={(value) =>
              choiceMutation.mutate(
                { featureId: f.id, value },
                { onError: (err) => showToast(errorMessage(err)) },
              )
            }
          />
        ))}
        {features.length === 0 && (
          <li className="py-2 text-xs text-slate-500">No class features yet.</li>
        )}
      </ul>
    </Panel>
  )
}

function FeatureLine({
  feature,
  onUse,
  onChoose,
}: {
  feature: Feature
  onUse: () => void
  onChoose: (value: string) => void
}) {
  const unlocked = feature.unlocked ?? true
  const isFightingStyle = feature.choice?.source === 'fighting_styles'
  const fightingStylesQuery = useQuery({
    queryKey: ['catalog', 'fighting-styles'],
    queryFn: catalogApi.fightingStyles,
    enabled: feature.kind === 'choice' && isFightingStyle,
  })
  const glyph = activationGlyph(feature.activation)

  return (
    <li className={`py-1.5 ${unlocked ? '' : 'opacity-50'}`}>
      <details>
        <summary className="flex cursor-pointer items-center gap-2 text-sm">
          {glyph && <span aria-hidden className="w-3 text-center">{glyph}</span>}
          <span className="font-medium text-slate-900">{feature.name}</span>
          {feature.kind === 'active' && (
            <span className="ml-auto rounded-sm border border-slate-400 px-1.5 py-0.5 text-[10px] tabular-nums text-slate-700">
              {feature.remaining_use ?? 0}/{feature.max_use ?? 0}
            </span>
          )}
          {!unlocked && (
            <span className="ml-auto text-[10px] text-slate-500">
              Unlocks lvl {feature.unlock_level}
            </span>
          )}
        </summary>
        <div className="prose prose-sm mt-1 max-w-none pl-5 text-slate-700">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{feature.desc}</ReactMarkdown>
        </div>
        {unlocked && feature.kind === 'active' && (
          <div className="pl-5 pt-1">
            <button
              type="button"
              disabled={(feature.remaining_use ?? 0) <= 0}
              onClick={onUse}
              className="rounded-sm border border-slate-800 bg-white px-2 py-0.5 text-[10px] font-semibold uppercase text-slate-700 hover:bg-slate-100 disabled:opacity-50"
            >
              Use
            </button>
          </div>
        )}
        {unlocked && feature.kind === 'choice' && (
          <div className="flex items-center gap-2 pl-5 pt-1 text-xs">
            <span className="text-slate-500">
              {feature.chosen_value ? `Chosen: ${feature.chosen_value}` : 'Not chosen'}
            </span>
            {isFightingStyle && (
              <select
                value={feature.chosen_value ?? ''}
                onChange={(e) => onChoose(e.target.value)}
                className="rounded-sm border border-slate-400 px-1 py-0.5 text-xs"
              >
                <option value="" disabled>
                  Choose…
                </option>
                {fightingStylesQuery.data?.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            )}
          </div>
        )}
      </details>
    </li>
  )
}

/** SPECIES TRAITS and FEATS boxes, rendered as a side-by-side pair. */
export function SpeciesAndFeats({ character }: { character: Character }) {
  const groups = useMemo(() => {
    const race: Feature[] = []
    const feats: Feature[] = []
    const background: Feature[] = []
    for (const f of character.features) {
      if (f.source === 'race') race.push(f)
      else if (f.source === 'feat') feats.push(f)
      else if (f.source === 'background') background.push(f)
    }
    return { race, feats, background }
  }, [character.features])

  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Panel title="Species Traits">
        <FeatureNameList features={groups.race} emptyText="No species traits." />
      </Panel>
      <Panel title="Feats">
        <FeatureNameList
          features={[...groups.feats, ...groups.background]}
          emptyText="No feats or background features."
        />
      </Panel>
    </div>
  )
}

function FeatureNameList({ features, emptyText }: { features: Feature[]; emptyText: string }) {
  if (features.length === 0) return <p className="text-xs text-slate-500">{emptyText}</p>
  return (
    <ul className="space-y-1">
      {features.map((f) => (
        <li key={f.id} className="text-sm">
          <details>
            <summary className="cursor-pointer">
              <span className="font-medium text-slate-900">{f.name}</span>
              {f.max_use !== undefined && (
                <span className="ml-2 rounded-sm border border-slate-400 px-1.5 py-0.5 text-[10px] tabular-nums">
                  {f.remaining_use ?? 0}/{f.max_use}
                </span>
              )}
            </summary>
            <div className="prose prose-sm mt-1 max-w-none pl-4 text-slate-700">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{f.desc}</ReactMarkdown>
            </div>
          </details>
        </li>
      ))}
    </ul>
  )
}
