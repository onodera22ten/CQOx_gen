import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../utils/api'
import EnhancedParetoChart from '../components/visualizations/EnhancedParetoChart'
import { ContextBar } from '../components/ContextBar'
import { DecisionSummaryCard } from '../components/DecisionSummaryCard'
import { formatYenShort, formatYenMan } from '../utils/format'

interface PortfolioSummary {
  total_policies: number
  total_incremental_profit: number
  total_roi: number
  by_channel: Record<string, { profit: number; roi: number }>
}

export default function Portfolio() {
  const [activeView, setActiveView] = useState<'overview' | 'frontier'>('overview')

  const { data, isLoading, error} = useQuery<PortfolioSummary>({
    queryKey: ['portfolio-summary'],
    queryFn: async () => {
      const response = await api.get<PortfolioSummary>('/api/portfolio/summary')
      return response
    },
  })

  const [selectedPolicy, setSelectedPolicy] = useState<string | null>('Policy E')

  // Enhanced Pareto data with CAS scores and baseline comparison
  const baselineProfit = 0
  const baselineRisk = 0

  const paretoData = [
    {
      name: 'Policy A',
      profit: 1500000,
      risk: 0.15,
      cas: 0.75,
      deltaProfit: 1500000,
      deltaRisk: 0.15,
      isParetoEfficient: false,
      description: 'Email campaign targeting high-value customers with personalized offers',
      targetChannel: 'Email',
      targetSegment: 'High-value customers (top 20%)',
      estimatedReach: 45000,
      estimatedCost: 320000,
      roi: 4.7
    },
    {
      name: 'Policy B',
      profit: 2800000,
      risk: 0.25,
      cas: 0.82,
      deltaProfit: 2800000,
      deltaRisk: 0.25,
      isParetoEfficient: true,
      description: 'Multi-channel campaign combining email, SMS, and push notifications',
      targetChannel: 'Multi-channel',
      targetSegment: 'Active users (last 30 days)',
      estimatedReach: 120000,
      estimatedCost: 850000,
      roi: 3.3
    },
    {
      name: 'Policy C',
      profit: 1200000,
      risk: 0.10,
      cas: 0.68,
      deltaProfit: 1200000,
      deltaRisk: 0.10,
      isParetoEfficient: false,
      description: 'Conservative retention campaign for at-risk customers',
      targetChannel: 'Email',
      targetSegment: 'At-risk customers (churn score > 0.6)',
      estimatedReach: 28000,
      estimatedCost: 180000,
      roi: 6.7
    },
    {
      name: 'Policy D',
      profit: 1800000,
      risk: 0.30,
      cas: 0.71,
      deltaProfit: 1800000,
      deltaRisk: 0.30,
      isParetoEfficient: false,
      description: 'Aggressive promotional campaign with high discount rates',
      targetChannel: 'Push + In-app',
      targetSegment: 'All active users',
      estimatedReach: 180000,
      estimatedCost: 1200000,
      roi: 1.5
    },
    {
      name: 'Policy E',
      profit: 5200000,
      risk: 0.12,
      cas: 0.92,
      deltaProfit: 5200000,
      deltaRisk: 0.12,
      isParetoEfficient: true,
      description: 'AI-optimized personalization engine with dynamic content',
      targetChannel: 'Email + Push',
      targetSegment: 'ML-predicted high-propensity users',
      estimatedReach: 95000,
      estimatedCost: 980000,
      roi: 5.3
    },
    {
      name: 'Policy F',
      profit: 800000,
      risk: 0.08,
      cas: 0.65,
      deltaProfit: 800000,
      deltaRisk: 0.08,
      isParetoEfficient: true,
      description: 'Low-risk test campaign for new product launch',
      targetChannel: 'Email',
      targetSegment: 'Early adopters segment',
      estimatedReach: 15000,
      estimatedCost: 120000,
      roi: 6.7
    },
  ]

  const bestPolicy = paretoData.reduce((best, policy) =>
    policy.profit / (1 + policy.risk) > best.profit / (1 + best.risk) ? policy : best
  )

  if (isLoading) {
    return (
      <div style={{ padding: '32px', color: '#cbd5e0' }}>
        Loading portfolio data...
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '32px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px' }}>
          Marketing Portfolio & ROI
        </h1>
        <div style={{ 
          background: 'rgba(245, 87, 108, 0.1)', 
          border: '1px solid rgba(245, 87, 108, 0.3)',
          borderRadius: '8px',
          padding: '16px',
          color: '#f5576c'
        }}>
          <div style={{ fontWeight: '600', marginBottom: '8px' }}>Portfolio data unavailable</div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>
            This feature requires backend API implementation.
          </div>
        </div>
      </div>
    )
  }

  const selected = paretoData.find(p => p.name === selectedPolicy) || bestPolicy

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px', color: '#fff' }}>
        Marketing Portfolio & ROI
      </h1>

      {/* Context Bar */}
      <ContextBar
        scenario={{
          id: 'portfolio-optimization',
          name: 'Multi-Policy Portfolio Optimization',
          type: 'Pareto Frontier Analysis',
        }}
        targetMetric={{
          outcome: 'Incremental Profit vs Risk',
        }}
      />

      {/* Decision Summary Card */}
      <DecisionSummaryCard
        title="Recommended Portfolio Strategy"
        verdict="Go"
        deltaYen={bestPolicy.deltaProfit}
        casScore={bestPolicy.cas}
        riskScore={bestPolicy.risk}
        roi={bestPolicy.profit / 1000000} // Simplified ROI
        reason={`Policy ${bestPolicy.name} offers the best risk-adjusted return with max Δ¥ subject to CAS≥0.8 & Risk≤0.3. This policy is on the Pareto frontier.`}
        recommendations={[
          `Deploy ${bestPolicy.name} as the primary policy`,
          `Monitor CAS score (currently ${bestPolicy.cas.toFixed(2)}) - maintain above 0.75`,
          `Total portfolio Pareto-efficient policies: ${paretoData.filter(p => p.isParetoEfficient).length}`,
          `Consider A/B testing with Policy ${paretoData.filter(p => p.isParetoEfficient && p.name !== bestPolicy.name)[0]?.name || 'B'} for validation`,
        ]}
        onViewDetails={() => {
          alert('Navigate to detailed diagnostics for ' + bestPolicy.name);
        }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <p style={{ color: '#94a3b8', fontSize: '14px' }}>
          Multi-objective optimization: {paretoData.length} policies analyzed
        </p>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={() => setActiveView('overview')}
            style={{
              padding: '10px 20px',
              background: activeView === 'overview' ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'rgba(51, 65, 85, 0.5)',
              border: 'none',
              borderRadius: '8px',
              color: '#fff',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            📊 Overview
          </button>
          <button
            onClick={() => setActiveView('frontier')}
            style={{
              padding: '10px 20px',
              background: activeView === 'frontier' ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'rgba(51, 65, 85, 0.5)',
              border: 'none',
              borderRadius: '8px',
              color: '#fff',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            🎯 Pareto Frontier
          </button>
        </div>
      </div>

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

      {activeView === 'overview' ? (
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
      ) : (
        <div style={{
          background: '#1e293b',
          borderRadius: '16px',
          padding: '32px',
          border: '1px solid #334155'
        }}>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '12px', color: '#fff' }}>
              🎯 Multi-Objective Pareto Frontier
            </h2>
            <p style={{ color: '#cbd5e1', fontSize: '14px' }}>
              比較: 利益 vs リスク - パレート効率的なpolicy群を可視化
            </p>
          </div>

          <div style={{
            background: 'rgba(59, 130, 246, 0.05)',
            border: '1px solid rgba(59, 130, 246, 0.2)',
            borderRadius: '12px',
            padding: '20px',
            marginBottom: '24px'
          }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '16px' }}>
              <div>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Total Policies Analyzed</div>
                <div style={{ fontSize: '24px', fontWeight: '700', color: '#3b82f6' }}>
                  {paretoData.length}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Pareto Efficient</div>
                <div style={{ fontSize: '24px', fontWeight: '700', color: '#10b981' }}>
                  {paretoData.filter((p, _i, arr) =>
                    !arr.some(other => other.profit > p.profit && other.risk < p.risk)
                  ).length}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Best Profit/Risk Ratio</div>
                <div style={{ fontSize: '24px', fontWeight: '700', color: '#f59e0b' }}>
                  {Math.max(...paretoData.map(p => p.profit / (p.risk * 1000000))).toFixed(1)}
                </div>
              </div>
            </div>

            <div style={{
              padding: '12px',
              background: 'rgba(139, 92, 246, 0.1)',
              borderRadius: '8px',
              fontSize: '13px',
              color: '#cbd5e1'
            }}>
              💡 <strong style={{ color: '#a78bfa' }}>パレート効率的なpolicy</strong>:
              他のpolicyと比較して、利益を犠牲にせずにリスクを減らすことも、リスクを増やさずに利益を上げることもできないpolicy。
              フロンティア上の点が最適なトレードオフを示します。
            </div>
          </div>

          <EnhancedParetoChart
            policies={paretoData}
            selectedPolicy={selectedPolicy}
            onSelectPolicy={(policy) => setSelectedPolicy(policy.name)}
          />

          <div style={{ marginTop: '24px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', color: '#fff' }}>
              Policy Details
            </h3>
            <div style={{ display: 'grid', gap: '12px' }}>
              {paretoData
                .sort((a, b) => b.profit - a.profit)
                .map(policy => {
                  const isPareto = !paretoData.some(other => other.profit > policy.profit && other.risk < policy.risk)
                  return (
                    <div
                      key={policy.name}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '16px',
                        background: isPareto ? 'rgba(16, 185, 129, 0.1)' : '#0f172a',
                        border: `1px solid ${isPareto ? 'rgba(16, 185, 129, 0.3)' : '#1e293b'}`,
                        borderRadius: '8px'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        {isPareto && <span style={{ fontSize: '20px' }}>⭐</span>}
                        <div>
                          <div style={{ fontWeight: '600', color: '#f1f5f9', fontSize: '15px' }}>
                            {policy.name}
                          </div>
                          <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                            {isPareto ? 'Pareto Efficient' : 'Dominated'}
                          </div>
                        </div>
                      </div>
                      <div style={{ display: 'flex', gap: '24px' }}>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '2px' }}>Profit</div>
                          <div style={{ fontSize: '16px', fontWeight: '600', color: '#10b981' }}>
                            ¥{(policy.profit / 1000).toFixed(0)}K
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '2px' }}>Risk</div>
                          <div style={{ fontSize: '16px', fontWeight: '600', color: '#ef4444' }}>
                            {(policy.risk * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '2px' }}>Ratio</div>
                          <div style={{ fontSize: '16px', fontWeight: '600', color: '#3b82f6' }}>
                            {(policy.profit / (policy.risk * 1000000)).toFixed(1)}
                          </div>
                        </div>
                      </div>
                    </div>
                  )
                })}
            </div>
          </div>

          {/* Selected Policy Details */}
          {selected && (
            <div style={{
              marginTop: '24px',
              background: '#1e293b',
              borderRadius: '16px',
              padding: '32px',
              border: '2px solid #3b82f6'
            }}>
              <div style={{ marginBottom: '24px' }}>
                <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '8px', color: '#fff', display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {selected.isParetoEfficient && <span style={{ fontSize: '24px' }}>⭐</span>}
                  {selected.name} - Detailed Specifications
                </h2>
                <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>
                  {(selected as any).description}
                </p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '24px' }}>
                <div style={{
                  padding: '16px',
                  background: 'rgba(16, 185, 129, 0.1)',
                  border: '1px solid rgba(16, 185, 129, 0.3)',
                  borderRadius: '12px'
                }}>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px', fontWeight: '600' }}>💰 EXPECTED PROFIT</div>
                  <div style={{ fontSize: '28px', fontWeight: '700', color: '#10b981', marginBottom: '4px' }}>
                    {formatYenShort(selected.profit)}
                  </div>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>
                    {formatYenMan(selected.profit)}
                  </div>
                  <div style={{ fontSize: '12px', color: '#10b981' }}>
                    ROI: {(selected as any).roi}x
                  </div>
                </div>

                <div style={{
                  padding: '16px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  borderRadius: '12px'
                }}>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px', fontWeight: '600' }}>⚠️ RISK SCORE</div>
                  <div style={{ fontSize: '28px', fontWeight: '700', color: '#ef4444', marginBottom: '4px' }}>
                    {(selected.risk * 100).toFixed(1)}%
                  </div>
                  <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                    {selected.risk < 0.15 ? 'Low Risk' : selected.risk < 0.25 ? 'Medium Risk' : 'High Risk'}
                  </div>
                </div>

                <div style={{
                  padding: '16px',
                  background: 'rgba(59, 130, 246, 0.1)',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  borderRadius: '12px'
                }}>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px', fontWeight: '600' }}>🎯 CAS SCORE</div>
                  <div style={{ fontSize: '28px', fontWeight: '700', color: selected.cas >= 0.8 ? '#10b981' : selected.cas >= 0.6 ? '#f59e0b' : '#ef4444', marginBottom: '4px' }}>
                    {selected.cas.toFixed(2)}
                  </div>
                  <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                    {selected.cas >= 0.8 ? 'High Confidence' : selected.cas >= 0.6 ? 'Medium Confidence' : 'Low Confidence'}
                  </div>
                </div>

                <div style={{
                  padding: '16px',
                  background: 'rgba(245, 158, 11, 0.1)',
                  border: '1px solid rgba(245, 158, 11, 0.3)',
                  borderRadius: '12px'
                }}>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px', fontWeight: '600' }}>👥 ESTIMATED REACH</div>
                  <div style={{ fontSize: '28px', fontWeight: '700', color: '#f59e0b', marginBottom: '4px' }}>
                    {((selected as any).estimatedReach / 1000).toFixed(0)}K
                  </div>
                  <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                    users
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px', color: '#f1f5f9' }}>
                    📋 Campaign Details
                  </h3>
                  <div style={{ display: 'grid', gap: '12px' }}>
                    <div style={{ padding: '12px', background: '#0f172a', borderRadius: '8px' }}>
                      <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Target Channel</div>
                      <div style={{ fontSize: '14px', color: '#f1f5f9', fontWeight: '600' }}>{(selected as any).targetChannel}</div>
                    </div>
                    <div style={{ padding: '12px', background: '#0f172a', borderRadius: '8px' }}>
                      <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Target Segment</div>
                      <div style={{ fontSize: '14px', color: '#f1f5f9', fontWeight: '600' }}>{(selected as any).targetSegment}</div>
                    </div>
                    <div style={{ padding: '12px', background: '#0f172a', borderRadius: '8px' }}>
                      <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>Estimated Cost</div>
                      <div style={{ fontSize: '14px', color: '#f1f5f9', fontWeight: '600' }}>{formatYenShort((selected as any).estimatedCost)}</div>
                      <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>{formatYenMan((selected as any).estimatedCost)}</div>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '12px', color: '#f1f5f9' }}>
                    ⚡ Status & Recommendations
                  </h3>
                  <div style={{ padding: '16px', background: selected.isParetoEfficient ? 'rgba(16, 185, 129, 0.1)' : 'rgba(100, 116, 139, 0.1)', borderRadius: '12px', border: `1px solid ${selected.isParetoEfficient ? '#10b981' : '#64748b'}` }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                      <span style={{ fontSize: '20px' }}>{selected.isParetoEfficient ? '✓' : '⚠️'}</span>
                      <span style={{ fontSize: '14px', fontWeight: '700', color: selected.isParetoEfficient ? '#10b981' : '#94a3b8' }}>
                        {selected.isParetoEfficient ? 'Pareto Efficient - Recommended' : 'Dominated - Not Optimal'}
                      </span>
                    </div>
                    <p style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: '1.6', margin: 0 }}>
                      {selected.isParetoEfficient
                        ? 'This policy is on the Pareto frontier. No other policy offers strictly better profit-risk tradeoff. Recommended for deployment.'
                        : 'This policy is dominated by other policies on the Pareto frontier. Consider alternatives with better profit-risk tradeoffs.'}
                    </p>
                  </div>

                  <div style={{ marginTop: '16px', display: 'flex', gap: '12px' }}>
                    <button
                      onClick={() => {
                        // Navigate to diagnostics page for this policy
                        window.location.href = '/diagnostics';
                      }}
                      style={{
                        flex: 1,
                        padding: '12px 24px',
                        background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                        border: 'none',
                        borderRadius: '8px',
                        color: '#fff',
                        fontSize: '14px',
                        fontWeight: '600',
                        cursor: 'pointer'
                      }}
                    >
                      📊 View Diagnostics
                    </button>
                    <button
                      onClick={() => {
                        window.location.href = '/export-gate';
                      }}
                      style={{
                        flex: 1,
                        padding: '12px 24px',
                        background: selected.isParetoEfficient ? '#10b981' : 'rgba(100, 116, 139, 0.5)',
                        border: 'none',
                        borderRadius: '8px',
                        color: '#fff',
                        fontSize: '14px',
                        fontWeight: '600',
                        cursor: selected.isParetoEfficient ? 'pointer' : 'not-allowed',
                        opacity: selected.isParetoEfficient ? 1 : 0.5
                      }}
                      disabled={!selected.isParetoEfficient}
                    >
                      📤 Export Policy
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
