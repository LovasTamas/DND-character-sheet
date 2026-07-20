import type { ReactNode } from 'react'

/**
 * Visual primitives used across the character sheet to match the printed
 * D&D 2024 sheet look: monochrome outlined boxes with tiny uppercase
 * labels centered inside a thin header strip.
 */

export function Panel({
  title,
  children,
  className = '',
  contentClassName = '',
  right,
}: {
  title?: ReactNode
  children: ReactNode
  className?: string
  contentClassName?: string
  right?: ReactNode
}) {
  return (
    <section className={`rounded-sm border border-slate-800 bg-white ${className}`}>
      {title && (
        <header className="flex items-center justify-between border-b border-slate-800 bg-slate-50 px-2 py-1">
          <PanelTitle>{title}</PanelTitle>
          {right}
        </header>
      )}
      <div className={`px-2 py-2 ${contentClassName}`}>{children}</div>
    </section>
  )
}

export function PanelTitle({ children }: { children: ReactNode }) {
  return (
    <h3 className="w-full text-center text-[10px] font-bold uppercase tracking-[0.14em] text-slate-700">
      {children}
    </h3>
  )
}

/** Tiny uppercase caption sitting under a value, mimicking the sheet's field labels. */
export function FieldCaption({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={`block text-[9px] font-medium uppercase tracking-[0.12em] text-slate-500 ${className}`}
    >
      {children}
    </span>
  )
}

/** Numeric readout centered in a large bold face, e.g. an ability score or AC. */
export function BigNumber({
  value,
  className = '',
}: {
  value: ReactNode
  className?: string
}) {
  return (
    <span
      className={`block text-center tabular-nums text-3xl font-bold text-slate-900 leading-none ${className}`}
    >
      {value}
    </span>
  )
}

/** Bordered mini box, e.g. AC / HP compartments in the header. */
export function StatBox({
  title,
  children,
  className = '',
}: {
  title: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <div className={`flex flex-col rounded-sm border border-slate-800 bg-white ${className}`}>
      <div className="border-b border-slate-800 bg-slate-50 px-2 py-1 text-center">
        <PanelTitle>{title}</PanelTitle>
      </div>
      <div className="flex-1 px-2 py-2">{children}</div>
    </div>
  )
}

/** Proficiency marker: hollow / filled / expertise (double). Read-only or clickable. */
export function ProfDot({
  state,
  onClick,
  title,
  disabled,
}: {
  state: 'none' | 'proficient' | 'expertise'
  onClick?: () => void
  title?: string
  disabled?: boolean
}) {
  const glyph = state === 'expertise' ? '◙' : state === 'proficient' ? '●' : '○'
  const color = state === 'none' ? 'text-slate-400' : 'text-slate-900'
  const base =
    'inline-flex h-4 w-4 items-center justify-center text-xs leading-none tabular-nums'
  if (!onClick) {
    return (
      <span aria-hidden className={`${base} ${color}`} title={title}>
        {glyph}
      </span>
    )
  }
  return (
    <button
      type="button"
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      title={title}
      aria-label={title}
      className={`${base} ${color} hover:text-indigo-700 disabled:cursor-not-allowed disabled:opacity-50`}
    >
      {glyph}
    </button>
  )
}

export function signed(n: number) {
  return n >= 0 ? `+${n}` : `${n}`
}
