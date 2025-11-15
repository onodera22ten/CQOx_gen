import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import Layout from './components/Layout'
import DecisionConsole from './pages/DecisionConsole'
import PolicyLab from './pages/PolicyLab'
import CausalDesign from './pages/CausalDesign'
import Portfolio from './pages/Portfolio'
import Diagnostics from './pages/Diagnostics'
import { Login } from './pages/Login'
import { OAuthCallback } from './pages/OAuthCallback'

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/auth/callback/:provider" element={<OAuthCallback />} />

          {/* Protected routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<DecisionConsole />} />
            <Route path="console" element={<DecisionConsole />} />

            {/* Policy Lab - requires models:write permission */}
            <Route path="policy" element={
              <ProtectedRoute requiredPermission="models:write">
                <PolicyLab />
              </ProtectedRoute>
            } />

            {/* Causal Design - requires models:read permission */}
            <Route path="causal" element={
              <ProtectedRoute requiredPermission="models:read">
                <CausalDesign />
              </ProtectedRoute>
            } />

            {/* Portfolio - requires policies:read permission */}
            <Route path="portfolio" element={
              <ProtectedRoute requiredPermission="policies:read">
                <Portfolio />
              </ProtectedRoute>
            } />

            {/* Diagnostics - requires diagnostics:read permission */}
            <Route path="diagnostics" element={
              <ProtectedRoute requiredPermission="diagnostics:read">
                <Diagnostics />
              </ProtectedRoute>
            } />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
