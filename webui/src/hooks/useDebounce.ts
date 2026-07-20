import { useEffect, useRef, useState } from 'react'

/**
 * Returns a debounced version of `value` that only updates 500ms (default)
 * after the input has stopped changing. Used for text inputs per the
 * vision's "debounce 500ms text" rule.
 */
export function useDebouncedValue<T>(value: T, delayMs = 500): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(timer)
  }, [value, delayMs])

  return debounced
}

/**
 * Local-optimistic text field: keeps a local draft, calls `onCommit` after
 * debounce, and syncs back to `serverValue` when it changes externally
 * (e.g. after a mutation round-trip or a reverted error).
 */
export function useDebouncedField(
  serverValue: string,
  onCommit: (value: string) => void,
  delayMs = 500,
) {
  const [draft, setDraft] = useState(serverValue)
  const lastCommitted = useRef(serverValue)
  const debounced = useDebouncedValue(draft, delayMs)

  useEffect(() => {
    setDraft(serverValue)
    lastCommitted.current = serverValue
  }, [serverValue])

  useEffect(() => {
    if (debounced !== lastCommitted.current) {
      lastCommitted.current = debounced
      onCommit(debounced)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounced])

  return [draft, setDraft] as const
}
