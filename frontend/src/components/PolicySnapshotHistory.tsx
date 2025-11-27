/**
 * 【日本語サマリ】このモジュールはポリシー推奨の履歴スナップショットを表示する。
 * - なぜ必要か: 過去の意思決定を振り返り、時系列でポリシー推奨の変化を追跡するため
 * - 何をするか: タイムライン形式で過去のanalysis結果とポリシー推奨を表示
 * - どう検証するか: スナップショット選択で、その時点の詳細データが復元表示されることを確認
 */

import React, { useState } from 'react'
import { formatYenShort } from '../utils/format'

export interface PolicySnapshot {
  id: string
  timestamp: string
  analysis_id: string
  policy_name: string
  delta_yen: number
  cas_score: number
  risk_score: number
  verdict: 'Go' | 'Canary' | 'Hold'
  description?: string
}

interface PolicySnapshotHistoryProps {
  snapshots: PolicySnapshot[]
  onSelectSnapshot: (snapshot: PolicySnapshot) => void
  selectedSnapshotId?: string
}

export const PolicySnapshotHistory: React.FC<PolicySnapshotHistoryProps> = ({
  snapshots,
  onSelectSnapshot,
  selectedSnapshotId,
}) => {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const getVerdictColor = (verdict: string) => {
    switch (verdict) {
      case 'Go':
        return '#10b981'
      case 'Canary':
        return '#f59e0b'
      case 'Hold':
        return '#ef4444'
      default:
        return '#94a3b8'
    }
  }

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (snapshots.length === 0) {
    return (
      <div
        style={{
          background: '#1e293b',
          borderRadius: '12px',
          padding: '32px',
          border: '1px solid #334155',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>📊</div>
        <div style={{ fontSize: '18px', fontWeight: '600', color: '#fff', marginBottom: '8px' }}>
          No Snapshots Available
        </div>
        <div style={{ fontSize: '14px', color: '#94a3b8' }}>
          Policy recommendations will be saved as snapshots when analyses complete.
        </div>
      </div>
    )
  }

  return (
    <div
      style={{
        background: '#1e293b',
        borderRadius: '12px',
        padding: '24px',
        border: '1px solid #334155',
      }}
    >
      <div style={{ marginBottom: '20px' }}>
        <h3
          style={{
            fontSize: '18px',
            fontWeight: '600',
            color: '#fff',
            marginBottom: '8px',
          }}
        >
          📈 Policy Recommendation History
        </h3>
        <p style={{ fontSize: '13px', color: '#94a3b8' }}>
          Timeline of past policy recommendations and decisions
        </p>
      </div>

      {/* Timeline */}
      <div style={{ position: 'relative', paddingLeft: '32px' }}>
        {/* Vertical Line */}
        <div
          style={{
            position: 'absolute',
            left: '12px',
            top: '8px',
            bottom: '8px',
            width: '2px',
            background: 'linear-gradient(180deg, #3b82f6 0%, #8b5cf6 100%)',
          }}
        />

        {/* Snapshot Items */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {snapshots.map((snapshot, index) => {
            const isSelected = selectedSnapshotId === snapshot.id
            const isExpanded = expandedId === snapshot.id

            return (
              <div
                key={snapshot.id}
                style={{
                  position: 'relative',
                  background: isSelected ? 'rgba(59, 130, 246, 0.1)' : '#0f172a',
                  border: isSelected
                    ? '2px solid #3b82f6'
                    : '1px solid #334155',
                  borderRadius: '12px',
                  padding: '16px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onClick={() => onSelectSnapshot(snapshot)}
                onMouseEnter={() => setExpandedId(snapshot.id)}
                onMouseLeave={() => setExpandedId(null)}
              >
                {/* Timeline Dot */}
                <div
                  style={{
                    position: 'absolute',
                    left: '-27px',
                    top: '20px',
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    background: getVerdictColor(snapshot.verdict),
                    border: '3px solid #1e293b',
                    boxShadow: `0 0 0 2px ${getVerdictColor(snapshot.verdict)}`,
                  }}
                />

                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '12px' }}>
                  <div>
                    <div style={{ fontSize: '16px', fontWeight: '600', color: '#fff', marginBottom: '4px' }}>
                      {snapshot.policy_name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                      {formatDate(snapshot.timestamp)}
                    </div>
                  </div>
                  <div
                    style={{
                      padding: '4px 12px',
                      background: `${getVerdictColor(snapshot.verdict)}20`,
                      border: `1px solid ${getVerdictColor(snapshot.verdict)}`,
                      borderRadius: '12px',
                      fontSize: '12px',
                      fontWeight: '600',
                      color: getVerdictColor(snapshot.verdict),
                    }}
                  >
                    {snapshot.verdict}
                  </div>
                </div>

                {/* Metrics Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginBottom: '12px' }}>
                  <div>
                    <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>
                      Δ¥
                    </div>
                    <div
                      style={{
                        fontSize: '16px',
                        fontWeight: '700',
                        color: snapshot.delta_yen >= 0 ? '#10b981' : '#ef4444',
                      }}
                    >
                      {formatYenShort(snapshot.delta_yen)}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>
                      CAS Score
                    </div>
                    <div
                      style={{
                        fontSize: '16px',
                        fontWeight: '700',
                        color: snapshot.cas_score >= 0.8 ? '#10b981' : snapshot.cas_score >= 0.6 ? '#f59e0b' : '#ef4444',
                      }}
                    >
                      {snapshot.cas_score.toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px' }}>
                      Risk
                    </div>
                    <div
                      style={{
                        fontSize: '16px',
                        fontWeight: '700',
                        color: snapshot.risk_score <= 0.15 ? '#10b981' : snapshot.risk_score <= 0.25 ? '#f59e0b' : '#ef4444',
                      }}
                    >
                      {(snapshot.risk_score * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                {/* Description (expanded) */}
                {isExpanded && snapshot.description && (
                  <div
                    style={{
                      marginTop: '12px',
                      paddingTop: '12px',
                      borderTop: '1px solid #334155',
                      fontSize: '13px',
                      color: '#cbd5e1',
                    }}
                  >
                    {snapshot.description}
                  </div>
                )}

                {/* Analysis ID */}
                <div style={{ marginTop: '8px', fontSize: '11px', color: '#64748b', fontFamily: 'monospace' }}>
                  Analysis: {snapshot.analysis_id.slice(0, 8)}...
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Summary Stats */}
      <div
        style={{
          marginTop: '24px',
          padding: '16px',
          background: 'rgba(139, 92, 246, 0.1)',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '8px',
        }}
      >
        <div style={{ fontSize: '12px', color: '#a78bfa', fontWeight: '600', marginBottom: '8px' }}>
          Summary Statistics
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', fontSize: '13px', color: '#cbd5e1' }}>
          <div>
            <span style={{ color: '#94a3b8' }}>Total Snapshots:</span>{' '}
            <span style={{ fontWeight: '600' }}>{snapshots.length}</span>
          </div>
          <div>
            <span style={{ color: '#94a3b8' }}>Go Decisions:</span>{' '}
            <span style={{ fontWeight: '600', color: '#10b981' }}>
              {snapshots.filter((s) => s.verdict === 'Go').length}
            </span>
          </div>
          <div>
            <span style={{ color: '#94a3b8' }}>Avg Δ¥:</span>{' '}
            <span style={{ fontWeight: '600', color: '#3b82f6' }}>
              {formatYenShort(
                snapshots.reduce((sum, s) => sum + s.delta_yen, 0) / snapshots.length
              )}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

