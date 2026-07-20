import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { catalogApi } from '../api/catalog'
import { characterApi } from '../api/characters'
import { useCharacterMutation } from '../hooks/useCharacter'
import { useDebouncedField } from '../hooks/useDebounce'
import type { Character } from '../types'
import { ConfirmDialog, ErrorText, errorMessage } from './common'
import { useToast } from './Toast'

export function Header({ character }: { character: Character }) {
  const { showToast } = useToast()
  const [nameError, setNameError] = useState<string | null>(null)
  const [classError, setClassError] = useState<string | null>(null)
  const [raceError, setRaceError] = useState<string | null>(null)
  const [subclassError, setSubclassError] = useState<string | null>(null)
  const [backgroundError, setBackgroundError] = useState<string | null>(null)
  const [levelError, setLevelError] = useState<string | null>(null)

  const [confirmClass, setConfirmClass] = useState<string | null>(null)
  const [confirmRace, setConfirmRace] = useState<string | null>(null)

  const classesQuery = useQuery({ queryKey: ['catalog', 'classes'], queryFn: catalogApi.classes })
  const racesQuery = useQuery({ queryKey: ['catalog', 'races'], queryFn: catalogApi.races })
  const backgroundsQuery = useQuery({
    queryKey: ['catalog', 'backgrounds'],
    queryFn: catalogApi.backgrounds,
  })
  const subclassesQuery = useQuery({
    queryKey: ['catalog', 'subclasses', character.class.id],
    queryFn: () => catalogApi.subclasses(character.class.id),
    enabled: !!character.class.id,
  })

  const nameMutation = useCharacterMutation(character.id, (name: string) =>
    characterApi.setName(character.id, name),
  )
  const classMutation = useCharacterMutation(character.id, (className: string) =>
    characterApi.setClass(character.id, className),
  )
  const raceMutation = useCharacterMutation(character.id, (raceName: string | null) =>
    characterApi.setRace(character.id, raceName),
  )
  const subclassMutation = useCharacterMutation(character.id, (subclassId: string | null) =>
    characterApi.setSubclass(character.id, subclassId),
  )
  const backgroundMutation = useCharacterMutation(
    character.id,
    (backgroundName: string | null) => characterApi.setBackground(character.id, backgroundName),
  )
  const levelMutation = useCharacterMutation(character.id, (level: number) =>
    characterApi.setLevel(character.id, level),
  )

  const [nameDraft, setNameDraft] = useDebouncedField(character.name, (value) => {
    setNameError(null)
    nameMutation.mutate(value, {
      onError: (err) => setNameError(errorMessage(err)),
    })
  })

  const subclassLocked = character.level < character.subclass_unlock_level

  function handleClassChange(className: string) {
    setConfirmClass(className)
  }

  function confirmClassChange() {
    if (!confirmClass) return
    setClassError(null)
    classMutation.mutate(confirmClass, {
      onError: (err) => setClassError(errorMessage(err)),
    })
    setConfirmClass(null)
  }

  function handleRaceChange(raceName: string) {
    setConfirmRace(raceName)
  }

  function confirmRaceChange() {
    setRaceError(null)
    const value = confirmRace === '' ? null : confirmRace
    raceMutation.mutate(value, {
      onError: (err) => setRaceError(errorMessage(err)),
    })
    setConfirmRace(null)
  }

  function handleSubclassChange(subclassId: string) {
    setSubclassError(null)
    subclassMutation.mutate(subclassId === '' ? null : subclassId, {
      onError: (err) => setSubclassError(errorMessage(err)),
    })
  }

  function handleBackgroundChange(backgroundName: string) {
    setBackgroundError(null)
    backgroundMutation.mutate(backgroundName === '' ? null : backgroundName, {
      onError: (err) => setBackgroundError(errorMessage(err)),
    })
  }

  function handleLevelChange(level: number) {
    if (level < 1 || level > 20) return
    setLevelError(null)
    levelMutation.mutate(level, {
      onError: (err) => {
        setLevelError(errorMessage(err))
        showToast(errorMessage(err))
      },
    })
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-end gap-4">
        <label className="min-w-[200px] flex-1">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Name
          </span>
          <input
            type="text"
            value={nameDraft}
            onChange={(e) => setNameDraft(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-lg font-semibold"
          />
          <ErrorText message={nameError} />
        </label>

        <label className="min-w-[140px]">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Class
          </span>
          <select
            value={character.class.name}
            onChange={(e) => handleClassChange(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm"
          >
            {classesQuery.data?.map((c) => (
              <option key={c.id} value={c.name}>
                {c.name}
              </option>
            ))}
          </select>
          <ErrorText message={classError} />
        </label>

        <label className="min-w-[140px]">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Species
          </span>
          <select
            value={character.race?.name ?? ''}
            onChange={(e) => handleRaceChange(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm"
          >
            <option value="">None</option>
            {racesQuery.data?.map((r) => (
              <option key={r.id} value={r.name}>
                {r.name}
              </option>
            ))}
          </select>
          <ErrorText message={raceError} />
        </label>

        <label
          className="min-w-[160px]"
          title={
            subclassLocked
              ? `Unlocks at level ${character.subclass_unlock_level}`
              : undefined
          }
        >
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Subclass
          </span>
          <select
            value={character.subclass.id ?? ''}
            disabled={subclassLocked}
            onChange={(e) => handleSubclassChange(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm disabled:bg-slate-100 disabled:text-slate-400"
          >
            <option value="">None</option>
            {(subclassesQuery.data ?? character.subclass_options)?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          {subclassLocked && (
            <p className="mt-1 text-xs text-slate-500">
              Unlocks at level {character.subclass_unlock_level}
            </p>
          )}
          <ErrorText message={subclassError} />
        </label>

        <label className="min-w-[160px]">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Background
          </span>
          <select
            value={character.background?.name ?? ''}
            onChange={(e) => handleBackgroundChange(e.target.value)}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm"
          >
            <option value="">None</option>
            {backgroundsQuery.data?.map((b) => (
              <option key={b.id} value={b.name}>
                {b.name}
              </option>
            ))}
          </select>
          <ErrorText message={backgroundError} />
        </label>

        <label className="w-24">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Level
          </span>
          <input
            type="number"
            min={1}
            max={20}
            value={character.level}
            onChange={(e) => handleLevelChange(Number(e.target.value))}
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-1.5 text-sm tabular-nums"
          />
          <ErrorText message={levelError} />
        </label>
      </div>

      {confirmClass !== null && (
        <ConfirmDialog
          title="Change class?"
          message="This will re-derive features and reset invalid choices."
          confirmLabel="Change class"
          onCancel={() => setConfirmClass(null)}
          onConfirm={confirmClassChange}
        />
      )}

      {confirmRace !== null && (
        <ConfirmDialog
          title="Change species?"
          message="This will rewrite species traits (size, speed, creature type)."
          confirmLabel="Change species"
          onCancel={() => setConfirmRace(null)}
          onConfirm={confirmRaceChange}
        />
      )}
    </section>
  )
}
