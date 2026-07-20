import { useEffect, useState } from 'react'
import { characterApi } from '../api/characters'
import { useCharacterMutation } from '../hooks/useCharacter'
import type { Character } from '../types'
import { ErrorText, errorMessage } from './common'
import { useToast } from './Toast'
import { FieldCaption, Panel } from './sheet'

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value))
}

/**
 * Combat-action strip: edit current/temp HP, apply damage/heal, spend a
 * hit die and take short/long rests. Split out of the old Vitals block
 * so the numeric readouts can live in the header while the interactive
 * controls sit in a compact panel underneath the sheet body.
 */
export function HpActions({ character }: { character: Character }) {
  const { showToast } = useToast()
  const { vitals } = character
  const [hpDraft, setHpDraft] = useState(vitals.current_hp)
  const [tempDraft, setTempDraft] = useState(vitals.temporary_hp)
  const [damageAmount, setDamageAmount] = useState(0)
  const [healAmount, setHealAmount] = useState(0)
  const [hpError, setHpError] = useState<string | null>(null)
  const [tempError, setTempError] = useState<string | null>(null)

  useEffect(() => setHpDraft(vitals.current_hp), [vitals.current_hp])
  useEffect(() => setTempDraft(vitals.temporary_hp), [vitals.temporary_hp])

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

  const num =
    'w-16 rounded-sm border border-slate-400 px-2 py-0.5 text-center text-sm tabular-nums focus:border-slate-900 focus:outline-none'
  const btn =
    'rounded-sm border border-slate-800 bg-white px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-slate-700 hover:bg-slate-100'
  const btnDark =
    'rounded-sm border border-slate-800 bg-slate-800 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white hover:bg-slate-700'

  return (
    <Panel title="Combat Actions" contentClassName="flex flex-wrap items-end gap-4">
      <label className="block">
        <FieldCaption>Current HP</FieldCaption>
        <input
          type="number"
          value={hpDraft}
          onChange={(e) => setHpDraft(Number(e.target.value))}
          onBlur={(e) => commitHp(Number(e.target.value))}
          className={num}
        />
        <ErrorText message={hpError} />
      </label>
      <label className="block">
        <FieldCaption>Temp HP</FieldCaption>
        <input
          type="number"
          value={tempDraft}
          onChange={(e) => setTempDraft(Number(e.target.value))}
          onBlur={(e) => commitTempHp(Number(e.target.value))}
          className={num}
        />
        <ErrorText message={tempError} />
      </label>

      <div>
        <FieldCaption>Damage</FieldCaption>
        <div className="mt-0.5 flex gap-1">
          <input
            type="number"
            min={0}
            value={damageAmount}
            onChange={(e) => setDamageAmount(Number(e.target.value))}
            className={num}
          />
          <button
            type="button"
            className={btn}
            onClick={() =>
              damageMutation.mutate(damageAmount, {
                onError: (err) => showToast(errorMessage(err)),
              })
            }
          >
            Apply
          </button>
        </div>
      </div>

      <div>
        <FieldCaption>Heal</FieldCaption>
        <div className="mt-0.5 flex gap-1">
          <input
            type="number"
            min={0}
            value={healAmount}
            onChange={(e) => setHealAmount(Number(e.target.value))}
            className={num}
          />
          <button
            type="button"
            className={btn}
            onClick={() =>
              healMutation.mutate(healAmount, {
                onError: (err) => showToast(errorMessage(err)),
              })
            }
          >
            Apply
          </button>
        </div>
      </div>

      <div>
        <FieldCaption>
          Hit dice {vitals.hit_die}: {vitals.hit_dice_remaining}/{vitals.hit_dice_total}
        </FieldCaption>
        <button
          type="button"
          disabled={vitals.hit_dice_remaining <= 0}
          onClick={handleSpendHitDie}
          className={`${btn} mt-0.5 disabled:cursor-not-allowed disabled:opacity-50`}
        >
          Spend die
        </button>
      </div>

      <div className="ml-auto flex gap-2">
        <button type="button" className={btnDark} onClick={() => restShortMutation.mutate(undefined)}>
          Short rest
        </button>
        <button type="button" className={btnDark} onClick={() => restLongMutation.mutate(undefined)}>
          Long rest
        </button>
      </div>
    </Panel>
  )
}
