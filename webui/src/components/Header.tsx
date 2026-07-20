import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { catalogApi } from '../api/catalog'
import { characterApi } from '../api/characters'
import { useCharacterMutation } from '../hooks/useCharacter'
import { useDebouncedField } from '../hooks/useDebounce'
import type { Character } from '../types'
import { ConfirmDialog, ErrorText, errorMessage } from './common'
import { useToast } from './Toast'
import { FieldCaption, PanelTitle } from './sheet'

/**
 * Segmented top strip mimicking the printed sheet header:
 *   [ identity block (name, class, subclass, background, species) ] [ LEVEL ] [ AC ] [ HP ] [ HIT DICE ] [ DEATH SAVES ]
 *
 * XP and death-save checkboxes are visual only: they aren't part of the
 * Character contract yet, but including them keeps the sheet layout
 * faithful to the PDF and gives us the right amount of space.
 */
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

  function confirmClassChange() {
    if (!confirmClass) return
    setClassError(null)
    classMutation.mutate(confirmClass, { onError: (err) => setClassError(errorMessage(err)) })
    setConfirmClass(null)
  }

  function confirmRaceChange() {
    setRaceError(null)
    const value = confirmRace === '' ? null : confirmRace
    raceMutation.mutate(value, { onError: (err) => setRaceError(errorMessage(err)) })
    setConfirmRace(null)
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

  const { vitals } = character

  const inputCls =
    'w-full border-0 border-b border-slate-400 bg-transparent px-1 py-0.5 text-sm focus:border-slate-900 focus:outline-none focus:ring-0'

  return (
    <section className="rounded-sm border border-slate-800 bg-white">
      <div className="grid grid-cols-1 gap-0 lg:grid-cols-[minmax(0,1fr)_auto]">
        {/* Identity block: name + two rows of dropdowns */}
        <div className="grid grid-cols-1 gap-2 p-3 sm:grid-cols-2">
          <label className="col-span-2 block">
            <input
              type="text"
              value={nameDraft}
              onChange={(e) => setNameDraft(e.target.value)}
              placeholder="Character name"
              className="w-full border-0 border-b border-slate-400 bg-transparent px-1 py-1 text-xl font-bold text-slate-900 focus:border-slate-900 focus:outline-none"
            />
            <FieldCaption>Name</FieldCaption>
            <ErrorText message={nameError} />
          </label>

          <label className="block">
            <select
              value={character.background?.name ?? ''}
              onChange={(e) =>
                backgroundMutation.mutate(e.target.value === '' ? null : e.target.value, {
                  onError: (err) => setBackgroundError(errorMessage(err)),
                })
              }
              className={inputCls}
            >
              <option value="">None</option>
              {backgroundsQuery.data?.map((b) => (
                <option key={b.id} value={b.name}>
                  {b.name}
                </option>
              ))}
            </select>
            <FieldCaption>Background</FieldCaption>
            <ErrorText message={backgroundError} />
          </label>

          <label className="block">
            <select
              value={character.class.name}
              onChange={(e) => setConfirmClass(e.target.value)}
              className={inputCls}
            >
              {classesQuery.data?.map((c) => (
                <option key={c.id} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
            <FieldCaption>Class</FieldCaption>
            <ErrorText message={classError} />
          </label>

          <label className="block">
            <select
              value={character.race?.name ?? ''}
              onChange={(e) => setConfirmRace(e.target.value)}
              className={inputCls}
            >
              <option value="">None</option>
              {racesQuery.data?.map((r) => (
                <option key={r.id} value={r.name}>
                  {r.name}
                </option>
              ))}
            </select>
            <FieldCaption>Species</FieldCaption>
            <ErrorText message={raceError} />
          </label>

          <label
            className="block"
            title={subclassLocked ? `Unlocks at level ${character.subclass_unlock_level}` : undefined}
          >
            <select
              value={character.subclass.id ?? ''}
              disabled={subclassLocked}
              onChange={(e) =>
                subclassMutation.mutate(e.target.value === '' ? null : e.target.value, {
                  onError: (err) => setSubclassError(errorMessage(err)),
                })
              }
              className={`${inputCls} disabled:text-slate-400`}
            >
              <option value="">None</option>
              {(subclassesQuery.data ?? character.subclass_options)?.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
            <FieldCaption>
              Subclass{subclassLocked && ` (unlocks lvl ${character.subclass_unlock_level})`}
            </FieldCaption>
            <ErrorText message={subclassError} />
          </label>
        </div>

        {/* Stats strip on the right: LEVEL | AC | HP | HIT DICE | DEATH SAVES */}
        <div className="grid grid-cols-5 divide-x divide-slate-800 border-t border-slate-800 lg:border-l lg:border-t-0">
          <MiniStat title="Level">
            <input
              type="number"
              min={1}
              max={20}
              value={character.level}
              onChange={(e) => handleLevelChange(Number(e.target.value))}
              className="w-full border-0 bg-transparent text-center text-2xl font-bold tabular-nums text-slate-900 focus:outline-none"
            />
            <div className="mt-1 border-t border-slate-300 pt-1 text-center text-[10px] uppercase tracking-widest text-slate-500">
              XP
            </div>
            <div className="text-center text-xs text-slate-400">—</div>
            <ErrorText message={levelError} />
          </MiniStat>

          <MiniStat title="AC">
            <div className="flex h-full flex-col items-center justify-center">
              <span className="text-3xl font-bold tabular-nums text-slate-900">{vitals.ac}</span>
              <div className="mt-1 flex items-center gap-1 border-t border-slate-300 pt-1 text-[10px] uppercase tracking-widest text-slate-500">
                <input type="checkbox" checked={!!character.equipped_shield} readOnly className="h-3 w-3" /> Shield
              </div>
            </div>
          </MiniStat>

          <MiniStat title="Hit Points">
            <div className="grid grid-cols-2 gap-x-2 text-center">
              <div>
                <div className="text-2xl font-bold tabular-nums text-slate-900">{vitals.current_hp}</div>
                <FieldCaption>Current</FieldCaption>
              </div>
              <div>
                <div className="text-2xl font-bold tabular-nums text-slate-900">{vitals.max_hp}</div>
                <FieldCaption>Max</FieldCaption>
              </div>
              <div className="col-span-2 mt-1 border-t border-slate-300 pt-1">
                <span className="text-sm font-semibold tabular-nums">{vitals.temporary_hp}</span>
                <FieldCaption className="inline pl-2">Temp</FieldCaption>
              </div>
            </div>
          </MiniStat>

          <MiniStat title={`Hit Dice (${vitals.hit_die})`}>
            <div className="grid grid-cols-2 gap-x-2 text-center">
              <div>
                <div className="text-2xl font-bold tabular-nums text-slate-900">
                  {vitals.hit_dice_total - vitals.hit_dice_remaining}
                </div>
                <FieldCaption>Spent</FieldCaption>
              </div>
              <div>
                <div className="text-2xl font-bold tabular-nums text-slate-900">
                  {vitals.hit_dice_total}
                </div>
                <FieldCaption>Max</FieldCaption>
              </div>
            </div>
          </MiniStat>

          <MiniStat title="Death Saves">
            <div className="flex flex-col justify-center gap-1">
              <DeathSaveRow label="Success" />
              <DeathSaveRow label="Failure" />
            </div>
          </MiniStat>
        </div>
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

function MiniStat({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="flex min-w-[110px] flex-col">
      <div className="border-b border-slate-800 bg-slate-50 px-2 py-1 text-center">
        <PanelTitle>{title}</PanelTitle>
      </div>
      <div className="flex-1 px-2 py-2">{children}</div>
    </div>
  )
}

function DeathSaveRow({ label }: { label: string }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <input
            key={i}
            type="checkbox"
            aria-label={`${label} ${i + 1}`}
            className="h-3 w-3 border border-slate-500"
          />
        ))}
      </div>
      <FieldCaption>{label}</FieldCaption>
    </div>
  )
}
