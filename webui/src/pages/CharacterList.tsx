import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { characterApi } from '../api/characters'
import { CreationWizard } from '../components/CreationWizard'
import { ConfirmDialog } from '../components/common'
import { useToast } from '../components/Toast'

export function CharacterList() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { showToast } = useToast()
  const [wizardOpen, setWizardOpen] = useState(false)
  const [pendingDelete, setPendingDelete] = useState<{ id: string; name: string } | null>(null)

  const { data: characters, isLoading, isError } = useQuery({
    queryKey: ['characters'],
    queryFn: characterApi.list,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => characterApi.remove(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['characters'] })
    },
    onError: () => {
      showToast('Failed to delete the character.')
    },
  })

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Characters</h1>
        <button
          type="button"
          onClick={() => setWizardOpen(true)}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          New character
        </button>
      </div>

      {isLoading && <p className="text-slate-500">Loading…</p>}
      {isError && <p className="text-red-700">Failed to load characters.</p>}
      {!isLoading && !isError && characters && characters.length === 0 && (
        <p className="text-slate-500">No characters yet. Create one to get started.</p>
      )}

      <ul className="space-y-2">
        {characters?.map((c) => (
          <li
            key={c.id}
            className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm"
          >
            <div>
              <p className="font-medium text-slate-900">{c.name}</p>
              <p className="text-sm text-slate-500">
                Level {c.level} {c.class_name}
                {c.race_name ? ` · ${c.race_name}` : ''}
                {c.background_name ? ` · ${c.background_name}` : ''}
              </p>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => navigate(`/character/${c.id}`)}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Open
              </button>
              <button
                type="button"
                onClick={() => setPendingDelete({ id: c.id, name: c.name })}
                className="rounded-md border border-red-300 px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50"
              >
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>

      {wizardOpen && (
        <CreationWizard
          onClose={() => setWizardOpen(false)}
          onCreated={(id) => {
            setWizardOpen(false)
            queryClient.invalidateQueries({ queryKey: ['characters'] })
            navigate(`/character/${id}`)
          }}
        />
      )}

      {pendingDelete && (
        <ConfirmDialog
          title="Delete character"
          message={`Delete "${pendingDelete.name}"? This cannot be undone.`}
          confirmLabel="Delete"
          onCancel={() => setPendingDelete(null)}
          onConfirm={() => {
            deleteMutation.mutate(pendingDelete.id)
            setPendingDelete(null)
          }}
        />
      )}
    </div>
  )
}
