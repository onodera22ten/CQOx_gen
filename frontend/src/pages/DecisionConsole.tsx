import { useQuery } from '@tanstack/react-query'
import { api } from '../utils/api'
import { formatYenShort, formatYenMan } from '../utils/format'

interface ConsoleSummary {
  total_decisions: number
  avg_delta_yen: number
  total_incremental_profit: number
  period_days?: number
  verdict_distribution?: {
    go: number
    canary: number
    hold: number
    total: number
  }
  max_delta_yen?: number
  min_delta_yen?: number
}

export default function DecisionConsole() {
  const { data, isLoading, error } = useQuery<ConsoleSummary>({
    queryKey: ['console-summary'],
    queryFn: async () => {
      const response = await api.get<ConsoleSummary>('/api/v1/console/delta-yen-summary?period_days=7')
      return response
    },
  })

  if (isLoading) {
    return <div style={{ padding: '32px', color: '#cbd5e0' }}>Loading...</div>
  }

  if (error) {
    return (
      <div style={{ padding: '32px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px' }}>
          Decision Console
        </h1>
        <div style={{ 
          background: 'rgba(245, 87, 108, 0.1)', 
          border: '1px solid rgba(245, 87, 108, 0.3)',
          borderRadius: '8px',
          padding: '16px',
          color: '#f5576c'
        }}>
          <div style={{ fontWeight: '600', marginBottom: '8px' }}>データ取得エラー</div>
          <div style={{ fontSize: '14px', opacity: 0.7 }}>
            バックエンドAPIに接続できません。Docker Composeが起動していることを確認してください。
          </div>
        </div>
      </div>
    )
  }

  const hasData = data && data.total_decisions > 0

  return (
    <div>
      <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px' }}>
        Decision Console
      </h1>

      {!hasData && (
        <div style={{ 
          marginBottom: '32px',
          padding: '24px', 
          background: 'rgba(59, 130, 246, 0.1)', 
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '12px',
          color: '#60a5fa'
        }}>
          <div style={{ fontWeight: '600', marginBottom: '8px', fontSize: '16px' }}>📊 データがまだありません</div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>
            Causal Design ページでデータセットをアップロードし、因果推論を実行してください。
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '24px', marginBottom: '32px' }}>
        <div style={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          borderRadius: '16px',
          padding: '32px',
          color: 'white',
          boxShadow: '0 10px 40px rgba(0,0,0,0.1)'
        }}>
          <div style={{ fontSize: '48px', fontWeight: '700', marginBottom: '8px' }}>
            {hasData ? formatYenShort(data.avg_delta_yen * data.total_decisions) : '¥0'}
          </div>
          <div style={{ fontSize: '14px', opacity: 0.9, marginBottom: '4px' }}>TOTAL INCREMENTAL PROFIT</div>
          <div style={{ fontSize: '12px', opacity: 0.7 }}>
            {hasData ? formatYenMan(data.avg_delta_yen * data.total_decisions) : ''}
          </div>
        </div>

        <div style={{ 
          background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
          borderRadius: '16px',
          padding: '32px',
          color: 'white',
          boxShadow: '0 10px 40px rgba(0,0,0,0.1)'
        }}>
          <div style={{ fontSize: '48px', fontWeight: '700', marginBottom: '8px' }}>
            {formatYenShort(data?.avg_delta_yen || 0)}
          </div>
          <div style={{ fontSize: '14px', opacity: 0.9, marginBottom: '4px' }}>AVERAGE Δ¥</div>
          <div style={{ fontSize: '12px', opacity: 0.7 }}>
            {data?.avg_delta_yen ? formatYenMan(data.avg_delta_yen) : ''}
          </div>
        </div>

        <div style={{ 
          background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
          borderRadius: '16px',
          padding: '32px',
          color: 'white',
          boxShadow: '0 10px 40px rgba(0,0,0,0.1)'
        }}>
          <div style={{ fontSize: '48px', fontWeight: '700', marginBottom: '8px' }}>
            {data?.total_decisions || 0}
          </div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>TOTAL DECISIONS</div>
        </div>
      </div>

      <div style={{ 
        background: '#2a2d3a',
        borderRadius: '16px',
        padding: '32px',
        marginBottom: '32px'
      }}>
        <h2 style={{ fontSize: '24px', fontWeight: '600', marginBottom: '24px', color: '#ffffff' }}>
          Recommended Policies
        </h2>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid rgba(255,255,255,0.1)' }}>
              <th style={{ padding: '16px', textAlign: 'left', color: '#a0aec0', fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px' }}>Policy Name</th>
              <th style={{ padding: '16px', textAlign: 'right', color: '#a0aec0', fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px' }}>Incremental Profit</th>
              <th style={{ padding: '16px', textAlign: 'right', color: '#a0aec0', fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px' }}>ROI</th>
              <th style={{ padding: '16px', textAlign: 'right', color: '#a0aec0', fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px' }}>Risk Score</th>
              <th style={{ padding: '16px', textAlign: 'right', color: '#a0aec0', fontWeight: '600', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px' }}>CAS Score</th>
            </tr>
          </thead>
          <tbody>
            {/* Mock recommended policies */}
            {[
              { name: 'Email Campaign A', profit: 2450000, roi: 5.2, risk: 0.12, cas: 0.87, verdict: 'GO' },
              { name: 'Multi-Channel B', profit: 1800000, roi: 3.8, risk: 0.18, cas: 0.75, verdict: 'GO' },
              { name: 'SMS Campaign C', profit: 1200000, roi: 3.1, risk: 0.22, cas: 0.68, verdict: 'CANARY' },
              { name: 'Push Notification D', profit: 950000, roi: 2.4, risk: 0.15, cas: 0.72, verdict: 'CANARY' },
              { name: 'Social Media E', profit: 650000, roi: 1.8, risk: 0.28, cas: 0.58, verdict: 'HOLD' },
            ].map((policy, index) => (
              <tr key={index} style={{
                borderBottom: '1px solid rgba(255,255,255,0.05)',
                transition: 'background 0.2s',
                cursor: 'pointer'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(59, 130, 246, 0.1)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <td style={{ padding: '20px 16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{
                      padding: '4px 10px',
                      borderRadius: '12px',
                      fontSize: '11px',
                      fontWeight: '700',
                      background: policy.verdict === 'GO' ? '#10b981' : policy.verdict === 'CANARY' ? '#f59e0b' : '#64748b',
                      color: '#fff'
                    }}>
                      {policy.verdict}
                    </span>
                    <span style={{ color: '#ffffff', fontWeight: '500' }}>{policy.name}</span>
                  </div>
                </td>
                <td style={{ padding: '20px 16px', textAlign: 'right', color: '#10b981', fontWeight: '600', fontSize: '16px' }}>
                  <div>{formatYenShort(policy.profit)}</div>
                  <div style={{ fontSize: '11px', color: '#94a3b8', fontWeight: '400', marginTop: '2px' }}>
                    {formatYenMan(policy.profit)}
                  </div>
                </td>
                <td style={{ padding: '20px 16px', textAlign: 'right', color: '#3b82f6', fontWeight: '600', fontSize: '16px' }}>
                  {policy.roi.toFixed(1)}x
                </td>
                <td style={{ padding: '20px 16px', textAlign: 'right' }}>
                  <span style={{
                    color: policy.risk < 0.15 ? '#10b981' : policy.risk < 0.25 ? '#f59e0b' : '#ef4444',
                    fontWeight: '600',
                    fontSize: '16px'
                  }}>
                    {(policy.risk * 100).toFixed(1)}%
                  </span>
                </td>
                <td style={{ padding: '20px 16px', textAlign: 'right' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '8px' }}>
                    <span style={{
                      color: policy.cas >= 0.8 ? '#10b981' : policy.cas >= 0.6 ? '#f59e0b' : '#ef4444',
                      fontWeight: '700',
                      fontSize: '16px'
                    }}>
                      {policy.cas.toFixed(2)}
                    </span>
                    <span style={{
                      fontSize: '10px',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: policy.cas >= 0.8 ? 'rgba(16, 185, 129, 0.2)' : policy.cas >= 0.6 ? 'rgba(245, 158, 11, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                      color: policy.cas >= 0.8 ? '#10b981' : policy.cas >= 0.6 ? '#f59e0b' : '#ef4444',
                      fontWeight: '600'
                    }}>
                      {policy.cas >= 0.8 ? 'HIGH' : policy.cas >= 0.6 ? 'MED' : 'LOW'}
                    </span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
