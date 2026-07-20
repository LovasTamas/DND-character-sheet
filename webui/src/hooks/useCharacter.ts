import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { characterApi } from '../api/characters'
import type { Character } from '../types'

export function characterQueryKey(id: string) {
  return ['character', id] as const
}

export function useCharacterQuery(id: string) {
  return useQuery({
    queryKey: characterQueryKey(id),
    queryFn: () => characterApi.get(id),
    enabled: !!id,
  })
}

/**
 * Generic wrapper for the "every mutation round-trips" rule: the mutation
 * function must resolve to the fresh Character body (or an object
 * containing one), which is written straight into the query cache instead
 * of triggering a separate refetch.
 */
export function useCharacterMutation<TVars>(
  id: string,
  mutationFn: (vars: TVars) => Promise<Character>,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: (character) => {
      queryClient.setQueryData(characterQueryKey(id), character)
    },
  })
}
