import { Route, Routes } from 'react-router-dom'
import { TopBarSpinner } from './components/TopBarSpinner'
import { CharacterList } from './pages/CharacterList'
import { Sheet } from './pages/Sheet'

function App() {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <TopBarSpinner />
      <Routes>
        <Route path="/" element={<CharacterList />} />
        <Route path="/character/:id" element={<Sheet />} />
      </Routes>
    </div>
  )
}

export default App
