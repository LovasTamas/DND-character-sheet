import { useNavigate, useParams } from 'react-router-dom'
import { useCharacterQuery } from '../hooks/useCharacter'
import { Header } from '../components/Header'
import { Vitals } from '../components/Vitals'
import { Abilities } from '../components/Abilities'
import { Skills } from '../components/Skills'
import { Features } from '../components/Features'
import { Inventory } from '../components/Inventory'
import { Proficiencies } from '../components/Proficiencies'

export function Sheet() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: character, isLoading, isError } = useCharacterQuery(id ?? '')

  if (!id) {
    return null
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <p className="text-slate-500">Loading character…</p>
      </div>
    )
  }

  if (isError || !character) {
    return (
      <div className="mx-auto max-w-5xl px-4 py-8">
        <p className="text-red-700">Failed to load this character.</p>
        <button
          type="button"
          onClick={() => navigate('/')}
          className="mt-4 rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-50"
        >
          Back to characters
        </button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl space-y-4 px-4 py-6">
      <button
        type="button"
        onClick={() => navigate('/')}
        className="text-sm font-medium text-indigo-700 hover:underline"
      >
        ← Characters
      </button>

      <Header character={character} />
      <Vitals character={character} />

      <div className="grid gap-4 lg:grid-cols-2">
        <Abilities character={character} />
        <Skills character={character} />
      </div>

      <Features character={character} />
      <Inventory character={character} />
      <Proficiencies character={character} />
    </div>
  )
}
