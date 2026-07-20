import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { catalogApi } from '../api/catalog'
import { characterApi } from '../api/characters'
import { useCharacterMutation } from '../hooks/useCharacter'
import type { Character, Feature } from '../types'
import { errorMessage } from './common'
import { useToast } from './Toast'

const GROUP_LABELS: Record<string, string> = {
  class: 'Class',
  race: 'Race / Species',
  background: 'Background',
  feat: 'Feats',
}

const KIND_BADGE_STYLE: Record<Feature['kind'], string> = {
  passive: 'bg-slate-100 text-slate-600 border-slate-300',
  active: 'bg-amber-50 text-amber-700 border-amber-300',
  choice: 'bg-indigo-50 text-indigo-700 border-indigo-300',
}

export function Features({ character }: { character: Character }) {
  const { showToast } = useToast()
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({})

  const groups = useMemo(() => {
    const map = new Map<string, Feature[]>()
    for (const feature of character.features) {
      const key = feature.source || 'other'
      if (!map.has(key)) map.set(key, [])
      map.get(key)!.push(feature)
    }
    return map
  }, [character.features])

  const useFeatureMutation = useCharacterMutation(character.id, (featureId: string) =>
    characterApi.useFeature(character.id, featureId),
  )
  const choiceMutation = useCharacterMutation(
    character.id,
    ({ featureId, value }: { featureId: string; value: string }) =>
      characterApi.setChoice(character.id, featureId, value),
  )

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
        Features
      </h2>
      <div className="space-y-3">
        {[...groups.entries()].map(([source, features]) => {
          const isCollapsed = collapsed[source] ?? false
          return (
            <div key={source} className="rounded-md border border-slate-200">
              <button
                type="button"
                onClick={() =>
                  setCollapsed((prev) => ({ ...prev, [source]: !isCollapsed }))
                }
                className="flex w-full items-center justify-between px-3 py-2 text-left text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                <span>{GROUP_LABELS[source] ?? source}</span>
                <span aria-hidden>{isCollapsed ? '▸' : '▾'}</span>
              </button>
              {!isCollapsed && (
                <ul className="divide-y divide-slate-100 px-3 pb-2">
                  {features.map((feature) => (
                    <li key={feature.id} className="py-3">
                      <FeatureRow
                        feature={feature}
                        characterId={character.id}
                        onUse={() =>
                          useFeatureMutation.mutate(feature.id, {
                            onError: (err) => showToast(errorMessage(err)),
                          })
                        }
                        onChoose={(value) =>
                          choiceMutation.mutate(
                            { featureId: feature.id, value },
                            { onError: (err) => showToast(errorMessage(err)) },
                          )
                        }
                      />
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )
        })}
        {character.features.length === 0 && (
          <p className="text-sm text-slate-500">No features yet.</p>
        )}
      </div>
    </section>
  )
}

function FeatureRow({
  feature,
  onUse,
  onChoose,
}: {
  feature: Feature
  characterId: string
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

  return (
    <div className={unlocked ? '' : 'opacity-50'}>
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-medium text-slate-900">{feature.name}</span>
        <span
          className={`rounded-full border px-1.5 py-0.5 text-[10px] font-medium uppercase ${KIND_BADGE_STYLE[feature.kind]}`}
        >
          {feature.kind}
        </span>
        {!unlocked && (
          <span className="text-xs text-slate-500">
            Unlocks at level {feature.unlock_level}
          </span>
        )}
        {feature.kind === 'active' && (
          <span className="rounded-full border border-slate-300 bg-slate-50 px-2 py-0.5 text-xs tabular-nums text-slate-700">
            {feature.remaining_use ?? 0}/{feature.max_use ?? 0}
          </span>
        )}
      </div>

      <div className="prose prose-sm mt-1 max-w-none text-slate-600">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{feature.desc}</ReactMarkdown>
      </div>

      {unlocked && feature.kind === 'active' && (
        <button
          type="button"
          disabled={(feature.remaining_use ?? 0) <= 0}
          onClick={onUse}
          className="mt-2 rounded-md border border-slate-300 px-3 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          Use
        </button>
      )}

      {unlocked && feature.kind === 'choice' && (
        <div className="mt-2 flex items-center gap-2">
          <span className="text-xs text-slate-500">
            {feature.chosen_value ? `Chosen: ${feature.chosen_value}` : 'Not chosen'}
          </span>
          {isFightingStyle && (
            <select
              value={feature.chosen_value ?? ''}
              onChange={(e) => onChoose(e.target.value)}
              className="rounded-md border border-slate-300 px-2 py-1 text-xs"
            >
              <option value="" disabled>
                Choose…
              </option>
              {fightingStylesQuery.data?.map((style) => (
                <option key={style.id} value={style.id}>
                  {style.name}
                </option>
              ))}
            </select>
          )}
        </div>
      )}
    </div>
  )
}
