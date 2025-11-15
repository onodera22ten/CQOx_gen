import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import DecisionConsole from './pages/DecisionConsole'
import PolicyLab from './pages/PolicyLab'
import CausalDesign from './pages/CausalDesign'
import Portfolio from './pages/Portfolio'
import Diagnostics from './pages/Diagnostics'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DecisionConsole />} />
          <Route path="console" element={<DecisionConsole />} />
          <Route path="policy" element={<PolicyLab />} />
          <Route path="causal" element={<CausalDesign />} />
          <Route path="portfolio" element={<Portfolio />} />
          <Route path="diagnostics" element={<Diagnostics />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
