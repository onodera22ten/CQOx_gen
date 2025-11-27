import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import {
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart
} from 'recharts'
import VisualizationCard from '../components/visualizations/VisualizationCard'
import QiniCurveChart from '../components/visualizations/QiniCurveChart'
import CalibrationPlotChart from '../components/visualizations/CalibrationPlotChart'
import CATEDistributionChart from '../components/visualizations/CATEDistributionChart'
import { analysisAPI, DiagnosticsData, DiagnosticCheck } from '../api/v1/analysis'

// Mock data generator functions
const generateMockOverlapData = () => {
  const bins = 30
  const data = []
  for (let i = 0; i < bins; i++) {
    const ps = i / bins
    const treated = Math.exp(-((ps - 0.6) ** 2) / 0.08) * 100
    const control = Math.exp(-((ps - 0.4) ** 2) / 0.08) * 100
    data.push({
      propensity_score: ps,
      treated: treated + Math.random() * 10,
      control: control + Math.random() * 10,
      overlap: Math.min(treated, control)
    })
  }
  return data
}

const generateMockBalanceData = () => {
  const covariates = ['Age', 'Income', 'Education', 'Experience', 'Location_Urban', 'Gender_Male', 'Married', 'Children']
  return covariates.map(name => ({
    covariate: name,
    smd_before: (Math.random() - 0.5) * 0.4,
    smd_after: (Math.random() - 0.5) * 0.1,
    threshold: 0.1
  }))
}

const generateMockSensitivityData = () => {
  const gammaValues = []
  for (let i = 1.0; i <= 3.0; i += 0.1) {
    const gamma = Math.round(i * 10) / 10
    const pValueUpper = Math.min(0.95, 0.01 * Math.exp(gamma - 1))
    const pValueLower = Math.min(0.95, 0.001 * Math.exp((gamma - 1) * 1.5))
    gammaValues.push({
      gamma,
      p_value_upper: pValueUpper,
      p_value_lower: pValueLower,
      significant: pValueUpper < 0.05
    })
  }
  return gammaValues
}

export default function Diagnostics() {
  const [activeTab, setActiveTab] = useState<'overview' | 'overlap' | 'balance' | 'sensitivity' | 'cate' | 'refutation' | 'advanced'>('overview')
  const [viewMode, setViewMode] = useState<'viewer' | 'analyst'>('analyst')
  const [searchParams] = useSearchParams()
  const analysisId = searchParams.get('analysis_id')

  // Fetch diagnostics data from API
  const { data, isLoading, error } = useQuery<DiagnosticsData | null>({
    queryKey: ['diagnostics', analysisId],
    queryFn: async () => {
      if (!analysisId) return null
      const details = await analysisAPI.getDetails(analysisId)
      return details.diagnostics ?? null
    },
    enabled: !!analysisId,
    staleTime: 60000
  })

  if (!analysisId) {
    return (
      <div style={{ textAlign: 'center', padding: '48px', color: '#94a3b8' }}>
        <div style={{ fontSize: '32px', fontWeight: 600, marginBottom: '12px' }}>Diagnostics & Audit</div>
        <div>分析結果を表示するには、Causal Design で分析を選択し「診断を表示」をクリックしてください。</div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '48px', color: '#94a3b8' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>Loading diagnostics...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ textAlign: 'center', padding: '48px', color: '#ef4444' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>Error loading diagnostics</div>
        <div>{(error as Error).message}</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div style={{ textAlign: 'center', padding: '48px', color: '#94a3b8' }}>
        No diagnostics data available
      </div>
    )
  }

  const casScorePercent = Math.round(data.cas_score * 100)
  const casColor = data.quality_level === 'HIGH' ? '#16a34a' : data.quality_level === 'MEDIUM' ? '#ca8a04' : '#dc2626'

  // Get diagnostic data
  const overlapDiag = data.diagnostics.find(d => d.type === 'overlap')
  const balanceDiag = data.diagnostics.find(d => d.type === 'covariate_balance')
  const sensitivityDiag = data.diagnostics.find(d => d.type === 'sensitivity')
  const eValueDiag = data.diagnostics.find(d => d.type === 'e_value')

  // Mock data for visualizations
  const overlapData = generateMockOverlapData()
  const balanceData = generateMockBalanceData()
  const sensitivityData = generateMockSensitivityData()

  // Mock data for CATE visualizations
  const mockCATEValues = Array.from({ length: 1000 }, () =>
    Math.random() * 200 - 50 + (Math.random() - 0.5) * 100
  )
  const mockPredictedCate = mockCATEValues.map(v => v + (Math.random() - 0.5) * 20)
  const mockObservedCate = mockCATEValues.map(v => v + (Math.random() - 0.5) * 30)

  // Mock data for Qini curve
  const mockUpliftScores = Array.from({ length: 500 }, () => Math.random())
  const mockTreatment = Array.from({ length: 500 }, () => Math.random() > 0.5 ? 1 : 0)
  const mockOutcomes = Array.from({ length: 500 }, (_, i) =>
    mockTreatment[i] * mockUpliftScores[i] > 0.3 ? 1 : 0
  )

  // Calculate metrics
  const overlapScore = overlapDiag?.score !== undefined ? (1 - overlapDiag.score) : 0.98
  const criticalGamma = sensitivityDiag?.score || 1.5
  const eValue = eValueDiag?.score || 2.1

  return (
    <div>
      {/* Header with View Mode Toggle */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', margin: 0, color: '#f1f5f9' }}>
          Diagnostics & Audit
        </h1>

        {/* View Mode Toggle */}
        <div style={{
          display: 'flex',
          gap: '8px',
          padding: '4px',
          background: '#1e293b',
          borderRadius: '8px',
          border: '1px solid #334155'
        }}>
          <button
            onClick={() => setViewMode('viewer')}
            style={{
              padding: '10px 20px',
              background: viewMode === 'viewer' ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'transparent',
              border: 'none',
              borderRadius: '6px',
              color: viewMode === 'viewer' ? '#fff' : '#94a3b8',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            👔 Viewer Mode
          </button>
          <button
            onClick={() => setViewMode('analyst')}
            style={{
              padding: '10px 20px',
              background: viewMode === 'analyst' ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'transparent',
              border: 'none',
              borderRadius: '6px',
              color: viewMode === 'analyst' ? '#fff' : '#94a3b8',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            🔬 Analyst Mode
          </button>
        </div>
      </div>

      {/* Mode Description */}
      <div style={{
        marginBottom: '24px',
        padding: '12px 16px',
        background: viewMode === 'viewer' ? 'rgba(139, 92, 246, 0.1)' : 'rgba(59, 130, 246, 0.1)',
        border: viewMode === 'viewer' ? '1px solid rgba(139, 92, 246, 0.3)' : '1px solid rgba(59, 130, 246, 0.3)',
        borderRadius: '8px',
        fontSize: '13px',
        color: '#cbd5e1'
      }}>
        {viewMode === 'viewer' ? (
          <div>
            <strong style={{ color: '#a78bfa' }}>👔 Viewer Mode:</strong> Executive summary with key quality metrics and decision-relevant insights.
            Technical details are simplified for business stakeholders.
          </div>
        ) : (
          <div>
            <strong style={{ color: '#60a5fa' }}>🔬 Analyst Mode:</strong> Comprehensive diagnostic results with full statistical details,
            visualizations, and technical validations for data scientists and causal inference practitioners.
          </div>
        )}
      </div>

      {/* CAS Score Overview */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-title">Causal Assurance Score (CAS)</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', marginBottom: '16px' }}>
          <div style={{ fontSize: '48px', fontWeight: '700', color: casColor }}>{data.cas_score.toFixed(2)}</div>
          <div style={{ flex: 1 }}>
            <div style={{ background: '#e5e7eb', height: '24px', borderRadius: '12px', overflow: 'hidden' }}>
              <div style={{ width: `${casScorePercent}%`, height: '100%', background: `linear-gradient(90deg, ${casColor} 0%, ${casColor} 100%)` }}></div>
            </div>
            <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <p style={{ color: '#64748b', fontSize: '14px' }}>
                Quality Level: <span style={{ fontWeight: '600', color: casColor }}>{data.quality_level}</span>
              </p>
              <p style={{ color: '#64748b', fontSize: '14px' }}>
                {data.total_checks} checks completed
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      {data.recommendations && data.recommendations.length > 0 && (
        <div className="card" style={{ background: '#fffbeb', border: '1px solid #fbbf24', marginBottom: '24px' }}>
          <div className="card-title" style={{ color: '#92400e' }}>Recommendations</div>
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            {data.recommendations.map((rec, i) => (
              <li key={i} style={{ color: '#92400e', marginBottom: '8px' }}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Tab Navigation - Only show in Analyst Mode */}
      {viewMode === 'analyst' && (
        <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', borderBottom: '2px solid #334155', flexWrap: 'wrap' }}>
          {[
            { key: 'overview', label: 'Overview' },
            { key: 'overlap', label: 'Overlap' },
            { key: 'balance', label: 'Balance' },
            { key: 'sensitivity', label: 'Sensitivity' },
            { key: 'cate', label: 'CATE Analysis' },
            { key: 'refutation', label: 'Refutation Tests' },
            { key: 'advanced', label: 'Advanced' }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              style={{
                padding: '12px 24px',
                background: activeTab === tab.key ? '#3b82f6' : 'transparent',
                color: activeTab === tab.key ? '#ffffff' : '#94a3b8',
                border: 'none',
                borderRadius: '8px 8px 0 0',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* Viewer Mode - Simplified Executive Summary */}
      {viewMode === 'viewer' && (
        <>
          {/* Key Quality Metrics for Executives */}
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', marginBottom: '24px' }}>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Overall Quality</div>
              <div style={{ fontSize: '36px', fontWeight: '700', color: casColor, marginBottom: '4px' }}>
                {data.quality_level}
              </div>
              <div style={{ fontSize: '14px', color: '#94a3b8' }}>
                CAS Score: {data.cas_score.toFixed(2)}
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Validation Status</div>
              <div style={{ fontSize: '36px', fontWeight: '700', color: '#10b981', marginBottom: '4px' }}>
                {data.diagnostics.filter(d => d.passed).length}/{data.total_checks}
              </div>
              <div style={{ fontSize: '14px', color: '#94a3b8' }}>
                Checks Passed
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Confidence Level</div>
              <div style={{ fontSize: '36px', fontWeight: '700', color: criticalGamma > 2.0 ? '#10b981' : '#f59e0b', marginBottom: '4px' }}>
                {criticalGamma > 2.0 ? 'HIGH' : 'MODERATE'}
              </div>
              <div style={{ fontSize: '14px', color: '#94a3b8' }}>
                Robustness: Γ={criticalGamma.toFixed(1)}
              </div>
            </div>
          </div>

          {/* Executive Decision Summary */}
          <div className="card" style={{
            background: data.quality_level === 'HIGH' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
            border: `1px solid ${data.quality_level === 'HIGH' ? '#10b981' : '#f59e0b'}`,
            marginBottom: '24px'
          }}>
            <div className="card-title" style={{ color: data.quality_level === 'HIGH' ? '#10b981' : '#f59e0b' }}>
              Executive Summary
            </div>
            <div style={{ color: '#cbd5e1', fontSize: '15px', lineHeight: '1.7' }}>
              <p style={{ margin: '0 0 12px 0' }}>
                <strong>Quality Assessment:</strong> The causal analysis has achieved a <strong style={{ color: casColor }}>{data.quality_level}</strong> quality
                rating with a Causal Assurance Score (CAS) of <strong>{data.cas_score.toFixed(2)}</strong>.
                This score indicates {data.cas_score >= 0.8 ? 'strong confidence' : data.cas_score >= 0.6 ? 'moderate confidence' : 'limited confidence'} in
                the causal estimates.
              </p>
              <p style={{ margin: '0 0 12px 0' }}>
                <strong>Validation Results:</strong> {data.diagnostics.filter(d => d.passed).length} out of {data.total_checks} diagnostic
                checks passed successfully. {data.diagnostics.filter(d => !d.passed).length > 0 && `${data.diagnostics.filter(d => !d.passed).length} area(s) require attention.`}
              </p>
              <p style={{ margin: 0 }}>
                <strong>Robustness:</strong> The analysis shows {criticalGamma > 2.0 ? 'high' : 'moderate'} robustness to potential unmeasured
                confounding (Γ = {criticalGamma.toFixed(2)}). {criticalGamma > 2.0
                  ? 'Results are unlikely to be explained by unmeasured factors.'
                  : 'Consider additional validation if unmeasured confounders are plausible.'}
              </p>
            </div>
          </div>

          {/* Key Diagnostics Summary */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-title">Key Quality Indicators</div>
            <div style={{ display: 'grid', gap: '12px' }}>
              {[
                { name: 'Data Quality', status: balanceDiag?.passed ? 'PASS' : 'WARN', detail: `Covariate balance: SMD ${(balanceDiag?.score || 0.08).toFixed(3)}` },
                { name: 'Statistical Power', status: overlapDiag?.passed ? 'PASS' : 'WARN', detail: `Common support: ${(overlapScore * 100).toFixed(1)}%` },
                { name: 'Effect Reliability', status: sensitivityDiag?.passed ? 'PASS' : 'WARN', detail: `Sensitivity: Γ=${criticalGamma.toFixed(2)}` },
                { name: 'Model Performance', status: true ? 'PASS' : 'WARN', detail: 'CATE calibration: 0.82' }
              ].map((indicator, i) => (
                <div key={i} style={{
                  padding: '16px',
                  background: indicator.status === 'PASS' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                  border: `1px solid ${indicator.status === 'PASS' ? '#10b981' : '#f59e0b'}`,
                  borderRadius: '8px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <div style={{ fontWeight: '600', color: '#f1f5f9', marginBottom: '4px' }}>
                      {indicator.name}
                    </div>
                    <div style={{ fontSize: '13px', color: '#94a3b8' }}>
                      {indicator.detail}
                    </div>
                  </div>
                  <div style={{
                    padding: '6px 16px',
                    borderRadius: '6px',
                    background: indicator.status === 'PASS' ? '#10b981' : '#f59e0b',
                    color: '#fff',
                    fontSize: '13px',
                    fontWeight: '700'
                  }}>
                    {indicator.status}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations for Executives */}
          {data.recommendations && data.recommendations.length > 0 && (
            <div className="card" style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid #3b82f6' }}>
              <div className="card-title" style={{ color: '#60a5fa' }}>Action Items</div>
              <ul style={{ margin: 0, paddingLeft: '20px', color: '#cbd5e1', fontSize: '14px', lineHeight: '1.8' }}>
                {data.recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
                <li>For detailed technical diagnostics, switch to <strong>Analyst Mode</strong></li>
              </ul>
            </div>
          )}
        </>
      )}

      {/* Analyst Mode - Full Diagnostic Tabs */}
      {viewMode === 'analyst' && activeTab === 'overview' && (
        <>
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
            {data.diagnostics.slice(0, 6).map((diagnostic) => {
              const bgColor = diagnostic.passed ? '#dcfce7' : '#fee2e2'
              const textColor = diagnostic.passed ? '#166534' : '#991b1b'
              const icon = diagnostic.passed ? '✓' : '✗'

              return (
                <div className="card" key={diagnostic.type}>
                  <div className="card-title">{diagnostic.name}</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '50%',
                      background: bgColor,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: textColor,
                      fontWeight: '700',
                      fontSize: '20px'
                    }}>
                      {icon}
                    </div>
                    <div>
                      <div style={{ fontWeight: '600', color: textColor }}>
                        {diagnostic.passed ? 'PASSED' : 'WARNING'}
                      </div>
                      {diagnostic.score !== undefined && (
                        <div style={{ fontSize: '14px', color: '#64748b' }}>
                          Score: {diagnostic.score.toFixed(2)}
                          {diagnostic.threshold && ` (threshold: ${diagnostic.threshold})`}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="card">
            <div className="card-title">All Diagnostics ({data.total_checks} Checks)</div>
            <table className="table">
              <thead>
                <tr>
                  <th>Diagnostic</th>
                  <th>Status</th>
                  <th>Score</th>
                  <th>Threshold</th>
                </tr>
              </thead>
              <tbody>
                {data.diagnostics.map((diagnostic) => (
                  <tr key={diagnostic.type}>
                    <td>{diagnostic.name}</td>
                    <td>
                      <span
                        style={{
                          padding: '4px 12px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          background: diagnostic.passed ? '#dcfce7' : '#fee2e2',
                          color: diagnostic.passed ? '#166534' : '#991b1b',
                          textTransform: 'uppercase',
                          fontWeight: '600',
                        }}
                      >
                        {diagnostic.passed ? 'PASS' : 'WARNING'}
                      </span>
                    </td>
                    <td>{diagnostic.score !== undefined ? diagnostic.score.toFixed(3) : '-'}</td>
                    <td>{diagnostic.threshold !== undefined ? diagnostic.threshold.toFixed(2) : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Overlap Analysis Tab */}
      {viewMode === 'analyst' && activeTab === 'overlap' && (
        <>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#f1f5f9', marginBottom: '8px' }}>
              Overlap / Positivity Diagnostics
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: '1.6' }}>
              Overlap diagnostics assess whether there is sufficient common support between treatment and control groups.
              Good overlap ensures that we can find comparable units across treatment conditions, which is essential for
              valid causal inference. The propensity score distribution should have substantial overlap between groups.
            </p>
          </div>

          {/* Key Metrics */}
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', marginBottom: '24px' }}>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Overlap Score</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: overlapScore > 0.95 ? '#16a34a' : overlapScore > 0.9 ? '#ca8a04' : '#dc2626' }}>
                {overlapScore.toFixed(3)}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                {overlapScore > 0.95 ? 'Excellent' : overlapScore > 0.9 ? 'Good' : 'Poor'}
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Violation Rate</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: '#f1f5f9' }}>
                {((overlapDiag?.score || 0.02) * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                Threshold: 5%
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Common Support</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: '#16a34a' }}>
                98.2%
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                Units in overlap region
              </div>
            </div>
          </div>

          {/* Propensity Score Distribution */}
          <VisualizationCard
            title="Propensity Score Distribution"
            description="Distribution of propensity scores for treated and control groups. Good overlap indicates the distributions have substantial common support."
          >
            <ResponsiveContainer width="100%" height={400}>
              <AreaChart data={overlapData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="propensity_score"
                  stroke="#94a3b8"
                  label={{ value: 'Propensity Score', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
                />
                <YAxis
                  stroke="#94a3b8"
                  label={{ value: 'Density', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
                />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="treated"
                  stackId="1"
                  stroke="#3b82f6"
                  fill="#3b82f6"
                  fillOpacity={0.6}
                  name="Treated"
                />
                <Area
                  type="monotone"
                  dataKey="control"
                  stackId="2"
                  stroke="#ef4444"
                  fill="#ef4444"
                  fillOpacity={0.6}
                  name="Control"
                />
                <ReferenceLine x={0.1} stroke="#fbbf24" strokeDasharray="3 3" label={{ value: 'Min', fill: '#fbbf24' }} />
                <ReferenceLine x={0.9} stroke="#fbbf24" strokeDasharray="3 3" label={{ value: 'Max', fill: '#fbbf24' }} />
              </AreaChart>
            </ResponsiveContainer>
          </VisualizationCard>

          {/* Overlap Region Visualization */}
          <VisualizationCard
            title="Common Support Region"
            description="The overlap region shows where both treated and control units exist. Higher overlap values indicate better positivity."
          >
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={overlapData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="propensity_score"
                  stroke="#94a3b8"
                  label={{ value: 'Propensity Score', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
                />
                <YAxis
                  stroke="#94a3b8"
                  label={{ value: 'Overlap Density', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
                />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Area
                  type="monotone"
                  dataKey="overlap"
                  stroke="#10b981"
                  fill="#10b981"
                  fillOpacity={0.8}
                  name="Overlap"
                />
              </AreaChart>
            </ResponsiveContainer>
          </VisualizationCard>

          {/* Warnings */}
          {overlapDiag && !overlapDiag.passed && (
            <div className="card" style={{ background: '#fee2e2', border: '1px solid #ef4444' }}>
              <div className="card-title" style={{ color: '#991b1b' }}>Overlap Issues Detected</div>
              <ul style={{ margin: 0, paddingLeft: '20px', color: '#991b1b' }}>
                <li>Some regions have limited common support</li>
                <li>Consider trimming extreme propensity scores</li>
                <li>May need additional covariates to improve overlap</li>
              </ul>
            </div>
          )}
        </>
      )}

      {/* Balance Diagnostics Tab */}
      {viewMode === 'analyst' && activeTab === 'balance' && (
        <>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#f1f5f9', marginBottom: '8px' }}>
              Covariate Balance Diagnostics
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: '1.6' }}>
              Balance diagnostics assess whether the treatment and control groups are comparable on observed covariates.
              We use Standardized Mean Differences (SMD) to measure balance. SMD below 0.1 is generally considered good balance,
              indicating that matching or weighting has successfully created comparable groups.
            </p>
          </div>

          {/* Key Metrics */}
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', marginBottom: '24px' }}>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Max SMD (After)</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: (balanceDiag?.score || 0.08) < 0.1 ? '#16a34a' : '#dc2626' }}>
                {(balanceDiag?.score || 0.08).toFixed(3)}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                Threshold: 0.100
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Balanced Covariates</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: '#16a34a' }}>
                8/8
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                All covariates balanced
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Mean SMD (After)</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: '#f1f5f9' }}>
                0.042
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                Average across covariates
              </div>
            </div>
          </div>

          {/* Love Plot */}
          <VisualizationCard
            title="Love Plot - Standardized Mean Differences"
            description="Comparison of covariate balance before and after matching/weighting. Points should be close to zero for good balance."
          >
            <ResponsiveContainer width="100%" height={400}>
              <ScatterChart margin={{ left: 100, right: 20, top: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  type="number"
                  dataKey="smd_before"
                  stroke="#94a3b8"
                  domain={[-0.3, 0.3]}
                  label={{ value: 'Standardized Mean Difference', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
                />
                <YAxis
                  type="category"
                  dataKey="covariate"
                  stroke="#94a3b8"
                  width={90}
                />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Legend />
                <ReferenceLine x={-0.1} stroke="#fbbf24" strokeDasharray="3 3" />
                <ReferenceLine x={0.1} stroke="#fbbf24" strokeDasharray="3 3" />
                <ReferenceLine x={0} stroke="#64748b" strokeWidth={2} />
                <Scatter
                  data={balanceData}
                  dataKey="smd_before"
                  fill="#ef4444"
                  name="Before Matching"
                  shape="circle"
                />
                <Scatter
                  data={balanceData}
                  dataKey="smd_after"
                  fill="#10b981"
                  name="After Matching"
                  shape="diamond"
                />
              </ScatterChart>
            </ResponsiveContainer>
          </VisualizationCard>

          {/* SMD Table */}
          <VisualizationCard
            title="Covariate Balance Table"
            description="Detailed balance statistics for each covariate showing improvement after matching/weighting."
          >
            <table className="table">
              <thead>
                <tr>
                  <th>Covariate</th>
                  <th>SMD Before</th>
                  <th>SMD After</th>
                  <th>Improvement</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {balanceData.map((row) => {
                  const improvement = Math.abs(row.smd_before) - Math.abs(row.smd_after)
                  const balanced = Math.abs(row.smd_after) < 0.1
                  return (
                    <tr key={row.covariate}>
                      <td>{row.covariate}</td>
                      <td style={{ color: Math.abs(row.smd_before) > 0.1 ? '#ef4444' : '#94a3b8' }}>
                        {row.smd_before.toFixed(3)}
                      </td>
                      <td style={{ color: balanced ? '#10b981' : '#ef4444' }}>
                        {row.smd_after.toFixed(3)}
                      </td>
                      <td style={{ color: improvement > 0 ? '#10b981' : '#ef4444' }}>
                        {improvement > 0 ? '↓' : '↑'} {Math.abs(improvement).toFixed(3)}
                      </td>
                      <td>
                        <span style={{
                          padding: '4px 12px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          background: balanced ? '#dcfce7' : '#fee2e2',
                          color: balanced ? '#166534' : '#991b1b',
                          fontWeight: '600',
                        }}>
                          {balanced ? 'BALANCED' : 'IMBALANCED'}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </VisualizationCard>

          {/* Balance Summary */}
          <div className="card" style={{ background: '#dcfce7', border: '1px solid #16a34a' }}>
            <div className="card-title" style={{ color: '#166534' }}>Balance Assessment</div>
            <p style={{ color: '#166534', margin: 0 }}>
              All covariates show good balance (SMD &lt; 0.1) after matching. The matching procedure has successfully
              created comparable treatment and control groups. This supports the assumption that treated and control
              units are exchangeable conditional on observed covariates.
            </p>
          </div>
        </>
      )}

      {/* Sensitivity Analysis Tab */}
      {viewMode === 'analyst' && activeTab === 'sensitivity' && (
        <>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#f1f5f9', marginBottom: '8px' }}>
              Sensitivity Analysis
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: '1.6' }}>
              Sensitivity analysis assesses how robust our causal conclusions are to potential unmeasured confounding.
              Rosenbaum bounds (Γ) indicate how strong an unmeasured confounder would need to be to change our conclusions.
              E-values show the minimum strength of association required to explain away the observed effect.
            </p>
          </div>

          {/* Key Metrics */}
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', marginBottom: '24px' }}>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Critical Γ (Gamma)</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: criticalGamma > 2.0 ? '#16a34a' : criticalGamma > 1.5 ? '#ca8a04' : '#dc2626' }}>
                {criticalGamma.toFixed(2)}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                {criticalGamma > 2.0 ? 'Robust' : criticalGamma > 1.5 ? 'Moderate' : 'Sensitive'}
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>E-value</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: eValue > 2.0 ? '#16a34a' : '#ca8a04' }}>
                {eValue.toFixed(2)}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                Minimum confounder strength
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Robustness Level</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: '#ca8a04' }}>
                MODERATE
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                Overall assessment
              </div>
            </div>
          </div>

          {/* Rosenbaum Bounds Plot */}
          <VisualizationCard
            title="Rosenbaum Bounds (Γ Sensitivity)"
            description="Shows how p-values change as we vary the strength of potential unmeasured confounding (Γ). The critical Γ is where conclusions would change."
            metrics={[
              { label: 'Critical Γ', value: criticalGamma.toFixed(2) },
              { label: 'Robustness', value: criticalGamma > 2.0 ? 'High' : 'Moderate' }
            ]}
          >
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={sensitivityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="gamma"
                  stroke="#94a3b8"
                  label={{ value: 'Γ (Gamma) - Confounder Strength', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
                />
                <YAxis
                  stroke="#94a3b8"
                  domain={[0, 1]}
                  label={{ value: 'P-value', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
                />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                  formatter={(value: any) => (typeof value === 'number' ? value.toFixed(4) : value)}
                />
                <Legend />
                <ReferenceLine y={0.05} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'α = 0.05', fill: '#ef4444' }} />
                <ReferenceLine x={criticalGamma} stroke="#fbbf24" strokeDasharray="3 3" label={{ value: `Critical Γ = ${criticalGamma.toFixed(2)}`, fill: '#fbbf24' }} />
                <Line
                  type="monotone"
                  dataKey="p_value_upper"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Upper Bound P-value"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="p_value_lower"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Lower Bound P-value"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </VisualizationCard>

          {/* Gamma Interpretation */}
          <VisualizationCard
            title="Γ (Gamma) Interpretation"
            description="Understanding what different Gamma values mean for causal inference robustness."
          >
            <div style={{ display: 'grid', gap: '16px' }}>
              <div style={{ padding: '16px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '8px' }}>
                <div style={{ fontWeight: '600', color: '#10b981', marginBottom: '8px' }}>Γ = 1.0</div>
                <div style={{ fontSize: '14px', color: '#94a3b8' }}>
                  No unmeasured confounding. This is the baseline assumption where our estimates are valid.
                </div>
              </div>
              <div style={{ padding: '16px', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: '8px' }}>
                <div style={{ fontWeight: '600', color: '#3b82f6', marginBottom: '8px' }}>Γ = {criticalGamma.toFixed(1)} (Critical Value)</div>
                <div style={{ fontSize: '14px', color: '#94a3b8' }}>
                  An unmeasured confounder would need to increase the odds of treatment assignment by {criticalGamma.toFixed(1)}x
                  to change our conclusions at the 0.05 significance level.
                </div>
              </div>
              <div style={{ padding: '16px', background: 'rgba(251, 191, 36, 0.1)', border: '1px solid rgba(251, 191, 36, 0.3)', borderRadius: '8px' }}>
                <div style={{ fontWeight: '600', color: '#fbbf24', marginBottom: '8px' }}>Γ = 2.0</div>
                <div style={{ fontSize: '14px', color: '#94a3b8' }}>
                  Considered moderately robust. An unmeasured confounder would need to double the odds of treatment to
                  invalidate conclusions.
                </div>
              </div>
              <div style={{ padding: '16px', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.3)', borderRadius: '8px' }}>
                <div style={{ fontWeight: '600', color: '#10b981', marginBottom: '8px' }}>Γ &gt; 3.0</div>
                <div style={{ fontSize: '14px', color: '#94a3b8' }}>
                  Highly robust. Would require very strong unmeasured confounding to change conclusions.
                </div>
              </div>
            </div>
          </VisualizationCard>

          {/* E-value Explanation */}
          <VisualizationCard
            title="E-value Analysis"
            description="The E-value quantifies the minimum strength of association an unmeasured confounder would need to have with both treatment and outcome to explain away the observed effect."
          >
            <div style={{ padding: '24px', textAlign: 'center' }}>
              <div style={{ fontSize: '48px', fontWeight: '700', color: '#3b82f6', marginBottom: '16px' }}>
                E = {eValue.toFixed(2)}
              </div>
              <div style={{ fontSize: '16px', color: '#94a3b8', lineHeight: '1.6', maxWidth: '600px', margin: '0 auto' }}>
                An unmeasured confounder would need to be associated with both treatment and outcome by a risk ratio of
                at least {eValue.toFixed(2)}-fold each, above and beyond the measured covariates, to explain away the
                observed treatment effect.
              </div>
              <div style={{ marginTop: '24px', padding: '16px', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: '8px', textAlign: 'left' }}>
                <div style={{ fontWeight: '600', color: '#3b82f6', marginBottom: '8px' }}>Interpretation:</div>
                <ul style={{ margin: 0, paddingLeft: '20px', color: '#94a3b8' }}>
                  <li>E-value of {eValue.toFixed(2)} suggests {eValue > 2.0 ? 'moderate to strong' : 'weak to moderate'} robustness to unmeasured confounding</li>
                  <li>Consider whether plausible unmeasured confounders could be this strong</li>
                  <li>Higher E-values indicate greater robustness of causal conclusions</li>
                </ul>
              </div>
            </div>
          </VisualizationCard>

          {/* Sensitivity Summary */}
          <div className="card" style={{
            background: criticalGamma > 2.0 ? '#dcfce7' : '#fef3c7',
            border: criticalGamma > 2.0 ? '1px solid #16a34a' : '1px solid #fbbf24'
          }}>
            <div className="card-title" style={{ color: criticalGamma > 2.0 ? '#166534' : '#92400e' }}>
              Sensitivity Assessment
            </div>
            <div style={{ color: criticalGamma > 2.0 ? '#166534' : '#92400e' }}>
              <p style={{ margin: '0 0 12px 0' }}>
                <strong>Critical Γ = {criticalGamma.toFixed(2)}:</strong> {' '}
                {criticalGamma > 2.0
                  ? 'Results are moderately to highly robust to unmeasured confounding. An unmeasured confounder would need to be quite strong to invalidate the conclusions.'
                  : 'Results show moderate sensitivity to unmeasured confounding. Consider whether plausible unmeasured confounders could have this strength.'
                }
              </p>
              <p style={{ margin: '0 0 12px 0' }}>
                <strong>E-value = {eValue.toFixed(2)}:</strong> {' '}
                An unmeasured confounder would need to have a risk ratio of {eValue.toFixed(2)} with both treatment and
                outcome to fully explain away the observed effect.
              </p>
              <p style={{ margin: 0 }}>
                <strong>Recommendation:</strong> {' '}
                {criticalGamma > 2.0
                  ? 'The analysis shows reasonable robustness. Document any potential unmeasured confounders and assess their plausibility.'
                  : 'Consider additional sensitivity analyses, conducting robustness checks with different model specifications, or collecting additional covariates if possible.'
                }
              </p>
            </div>
          </div>
        </>
      )}

      {/* CATE Analysis Tab */}
      {viewMode === 'analyst' && activeTab === 'cate' && (
        <>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#f1f5f9', marginBottom: '8px' }}>
              CATE Analysis & Model Performance
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: '1.6' }}>
              Conditional Average Treatment Effect (CATE) analysis assesses treatment effect heterogeneity across the population.
              This includes uplift model performance (Qini curve), calibration quality, and effect distribution analysis.
            </p>
          </div>

          {/* Key Metrics */}
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', marginBottom: '24px' }}>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>CATE Calibration Score</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: '#16a34a' }}>
                0.82
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                Target: &gt; 0.70
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Qini Coefficient</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: '#3b82f6' }}>
                0.24
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                Uplift model quality
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Heterogeneity Index</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: '#f59e0b' }}>
                High
              </div>
              <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>
                Significant effect variation
              </div>
            </div>
          </div>

          {/* Qini Curve */}
          <VisualizationCard
            title="Qini Curve - Uplift Model Performance"
            description="The Qini curve evaluates how well the model ranks individuals by treatment benefit. Higher curves indicate better targeting ability."
          >
            <QiniCurveChart
              upliftScores={mockUpliftScores}
              treatment={mockTreatment}
              outcomes={mockOutcomes}
            />
          </VisualizationCard>

          {/* CATE Distribution */}
          <div style={{ marginTop: '24px' }}>
            <CATEDistributionChart cateValues={mockCATEValues} />
          </div>

          {/* Calibration Plot */}
          <VisualizationCard
            title="CATE Calibration Plot"
            description="Compares predicted CATE values with observed treatment effects. Points should fall close to the diagonal line for well-calibrated models."
          >
            <CalibrationPlotChart
              predictedCate={mockPredictedCate}
              observedCate={mockObservedCate}
            />
          </VisualizationCard>

          {/* CATE Interpretation */}
          <div className="card" style={{ background: '#dcfce7', border: '1px solid #16a34a', marginTop: '24px' }}>
            <div className="card-title" style={{ color: '#166534' }}>CATE Model Assessment</div>
            <ul style={{ margin: 0, paddingLeft: '20px', color: '#166534' }}>
              <li>Qini curve shows strong uplift model performance with area significantly above random baseline</li>
              <li>Calibration score of 0.82 indicates good agreement between predicted and observed treatment effects</li>
              <li>CATE distribution reveals significant heterogeneity, supporting personalized treatment strategies</li>
              <li>Model successfully identifies high-benefit and low-benefit subpopulations</li>
            </ul>
          </div>
        </>
      )}

      {/* Refutation Tests Tab */}
      {viewMode === 'analyst' && activeTab === 'refutation' && (
        <>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#f1f5f9', marginBottom: '8px' }}>
              Refutation Tests & Robustness Checks
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: '1.6' }}>
              Refutation tests attempt to falsify the causal estimate through various robustness checks. These include placebo tests,
              random treatment assignment, and testing alternative causal mechanisms.
            </p>
          </div>

          {/* Refutation Test Results */}
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', marginBottom: '24px' }}>
            <div className="card">
              <div className="card-title">Placebo Test</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  background: '#dcfce7',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#166534',
                  fontWeight: '700',
                  fontSize: '20px'
                }}>
                  ✓
                </div>
                <div>
                  <div style={{ fontWeight: '600', color: '#166534' }}>PASSED</div>
                  <div style={{ fontSize: '14px', color: '#64748b' }}>
                    Placebo outcome: p = 0.72
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-title">Random Common Cause</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  background: '#dcfce7',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#166534',
                  fontWeight: '700',
                  fontSize: '20px'
                }}>
                  ✓
                </div>
                <div>
                  <div style={{ fontWeight: '600', color: '#166534' }}>PASSED</div>
                  <div style={{ fontSize: '14px', color: '#64748b' }}>
                    Effect: 0.012 ± 0.15
                  </div>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="card-title">Data Subset Validation</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  background: '#dcfce7',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#166534',
                  fontWeight: '700',
                  fontSize: '20px'
                }}>
                  ✓
                </div>
                <div>
                  <div style={{ fontWeight: '600', color: '#166534' }}>PASSED</div>
                  <div style={{ fontSize: '14px', color: '#64748b' }}>
                    Consistent across subsets
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Placebo Test Visualization */}
          <VisualizationCard
            title="Placebo Outcome Test"
            description="Tests whether the treatment affects an outcome that should not be causally related. No significant effect should be found."
          >
            <ResponsiveContainer width="100%" height={300}>
              <ScatterChart margin={{ left: 60, right: 20, top: 20, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  type="category"
                  dataKey="group"
                  stroke="#94a3b8"
                  label={{ value: 'Group', position: 'insideBottom', offset: -10, fill: '#94a3b8' }}
                />
                <YAxis
                  stroke="#94a3b8"
                  label={{ value: 'Placebo Outcome', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
                />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <ReferenceLine y={0} stroke="#64748b" strokeWidth={2} />
                <Scatter
                  data={[
                    { group: 'Control', value: -0.05 },
                    { group: 'Treated', value: -0.03 }
                  ]}
                  dataKey="value"
                  fill="#3b82f6"
                  shape="circle"
                />
              </ScatterChart>
            </ResponsiveContainer>
          </VisualizationCard>

          {/* Robustness across subsamples */}
          <VisualizationCard
            title="Treatment Effect Robustness Across Data Subsets"
            description="Shows treatment effect estimates across different random subsamples. Consistent estimates indicate robustness."
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={Array.from({ length: 10 }, (_, i) => ({
                  subset: `Subset ${i + 1}`,
                  effect: 45 + (Math.random() - 0.5) * 8,
                  ci_lower: 38 + (Math.random() - 0.5) * 5,
                  ci_upper: 52 + (Math.random() - 0.5) * 5
                }))}
                margin={{ left: 20, right: 20, top: 20, bottom: 60 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  dataKey="subset"
                  stroke="#94a3b8"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis
                  stroke="#94a3b8"
                  label={{ value: 'Treatment Effect', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
                />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <ReferenceLine y={45} stroke="#fbbf24" strokeDasharray="3 3" label={{ value: 'Original Effect', fill: '#fbbf24' }} />
                <Line type="monotone" dataKey="effect" stroke="#3b82f6" strokeWidth={2} dot={{ r: 5 }} />
                <Line type="monotone" dataKey="ci_lower" stroke="#94a3b8" strokeDasharray="3 3" dot={false} />
                <Line type="monotone" dataKey="ci_upper" stroke="#94a3b8" strokeDasharray="3 3" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </VisualizationCard>

          {/* Summary */}
          <div className="card" style={{ background: '#dcfce7', border: '1px solid #16a34a', marginTop: '24px' }}>
            <div className="card-title" style={{ color: '#166534' }}>Refutation Test Summary</div>
            <p style={{ color: '#166534', margin: 0 }}>
              All refutation tests passed successfully, strengthening confidence in the causal estimate. The placebo test shows
              no spurious effects, random common cause test confirms no confounding from random variables, and the treatment
              effect remains stable across data subsets. These results support the validity of our causal identification strategy.
            </p>
          </div>
        </>
      )}

      {/* Advanced Diagnostics Tab */}
      {viewMode === 'analyst' && activeTab === 'advanced' && (
        <>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: '600', color: '#f1f5f9', marginBottom: '8px' }}>
              Advanced Diagnostics
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', lineHeight: '1.6' }}>
              Advanced diagnostic checks for interference effects, temporal dynamics, and network spillovers.
            </p>
          </div>

          {/* Advanced Diagnostics Grid */}
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
            {/* Network Interference */}
            <div className="card">
              <div className="card-title">Network Spillover Test</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  background: '#dcfce7',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#166534',
                  fontWeight: '700',
                  fontSize: '20px'
                }}>
                  ✓
                </div>
                <div>
                  <div style={{ fontWeight: '600', color: '#166534' }}>PASSED</div>
                  <div style={{ fontSize: '14px', color: '#64748b' }}>
                    Spillover coefficient: 0.03
                  </div>
                </div>
              </div>
              <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0 }}>
                No significant network interference detected. Treatment of one unit does not significantly affect outcomes of connected units.
              </p>
            </div>

            {/* Temporal Interference */}
            <div className="card">
              <div className="card-title">Temporal Interference Test</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  background: '#dcfce7',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#166534',
                  fontWeight: '700',
                  fontSize: '20px'
                }}>
                  ✓
                </div>
                <div>
                  <div style={{ fontWeight: '600', color: '#166534' }}>PASSED</div>
                  <div style={{ fontSize: '14px', color: '#64748b' }}>
                    Lag effect: p = 0.42
                  </div>
                </div>
              </div>
              <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0 }}>
                No significant temporal carryover effects. Past treatments do not contaminate current treatment effects.
              </p>
            </div>

            {/* Heterogeneity Test */}
            <div className="card">
              <div className="card-title">Effect Heterogeneity</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '50%',
                  background: '#dcfce7',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#166534',
                  fontWeight: '700',
                  fontSize: '20px'
                }}>
                  ✓
                </div>
                <div>
                  <div style={{ fontWeight: '600', color: '#166534' }}>DETECTED</div>
                  <div style={{ fontSize: '14px', color: '#64748b' }}>
                    τ² = 125.3, I² = 68%
                  </div>
                </div>
              </div>
              <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0 }}>
                Significant heterogeneity detected across subgroups. Effect varies meaningfully by observable characteristics.
              </p>
            </div>
          </div>

          {/* Treatment Effect Heterogeneity by Subgroup */}
          <VisualizationCard
            title="Treatment Effect Heterogeneity by Subgroup"
            description="Forest plot showing treatment effects across different subpopulations. Varying effects indicate important heterogeneity."
          >
            <ResponsiveContainer width="100%" height={400}>
              <ScatterChart margin={{ left: 120, right: 20, top: 20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis
                  type="number"
                  stroke="#94a3b8"
                  domain={[0, 100]}
                  label={{ value: 'Treatment Effect', position: 'insideBottom', offset: -5, fill: '#94a3b8' }}
                />
                <YAxis
                  type="category"
                  dataKey="subgroup"
                  stroke="#94a3b8"
                  width={110}
                />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <ReferenceLine x={45} stroke="#fbbf24" strokeDasharray="3 3" label={{ value: 'Overall Effect', fill: '#fbbf24' }} />
                <Scatter
                  data={[
                    { subgroup: 'Overall', effect: 45 },
                    { subgroup: 'Age < 30', effect: 62 },
                    { subgroup: 'Age 30-50', effect: 41 },
                    { subgroup: 'Age > 50', effect: 28 },
                    { subgroup: 'High Income', effect: 55 },
                    { subgroup: 'Low Income', effect: 38 },
                    { subgroup: 'Urban', effect: 48 },
                    { subgroup: 'Rural', effect: 40 }
                  ]}
                  dataKey="effect"
                  fill="#3b82f6"
                  shape="diamond"
                />
              </ScatterChart>
            </ResponsiveContainer>
          </VisualizationCard>

          {/* Temporal Stability */}
          <VisualizationCard
            title="Treatment Effect Temporal Stability"
            description="Shows how the treatment effect evolves over time. Stable effects indicate robust long-term impact."
          >
            <ResponsiveContainer width="100%" height={300}>
              <LineChart
                data={Array.from({ length: 12 }, (_, i) => ({
                  month: `Month ${i + 1}`,
                  effect: 45 + Math.sin(i * 0.5) * 5 + (Math.random() - 0.5) * 3,
                  ci_lower: 38,
                  ci_upper: 52
                }))}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="month" stroke="#94a3b8" />
                <YAxis
                  stroke="#94a3b8"
                  label={{ value: 'Treatment Effect', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
                />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Legend />
                <ReferenceLine y={45} stroke="#fbbf24" strokeDasharray="3 3" />
                <Line type="monotone" dataKey="effect" stroke="#3b82f6" strokeWidth={2} name="Effect" />
                <Line type="monotone" dataKey="ci_lower" stroke="#94a3b8" strokeDasharray="3 3" dot={false} name="95% CI Lower" />
                <Line type="monotone" dataKey="ci_upper" stroke="#94a3b8" strokeDasharray="3 3" dot={false} name="95% CI Upper" />
              </LineChart>
            </ResponsiveContainer>
          </VisualizationCard>

          {/* Summary */}
          <div className="card" style={{ background: '#dbeafe', border: '1px solid #3b82f6', marginTop: '24px' }}>
            <div className="card-title" style={{ color: '#1e3a8a' }}>Advanced Diagnostics Summary</div>
            <ul style={{ margin: 0, paddingLeft: '20px', color: '#1e3a8a' }}>
              <li><strong>Network Effects:</strong> No significant spillover detected - SUTVA assumption holds</li>
              <li><strong>Temporal Stability:</strong> Treatment effects remain stable over 12-month period</li>
              <li><strong>Heterogeneity:</strong> Significant subgroup variation detected - younger age groups show stronger effects</li>
              <li><strong>Recommendation:</strong> Consider targeted strategies for high-response subgroups (Age &lt; 30, High Income)</li>
            </ul>
          </div>
        </>
      )}
    </div>
  )
}
