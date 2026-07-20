import { useIsFetching, useIsMutating } from '@tanstack/react-query'

/** Subtle top-bar spinner, shown while any request is in flight (vision "Loading state"). */
export function TopBarSpinner() {
  const isFetching = useIsFetching()
  const isMutating = useIsMutating()
  const active = isFetching > 0 || isMutating > 0

  return (
    <div className="fixed left-0 right-0 top-0 z-50 h-0.5">
      {active && (
        <div className="h-full w-full origin-left animate-pulse bg-indigo-500" />
      )}
    </div>
  )
}
