import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { catalogApi } from '../api/catalog'
import { characterApi } from '../api/characters'
import { ABILITIES, ABILITY_ABBR } from '../types'
import type { Ability } from '../types'
import { Modal } from './common'
import { errorMessage } from './common'

interface CreationWizardProps {
  onClose: () => void
  onCreated: (characterId: string) => void
}

const DEFAULT_SCORES: Record<Ability, number> = {
  strength: 10,
  dexterity: 10,
  constitution: 10,
  intelligence: 10,
  wisdom: 10,
  charisma: 10,
}

export function CreationWizard({ onClose, onCreated }: CreationWizardProps) {
  const [name, setName] = useState('')
  const [className, setClassName] = useState('')
  const [raceName, setRaceName] = useState('')
  const [backgroundName, setBackgroundName] = useState('')
  const [scores, setScores] = useState<Record<Ability, number>>(DEFAULT_SCORES)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const classesQuery = useQuery({ queryKey: ['catalog', 'classes'], queryFn: catalogApi.classes })
  const racesQuery = useQuery({ queryKey: ['catalog', 'races'], queryFn: catalogApi.races })
  const backgroundsQuery = useQuery({
    queryKey: ['catalog', 'backgrounds'],
    queryFn: catalogApi.backgrounds,
  })

  useEffect(() => {
    if (!className && classesQuery.data && classesQuery.data.length > 0) {
      setClassName(classesQuery.data[0].name)
    }
  }, [classesQuery.data, className])

  const canSubmit = useMemo(() => name.trim().length > 0 && className.length > 0, [name, className])

  async function handleSubmit() {
    if (!canSubmit) return
    setSubmitting(true)
    setSubmitError(null)
    try {
      const character = await characterApi.create({
        name: name.trim(),
        class_name: className,
        race_name: raceName || undefined,
        background_name: backgroundName || undefined,
      })
      // Ability scores + background ASI are follow-up mutations against the
      // freshly created character, since POST /characters only takes the
      // mandatory picks. Backend defaults ability scores to 0, so we always
      // send the wizard's values (including the default 10).
      for (const ability of ABILITIES) {
        await characterApi.setAbility(character.id, ability, scores[ability])
      }
      onCreated(character.id)
    } catch (err) {
      setSubmitError(errorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal title="New character" onClose={onClose}>
      <div className="space-y-4">
        <label className="block">
          <span className="text-sm font-medium text-slate-700">Name</span>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm"
            placeholder="Character name"
          />
        </label>

        <label className="block">
          <span className="text-sm font-medium text-slate-700">Class</span>
          <select
            value={className}
            onChange={(e) => setClassName(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm"
          >
            <option value="" disabled>
              Select a class…
            </option>
            {classesQuery.data?.map((c) => (
              <option key={c.id} value={c.name}>
                {c.name}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-sm font-medium text-slate-700">Race</span>
          <select
            value={raceName}
            onChange={(e) => setRaceName(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm"
          >
            <option value="">None</option>
            {racesQuery.data?.map((r) => (
              <option key={r.id} value={r.name}>
                {r.name}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-sm font-medium text-slate-700">Background</span>
          <select
            value={backgroundName}
            onChange={(e) => setBackgroundName(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm"
          >
            <option value="">None</option>
            {backgroundsQuery.data?.map((b) => (
              <option key={b.id} value={b.name}>
                {b.name}
              </option>
            ))}
          </select>
        </label>

        <div>
          <span className="text-sm font-medium text-slate-700">Ability scores</span>
          <div className="mt-1 grid grid-cols-3 gap-2 sm:grid-cols-6">
            {ABILITIES.map((ability) => (
              <label key={ability} className="block text-center">
                <span className="block text-xs text-slate-500">{ABILITY_ABBR[ability]}</span>
                <input
                  type="number"
                  min={3}
                  max={20}
                  value={scores[ability]}
                  onChange={(e) =>
                    setScores((prev) => ({ ...prev, [ability]: Number(e.target.value) }))
                  }
                  className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1 text-center text-sm tabular-nums"
                />
              </label>
            ))}
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Background ability bonuses and class skill picks can be set on the sheet after
            creation.
          </p>
        </div>

        {submitError && <p className="text-sm font-medium text-red-700">{submitError}</p>}

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!canSubmit || submitting}
            onClick={handleSubmit}
            className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {submitting ? 'Creating…' : 'Create character'}
          </button>
        </div>
      </div>
    </Modal>
  )
}
