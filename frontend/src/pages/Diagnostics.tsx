import { useQuery } from '@tanstack/react-query'

interface DiagnosticCheck {
  type: string
  name: string
  passed: boolean
  score?: number
  threshold?: number
  data?: any
}

interface DiagnosticsData {
  status: string
  cas_score: number
  quality_level: string
  diagnostics: DiagnosticCheck[]
  recommendations?: string[]
  total_checks: number
}

export default function Diagnostics() {
  // Fetch diagnostics data from API
  const { data, isLoading, error } = useQuery<DiagnosticsData>({
    queryKey: ['diagnostics'],
    queryFn: async () => {
      // Mock data for now - replace with actual API call
      // const response = await fetch('http://localhost:8000/api/diagnostics/run', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ dataset_path: 'path/to/dataset.csv' })
      // })
      // return response.json()

      // Mock response matching API structure
      return {
        status: 'completed',
        cas_score: 0.85,
        quality_level: 'HIGH',
        total_checks: 14,
        diagnostics: [
          { type: 'covariate_balance', name: 'Covariate Balance (SMD)', passed: true, score: 0.08, threshold: 0.1 },
          { type: 'love_plot', name: 'Love Plot', passed: true },
          { type: 'overlap', name: 'Overlap / Positivity', passed: true, score: 0.02, threshold: 0.05 },
          { type: 'propensity_density', name: 'Propensity Density', passed: true },
          { type: 'sensitivity', name: 'Sensitivity (Γ)', passed: false, score: 1.5, threshold: 1.3 },
          { type: 'e_value', name: 'E-value', passed: true, score: 2.1, threshold: 1.5 },
          { type: 'qini_curve', name: 'Qini Curve', passed: true },
          { type: 'calibration', name: 'CATE Calibration', passed: true, score: 0.82, threshold: 0.7 },
          { type: 'heterogeneity', name: 'CATE Heterogeneity', passed: true },
          { type: 'network_interference', name: 'Network Spillover', passed: true },
          { type: 'temporal_interference', name: 'Temporal Interference', passed: true },
          { type: 'placebo_test', name: 'Placebo Test', passed: true },
          { type: 'refutation', name: 'Refutation Tests', passed: true },
          { type: 'robustness', name: 'Robustness Checks', passed: true },
        ],
        recommendations: [
          'Sensitivity analysis shows moderate robustness (Γ=1.5)',
          'Consider additional covariate adjustment for X3',
          'Overall causal estimate quality is HIGH'
        ]
      }
    },
    staleTime: 60000
  })

  if (isLoading) {
    return <div>Loading diagnostics...</div>
  }

  if (error) {
    return <div>Error loading diagnostics: {(error as Error).message}</div>
  }

  if (!data) {
    return <div>No diagnostics data available</div>
  }

  const casScorePercent = Math.round(data.cas_score * 100)
  const casColor = data.quality_level === 'HIGH' ? '#16a34a' : data.quality_level === 'MEDIUM' ? '#ca8a04' : '#dc2626'
  const casBgColor = data.quality_level === 'HIGH' ? '#dcfce7' : data.quality_level === 'MEDIUM' ? '#fef3c7' : '#fee2e2'

  return (
    <div>
      <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px' }}>
        Diagnostics & Audit
      </h1>

      <div className="card">
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

      {data.recommendations && data.recommendations.length > 0 && (
        <div className="card" style={{ background: '#fffbeb', border: '1px solid #fbbf24' }}>
          <div className="card-title" style={{ color: '#92400e' }}>Recommendations</div>
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            {data.recommendations.map((rec, i) => (
              <li key={i} style={{ color: '#92400e', marginBottom: '8px' }}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
        {data.diagnostics.slice(0, 6).map((diagnostic) => {
          const bgColor = diagnostic.passed ? '#dcfce7' : '#fee2e2'
          const textColor = diagnostic.passed ? '#166534' : '#991b1b'
          const icon = diagnostic.passed ? '✓' : '✗'

          return (
            <div className="card" key={diagnostic.type}>
              <div className="card-title">{diagnostic.name}</div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: '50%', background: bgColor, display: 'flex', alignItems: 'center', justifyContent: 'center', color: textColor, fontWeight: '700', fontSize: '20px' }}>
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
    </div>
  )
}
