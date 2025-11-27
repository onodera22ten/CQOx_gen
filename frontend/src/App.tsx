import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { I18nProvider } from './contexts/I18nContext'
import { ProtectedRoute } from './components/ProtectedRoute'
import Layout from './components/Layout'
import DecisionConsole from './pages/DecisionConsole'
import PolicyLab from './pages/PolicyLab'
import CausalDesign from './pages/CausalDesign'
import Portfolio from './pages/Portfolio'
import Diagnostics from './pages/Diagnostics'
import { Admin } from './pages/Admin'
import { Login } from './pages/Login'
import { Signup } from './pages/Signup'
import { OAuthCallback } from './pages/OAuthCallback'

// v2 Pages
import PolicyLabV2 from './pages/PolicyLabV2'
import RecourseV2 from './pages/RecourseV2'
import ExperimentDesignV2 from './pages/ExperimentDesignV2'
import ExperimentStudio from './pages/ExperimentStudio'
import GrowthStudio from './pages/GrowthStudio'
import CustomerDigitalTwin from './pages/CustomerDigitalTwin'
import PolicyExportGate from './pages/PolicyExportGate'
import GovernanceCenter from './pages/GovernanceCenter'

// Data Management
import DatasetManagement from './pages/DatasetManagement'

// Visualizations

// Demo - REMOVED (not in specification, production only)

function App() {
  return (
    <BrowserRouter>
      <I18nProvider>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/auth/callback/:provider" element={<OAuthCallback />} />

          {/* Protected routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<DecisionConsole />} />
            <Route path="console" element={<DecisionConsole />} />

            {/* Dataset Management */}
            <Route path="datasets" element={<DatasetManagement />} />

            {/* Demo Mode - REMOVED (not in specification) */}

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

            {/* Experiment Studio - requires models:write permission */}
            <Route path="experiment-studio" element={
              <ProtectedRoute requiredPermission="models:write">
                <ExperimentStudio />
              </ProtectedRoute>
            } />

            {/* Growth & LTV Studio */}
            <Route path="growth-studio" element={
              <ProtectedRoute requiredPermission="models:read">
                <GrowthStudio />
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

            {/* Visualizations - 可視化ダッシュボード */}

            {/* Admin - requires admin role */}
            <Route path="admin" element={
              <ProtectedRoute requiredRole="admin">
                <Admin />
              </ProtectedRoute>
            } />

            {/* ===== v2 Routes ===== */}

            {/* Policy Lab v2 - Offline policy learning with OPE */}
            <Route path="policy-lab-v2" element={
              <ProtectedRoute requiredPermission="models:write">
                <PolicyLabV2 />
              </ProtectedRoute>
            } />

            {/* Recourse v2 - Individual counterfactual interventions */}
            <Route path="recourse-v2" element={
              <ProtectedRoute requiredPermission="models:read">
                <RecourseV2 />
              </ProtectedRoute>
            } />

            {/* Experiment Design v2 - A/B testing with power analysis */}
            <Route path="experiment-design-v2" element={
              <ProtectedRoute requiredPermission="policies:write">
                <ExperimentDesignV2 />
              </ProtectedRoute>
            } />

            {/* Customer Digital Twin - Customer persona simulation */}
            <Route path="digital-twin" element={
              <ProtectedRoute requiredPermission="models:read">
                <CustomerDigitalTwin />
              </ProtectedRoute>
            } />

            {/* Policy Export Gate - Policy-as-Code export and CI/CD integration */}
            <Route path="export-gate" element={
              <ProtectedRoute requiredPermission="policies:read">
                <PolicyExportGate />
              </ProtectedRoute>
            } />

            {/* Governance Center - Safety Gate */}
            <Route path="governance" element={
              <ProtectedRoute requiredPermission="policies:read">
                <GovernanceCenter />
              </ProtectedRoute>
            } />
          </Route>
        </Routes>
      </AuthProvider>
      </I18nProvider>
    </BrowserRouter>
  )
}

export default App
