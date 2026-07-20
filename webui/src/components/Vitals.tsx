import { useState } from 'react'
import { characterApi } from '../api/characters'
import { useCharacterMutation } from '../hooks/useCharacter'
import type { Character } from '../types'
import { ErrorText, errorMessage } from './common'
import { useToast } from './Toast'

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}

export function Vitals({ character }: { character: Character }) {
  const { showToast } = useToast()
  const { vitals } = character
  const [hpDraft, setHpDraft] = useState(vitals.current_hp)
  const [tempDraft, setTempDraft] = useState(vitals.temporary_hp)
  const [damageAmount, setDamageAmount] = useState(0)
  const [healAmount, setHealAmount] = useState(0)
  const [hpError, setHpError] = useState<string | null>(null)
  const [tempError, setTempError] = useState<string | null>(null)

  const hpMutation = useCharacterMutation(character.id, (value: number) =>
    characterApi.setHp(character.id, value),
  )
  const tempHpMutation = useCharacterMutation(character.id, (value: number) =>
    characterApi.setTemporaryHp(character.id, value),
  )
  const damageMutation = useCharacterMutation(character.id, (amount: number) =>
    characterApi.damage(character.id, amount),
  )
  const healMutation = useCharacterMutation(character.id, (amount: number) =>
    characterApi.heal(character.id, amount),
  )
  const spendHitDieMutation = useCharacterMutation(character.id, () =>
    characterApi.spendHitDie(character.id).then((res) => res.character),
  )
  const restShortMutation = useCharacterMutation(character.id, () =>
    characterApi.restShort(character.id),
  )
  const restLongMutation = useCharacterMutation(character.id, () =>
    characterApi.restLong(character.id),
  )

  function commitHp(value: number) {
    const clamped = clamp(value, 0, vitals.max_hp)
    setHpDraft(clamped)
    setHpError(null)
    hpMutation.mutate(clamped, {
      onError: (err) => {
        setHpDraft(vitals.current_hp)
        setHpError(errorMessage(err))
      },
    })
  }

  function commitTempHp(value: number) {
    setTempDraft(value)
    setTempError(null)
    tempHpMutation.mutate(value, {
      onError: (err) => {
        setTempDraft(vitals.temporary_hp)
        setTempError(errorMessage(err))
      },
    })
  }

  function handleSpendHitDie() {
    if (vitals.hit_dice_remaining <= 0) return
    spendHitDieMutation.mutate(undefined, {
      onSuccess: () => {
        const rolled = window.prompt(`Rolled amount to heal (${vitals.hit_die})?`, '0')
        const amount = Number(rolled)
        if (rolled !== null && !Number.isNaN(amount) && amount > 0) {
          healMutation.mutate(amount, { onError: (err) => showToast(errorMessage(err)) })
        }
      },
      onError: (err) => showToast(errorMessage(err)),
    })
  }

  const readout = (label: string, value: string | number) => (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="tabular-nums text-lg font-semibold text-slate-900">{value}</p>
    </div>
  )

  const signed = (n: number) => (n >= 0 ? `+${n}` : `${n}`)

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
        Vitals
      </h2>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 lg:grid-cols-6">
        <label className="block">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Current HP
          </span>
          <input
            type="number"
            value={hpDraft}
            onChange={(e) => setHpDraft(Number(e.target.value))}
            onBlur={(e) => commitHp(Number(e.target.value))}
            className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1 text-sm tabular-nums"
          />
          <ErrorText message={hpError} />
        </label>
        <label className="block">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Temp HP
          </span>
          <input
            type="number"
            value={tempDraft}
            onChange={(e) => setTempDraft(Number(e.target.value))}
            onBlur={(e) => commitTempHp(Number(e.target.value))}
            className="mt-1 w-full rounded-md border border-slate-300 px-2 py-1 text-sm tabular-nums"
          />
          <ErrorText message={tempError} />
        </label>
        {readout('Max HP', vitals.max_hp)}
        {readout('AC', vitals.ac)}
        {readout('Speed', `${vitals.speed} ft`)}
        {readout('Initiative', signed(vitals.initiative))}
        {readout('Prof. bonus', signed(vitals.proficiency_bonus))}
        {readout('Passive perception', vitals.passive_perception)}
        {readout('Size', vitals.size)}
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Hit dice</p>
          <p className="tabular-nums text-lg font-semibold text-slate-900">
            {vitals.hit_die} × {vitals.hit_dice_remaining}/{vitals.hit_dice_total}
          </p>
          <button
            type="button"
            disabled={vitals.hit_dice_remaining <= 0}
            onClick={handleSpendHitDie}
            className="mt-1 rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Spend
          </button>
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-end gap-4 border-t border-slate-100 pt-4">
        <label className="block">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Damage
          </span>
          <div className="mt-1 flex gap-1">
            <input
              type="number"
              min={0}
              value={damageAmount}
              onChange={(e) => setDamageAmount(Number(e.target.value))}
              className="w-20 rounded-md border border-slate-300 px-2 py-1 text-sm tabular-nums"
            />
            <button
              type="button"
              onClick={() =>
                damageMutation.mutate(damageAmount, {
                  onError: (err) => showToast(errorMessage(err)),
                })
              }
              className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium hover:bg-slate-50"
            >
              Apply
            </button>
          </div>
        </label>
        <label className="block">
          <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Heal
          </span>
          <div className="mt-1 flex gap-1">
            <input
              type="number"
              min={0}
              value={healAmount}
              onChange={(e) => setHealAmount(Number(e.target.value))}
              className="w-20 rounded-md border border-slate-300 px-2 py-1 text-sm tabular-nums"
            />
            <button
              type="button"
              onClick={() =>
                healMutation.mutate(healAmount, {
                  onError: (err) => showToast(errorMessage(err)),
                })
              }
              className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium hover:bg-slate-50"
            >
              Apply
            </button>
          </div>
        </label>
        <button
          type="button"
          onClick={() => restShortMutation.mutate(undefined)}
          className="rounded-md bg-slate-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
        >
          Short rest
        </button>
        <button
          type="button"
          onClick={() => restLongMutation.mutate(undefined)}
          className="rounded-md bg-slate-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
        >
          Long rest
        </button>
      </div>
    </section>
  )
}
