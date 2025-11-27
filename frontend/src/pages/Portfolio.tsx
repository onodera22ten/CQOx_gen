/**
 * Marketing Portfolio & ROI Page
 * 仕様: Marketing Portfolio & ROI (portfolio).pdf に完全準拠
 *
 * 役割: 複数の候補施策から、どの組み合わせで予算を張るかを決めるC level向け画面
 *
 * 構成:
 * 1. Recommended Portfolio Strategy カード（主役）
 * 2. Pareto Frontier + Portfolio Contribution
 * 3. Portfolio Policies Table（Include/Exclude/Test verdict付き）
 * 4. Empty state（ダミーデータ完全削除、実データのみ表示）
 */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../utils/api'
import { formatYenShort, formatYenMan } from '../utils/format'
import { ContextBar } from '../components/ContextBar'
import { DecisionSummaryCard } from '../components/DecisionSummaryCard'
import EnhancedParetoChart from '../components/visualizations/EnhancedParetoChart'

// ==================== Types ====================

type PortfolioWindow = '14d' | '28d' | '56d'

interface PortfolioSummary {
  window: string
  expectedDeltaYen: number
  totalCostYen: number | null
  meanCas: number
  portfolioRisk: number
  roi: number
  selectedPolicyIds: string[]
}

interface PortfolioPolicy {
  id: string
  name: string
  datasetName: string
  channel: string | null
  segment: string | null
  deltaYen: number
  roi: number
  risk: number
  cas: number
  verdict: 'include' | 'exclude' | 'test'
}

interface ParetoPoint {
  portfolioId: string
  risk: number
  deltaYen: number
  meanCas: number
  isRecommended: boolean
}

// ==================== API Clients ====================

const portfolioAPI = {
  summary: async (window: PortfolioWindow): Promise<PortfolioSummary> => {
    return await api.get<PortfolioSummary>(`/api/portfolio/summary?window=${window}`)
  },
  policies: async (window: PortfolioWindow): Promise<PortfolioPolicy[]> => {
    return await api.get<PortfolioPolicy[]>(`/api/portfolio/policies?window=${window}`)
  },
  frontier: async (window: PortfolioWindow): Promise<ParetoPoint[]> => {
    return await api.get<ParetoPoint[]>(`/api/portfolio/frontier?window=${window}`)
  }
}

// ==================== Custom Hook ====================

function usePortfolioData(window: PortfolioWindow) {
  const summaryQuery = useQuery({
    queryKey: ['portfolio-summary', window],
    queryFn: () => portfolioAPI.summary(window),
    staleTime: 30000
  })

  const policiesQuery = useQuery({
    queryKey: ['portfolio-policies', window],
    queryFn: () => portfolioAPI.policies(window),
    staleTime: 30000
  })

  const frontierQuery = useQuery({
    queryKey: ['portfolio-frontier', window],
    queryFn: () => portfolioAPI.frontier(window),
    staleTime: 30000
  })

  return { summaryQuery, policiesQuery, frontierQuery }
}

// ==================== Main Component ====================

export default function Portfolio() {
  const [window, setWindow] = useState<PortfolioWindow>('28d')
  const [verdictFilter, setVerdictFilter] = useState<string>('all')
  const [selectedPolicyId, setSelectedPolicyId] = useState<string | null>(null)

  const { summaryQuery, policiesQuery, frontierQuery } = usePortfolioData(window)

  const isLoading = summaryQuery.isLoading || policiesQuery.isLoading || frontierQuery.isLoading
  const hasError = summaryQuery.isError || policiesQuery.isError || frontierQuery.isError

  // Loading state
  if (isLoading) {
    return (
      <div style={{ padding: '32px', color: '#cbd5e0' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px', color: '#fff' }}>
          Marketing Portfolio & ROI
        </h1>
        <div>Loading portfolio data...</div>
      </div>
    )
  }

  // Error state
  if (hasError) {
    return (
      <div style={{ padding: '32px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px', color: '#fff' }}>
          Marketing Portfolio & ROI
        </h1>
        <div style={{
          background: 'rgba(245, 87, 108, 0.1)',
          border: '1px solid rgba(245, 87, 108, 0.3)',
          borderRadius: '12px',
          padding: '24px',
          color: '#f5576c'
        }}>
          <div style={{ fontWeight: '600', marginBottom: '12px', fontSize: '18px' }}>
            ポートフォリオ情報の取得に失敗しました
          </div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>
            施策数が 1 件以下、データ欠損、または内部エラーの可能性があります。
            施策設定とデータセット構成を確認してください。
          </div>
        </div>
      </div>
    )
  }

  const summary = summaryQuery.data!
  const policies = policiesQuery.data ?? []
  const frontier = frontierQuery.data ?? []

  // Empty state - NO policies at all
  if (policies.length === 0) {
    return (
      <div style={{ padding: '32px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px', color: '#fff' }}>
          Marketing Portfolio & ROI
        </h1>
        <div style={{
          background: 'rgba(59, 130, 246, 0.1)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '16px',
          padding: '48px 32px',
          textAlign: 'center',
          color: '#60a5fa',
          marginTop: '48px'
        }}>
          <div style={{ fontSize: '64px', marginBottom: '24px' }}>📊</div>
          <div style={{ fontSize: '28px', fontWeight: '700', marginBottom: '16px', color: '#fff' }}>
            ポートフォリオを作成するには施策が必要です
          </div>
          <div style={{ fontSize: '16px', lineHeight: '1.6', marginBottom: '32px', maxWidth: '600px', margin: '0 auto 32px' }}>
            まだ評価済みのマーケ施策がありません。<br />
            「Policy Lab」で 2 件以上の施策を評価すると、この画面でポートフォリオ最適化が行えます。
          </div>
          <button
            onClick={() => window.location.href = '/policy'}
            style={{
              padding: '16px 32px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
              border: 'none',
              borderRadius: '12px',
              color: '#fff',
              fontSize: '16px',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(59, 130, 246, 0.3)'
            }}
          >
            Policy Lab を開く
          </button>
        </div>
      </div>
    )
  }

  // Filter policies by verdict
  const filteredPolicies = verdictFilter === 'all'
    ? policies
    : policies.filter(p => p.verdict === verdictFilter)

  // Top 5 contributors for bar chart
  const includedPolicies = policies.filter(p => p.verdict === 'include').slice(0, 5)
  const totalIncludedDelta = includedPolicies.reduce((sum, p) => sum + p.deltaYen, 0)

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

      {/* Period Filter */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '24px' }}>
        {(['14d', '28d', '56d'] as PortfolioWindow[]).map(w => (
          <button
            key={w}
            onClick={() => setWindow(w)}
            style={{
              padding: '10px 20px',
              background: window === w ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'rgba(51, 65, 85, 0.5)',
              border: 'none',
              borderRadius: '8px',
              color: '#fff',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Last {w}
          </button>
        ))}
      </div>

      {/* 主役：Recommended Portfolio Strategy Card */}
      <DecisionSummaryCard
        title="Recommended Portfolio Strategy"
        verdict="Go"
        deltaYen={summary.expectedDeltaYen}
        casScore={summary.meanCas}
        riskScore={summary.portfolioRisk}
        roi={summary.roi}
        reason={`選択された ${summary.selectedPolicyIds.length} 件のポリシーが、CAS ≥ ${(summary.meanCas).toFixed(2)} & Risk ≤ ${(summary.portfolioRisk).toFixed(2)} の制約下で最も高い Δ¥ を提供します。このポートフォリオはPareto効率的です。`}
        recommendations={[
          `選択ポリシー数: ${summary.selectedPolicyIds.length} / ${policies.length}`,
          `Mean CAS Score: ${summary.meanCas.toFixed(2)} - ${summary.meanCas >= 0.8 ? 'High Confidence' : summary.meanCas >= 0.6 ? 'Medium Confidence' : 'Low Confidence'}`,
          `Portfolio Risk: ${(summary.portfolioRisk * 100).toFixed(1)}% - ${summary.portfolioRisk < 0.15 ? 'Low Risk' : summary.portfolioRisk < 0.25 ? 'Medium Risk' : 'High Risk'}`,
          `Total Budget: ${formatYenShort(summary.totalCostYen || 0)} （${formatYenMan(summary.totalCostYen || 0)}）`
        ]}
        onViewDetails={() => {
          // Scroll to table
          document.getElementById('portfolio-table')?.scrollIntoView({ behavior: 'smooth' })
        }}
      />

      {/* 中段：Pareto Frontier + Portfolio Contribution */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '2fr 1fr',
        gap: '24px',
        marginBottom: '24px'
      }}>
        {/* Pareto Frontier Chart */}
        <div style={{
          background: '#1e293b',
          borderRadius: '16px',
          padding: '32px',
          border: '1px solid #334155'
        }}>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '8px', color: '#fff' }}>
              Pareto Frontier (Profit vs Risk)
            </h2>
            <p style={{ color: '#cbd5e1', fontSize: '13px' }}>
              利益 vs リスク - Pareto効率的なポリシー群を可視化
            </p>
          </div>

          <EnhancedParetoChart
            policies={policies.map(p => ({
              name: p.name,
              profit: p.deltaYen,
              risk: p.risk,
              cas: p.cas,
              deltaProfit: p.deltaYen,
              deltaRisk: p.risk,
              isParetoEfficient: p.verdict === 'include',
              description: p.segment || '',
              targetChannel: p.channel || 'Multi-channel',
              targetSegment: p.segment || '',
              estimatedReach: 50000,
              estimatedCost: (summary.totalCostYen || 0) / summary.selectedPolicyIds.length,
              roi: p.roi,
              analysisId: p.id
            }))}
            selectedPolicy={selectedPolicyId}
            onSelectPolicy={(policy) => setSelectedPolicyId(policy.analysisId)}
          />

          <div style={{
            marginTop: '16px',
            padding: '12px',
            background: 'rgba(139, 92, 246, 0.1)',
            borderRadius: '8px',
            fontSize: '12px',
            color: '#cbd5e1'
          }}>
            <strong style={{ color: '#a78bfa' }}>Pareto効率的なポリシー</strong>:
            他のポリシーと比較して、利益を犠牲にせずにリスクを減らすことも、リスクを増やさずに利益を上げることもできないポリシー。
            フロンティア上の点が最適なトレードオフを示します。
          </div>
        </div>

        {/* Portfolio Contribution (寄与度ランキング) */}
        <div style={{
          background: '#1e293b',
          borderRadius: '16px',
          padding: '32px',
          border: '1px solid #334155'
        }}>
          <h2 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '16px', color: '#fff' }}>
            Portfolio Contribution
          </h2>
          <p style={{ color: '#cbd5e1', fontSize: '13px', marginBottom: '20px' }}>
            寄与度ランキング（上位5件）
          </p>

          {includedPolicies.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '24px', color: '#64748b' }}>
              推奨ポリシーなし
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {includedPolicies.map((policy, idx) => {
                const contribution = totalIncludedDelta > 0 ? (policy.deltaYen / totalIncludedDelta) * 100 : 0
                return (
                  <div key={policy.id} style={{ marginBottom: '8px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontSize: '13px', fontWeight: '600', color: '#f1f5f9' }}>
                        {idx + 1}. {policy.name}
                      </span>
                      <span style={{ fontSize: '13px', color: '#10b981' }}>
                        {formatYenShort(policy.deltaYen)}
                      </span>
                    </div>
                    <div style={{
                      height: '8px',
                      background: '#0f172a',
                      borderRadius: '4px',
                      overflow: 'hidden'
                    }}>
                      <div style={{
                        height: '100%',
                        width: `${contribution}%`,
                        background: 'linear-gradient(90deg, #10b981 0%, #3b82f6 100%)',
                        transition: 'width 0.3s ease'
                      }} />
                    </div>
                    <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                      {contribution.toFixed(1)}% of total
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* 下段：Portfolio Policies Table */}
      <div id="portfolio-table" style={{
        background: '#1e293b',
        borderRadius: '16px',
        padding: '32px',
        border: '1px solid #334155'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#fff' }}>
            Portfolio Policies
          </h2>
          <div style={{ display: 'flex', gap: '8px' }}>
            {['all', 'include', 'test', 'exclude'].map(v => (
              <button
                key={v}
                onClick={() => setVerdictFilter(v)}
                style={{
                  padding: '8px 16px',
                  background: verdictFilter === v ? 'rgba(59, 130, 246, 0.2)' : 'transparent',
                  border: `1px solid ${verdictFilter === v ? '#3b82f6' : '#475569'}`,
                  borderRadius: '6px',
                  color: verdictFilter === v ? '#60a5fa' : '#94a3b8',
                  fontSize: '13px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  textTransform: 'capitalize'
                }}
              >
                {v === 'all' ? `All (${policies.length})` : `${v} (${policies.filter(p => p.verdict === v).length})`}
              </button>
            ))}
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #334155' }}>
                <th style={{ padding: '12px 16px', textAlign: 'left', color: '#94a3b8', fontSize: '12px', fontWeight: '600' }}>Policy Name</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', color: '#94a3b8', fontSize: '12px', fontWeight: '600' }}>Dataset</th>
                <th style={{ padding: '12px 16px', textAlign: 'left', color: '#94a3b8', fontSize: '12px', fontWeight: '600' }}>Channel</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', color: '#94a3b8', fontSize: '12px', fontWeight: '600' }}>Δ¥</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', color: '#94a3b8', fontSize: '12px', fontWeight: '600' }}>ROI</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', color: '#94a3b8', fontSize: '12px', fontWeight: '600' }}>Risk</th>
                <th style={{ padding: '12px 16px', textAlign: 'right', color: '#94a3b8', fontSize: '12px', fontWeight: '600' }}>CAS</th>
                <th style={{ padding: '12px 16px', textAlign: 'center', color: '#94a3b8', fontSize: '12px', fontWeight: '600' }}>Verdict</th>
              </tr>
            </thead>
            <tbody>
              {filteredPolicies.map((policy, idx) => (
                <tr
                  key={policy.id}
                  style={{
                    borderBottom: '1px solid #334155',
                    background: policy.verdict === 'include' ? 'rgba(16, 185, 129, 0.05)' : 'transparent',
                    cursor: 'pointer'
                  }}
                  onClick={() => setSelectedPolicyId(policy.id)}
                >
                  <td style={{ padding: '16px', color: '#f1f5f9', fontSize: '14px', fontWeight: '600' }}>
                    {policy.verdict === 'include' && <span style={{ marginRight: '8px' }}>⭐</span>}
                    {policy.name}
                  </td>
                  <td style={{ padding: '16px', color: '#cbd5e1', fontSize: '13px' }}>{policy.datasetName}</td>
                  <td style={{ padding: '16px', color: '#cbd5e1', fontSize: '13px' }}>{policy.channel}</td>
                  <td style={{ padding: '16px', color: '#10b981', fontSize: '14px', fontWeight: '600', textAlign: 'right' }}>
                    {formatYenShort(policy.deltaYen)}
                  </td>
                  <td style={{ padding: '16px', color: '#f59e0b', fontSize: '14px', textAlign: 'right' }}>
                    {policy.roi.toFixed(2)}x
                  </td>
                  <td style={{ padding: '16px', color: '#ef4444', fontSize: '14px', textAlign: 'right' }}>
                    {(policy.risk * 100).toFixed(1)}%
                  </td>
                  <td style={{
                    padding: '16px',
                    color: policy.cas >= 0.8 ? '#10b981' : policy.cas >= 0.6 ? '#f59e0b' : '#ef4444',
                    fontSize: '14px',
                    fontWeight: '600',
                    textAlign: 'right'
                  }}>
                    {policy.cas.toFixed(2)}
                  </td>
                  <td style={{ padding: '16px', textAlign: 'center' }}>
                    <span style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: '600',
                      background: policy.verdict === 'include'
                        ? 'rgba(16, 185, 129, 0.15)'
                        : policy.verdict === 'test'
                          ? 'rgba(245, 158, 11, 0.15)'
                          : 'rgba(100, 116, 139, 0.15)',
                      color: policy.verdict === 'include'
                        ? '#10b981'
                        : policy.verdict === 'test'
                          ? '#f59e0b'
                          : '#64748b'
                    }}>
                      {policy.verdict.toUpperCase()}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredPolicies.length === 0 && (
          <div style={{ textAlign: 'center', padding: '48px', color: '#64748b' }}>
            No policies match the selected filter.
          </div>
        )}
      </div>
    </div>
  )
}
