import { useState } from 'react'
import LandingPage from './components/LandingPage'
import LoadingSequence from './components/LoadingSequence'
import Dashboard from './components/Dashboard'

export default function App() {
  const [screen, setScreen] = useState('landing') // 'landing' | 'loading' | 'dashboard'

  return (
    <>
      {screen === 'landing'   && <LandingPage   onStart={() => setScreen('loading')} />}
      {screen === 'loading'   && <LoadingSequence onDone={() => setScreen('dashboard')} />}
      {screen === 'dashboard' && <Dashboard />}
    </>
  )
}