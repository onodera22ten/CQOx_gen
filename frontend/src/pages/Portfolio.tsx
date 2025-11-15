import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

export default function Portfolio() {
  const { data, isLoading } = useQuery({
    queryKey: ['portfolio-summary'],
    queryFn: async () => {
      const response = await axios.get('/api/portfolio/summary')
      return response.data
    },
  })

  if (isLoading) {
    return <div>Loading...</div>
  }

  return (
    <div>
      <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px' }}>
        Marketing Portfolio & ROI
      </h1>

      <div className="grid">
        <div className="card">
          <div className="card-title">Total Policies</div>
          <div style={{ fontSize: '36px', fontWeight: '700', color: '#2563eb' }}>
            {data?.total_policies || 0}
          </div>
        </div>

        <div className="card">
          <div className="card-title">Total Incremental Profit</div>
          <div style={{ fontSize: '36px', fontWeight: '700', color: '#16a34a' }}>
            ${((data?.total_incremental_profit || 0) / 1000000).toFixed(1)}M
          </div>
        </div>

        <div className="card">
          <div className="card-title">Average ROI</div>
          <div style={{ fontSize: '36px', fontWeight: '700', color: '#dc2626' }}>
            {(data?.total_roi || 0).toFixed(1)}x
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-title">Performance by Channel</div>
        <table className="table">
          <thead>
            <tr>
              <th>Channel</th>
              <th>Incremental Profit</th>
              <th>ROI</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data?.by_channel || {}).map(([channel, metrics]: [string, any]) => (
              <tr key={channel}>
                <td style={{ textTransform: 'capitalize', fontWeight: '500' }}>{channel}</td>
                <td>${(metrics.profit / 1000000).toFixed(1)}M</td>
                <td>{metrics.roi.toFixed(1)}x</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <div className="card-title">Multi-Objective Pareto Frontier</div>
        <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#f9fafb', borderRadius: '8px' }}>
          <p style={{ color: '#64748b' }}>Pareto frontier visualization (Wolfram integration)</p>
        </div>
      </div>
    </div>
  )
}
