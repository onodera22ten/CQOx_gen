import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

export default function DecisionConsole() {
  const { data, isLoading } = useQuery({
    queryKey: ['console-summary'],
    queryFn: async () => {
      const response = await axios.get('/api/console/summary')
      return response.data
    },
  })

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px' }}>
        Decision Console
      </h1>

      <div className="grid">
        <div className="metric-card">
          <div className="metric-value">
            ${((data?.total_incremental_profit || 0) / 1000000).toFixed(1)}M
          </div>
          <div className="metric-label">Total Incremental Profit</div>
        </div>

        <div className="metric-card" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
          <div className="metric-value">{(data?.avg_roi || 0).toFixed(1)}x</div>
          <div className="metric-label">Average ROI</div>
        </div>

        <div className="metric-card" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
          <div className="metric-value">{data?.total_campaigns || 0}</div>
          <div className="metric-label">Total Campaigns</div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Recommended Policies</div>
        <table className="table">
          <thead>
            <tr>
              <th>Policy Name</th>
              <th>Incremental Profit</th>
              <th>ROI</th>
              <th>Risk Score</th>
              <th>CAS Score</th>
            </tr>
          </thead>
          <tbody>
            {(data?.recommended_policies || []).map((policy: any) => (
              <tr key={policy.policy_id}>
                <td>{policy.name}</td>
                <td>${(policy.incremental_profit / 1000000).toFixed(1)}M</td>
                <td>{policy.roi.toFixed(1)}x</td>
                <td>{(policy.risk_score * 100).toFixed(0)}%</td>
                <td>{(policy.cas_score * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
