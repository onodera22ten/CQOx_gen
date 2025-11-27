/**
 * Decision Summary Card Component
 *
 * Displays the key decision/verdict at the top of each page
 * "グラフは根拠、ファーストビューは Decision"
 */
import React from 'react';
import { formatYenShort, formatYenMan } from '../utils/format';

export type Verdict = 'Go' | 'Canary' | 'Hold' | 'Pass' | 'Warning' | 'Fail';

export interface DecisionSummaryCardProps {
  title: string;
  verdict: Verdict;
  deltaYen?: number;
  deltaYenCiLow?: number;
  deltaYenCiHigh?: number;
  casScore?: number;
  riskScore?: number;
  roi?: number;
  reason?: string;
  recommendations?: string[];
  onViewDetails?: () => void;
  detailsLoading?: boolean;
}

const verdictConfig: Record<Verdict, { color: string; bgColor: string; label: string }> = {
  Go: { color: '#10b981', bgColor: 'rgba(16, 185, 129, 0.1)', label: '✓ GO' },
  Canary: { color: '#f59e0b', bgColor: 'rgba(245, 158, 11, 0.1)', label: '⚠ CANARY' },
  Hold: { color: '#ef4444', bgColor: 'rgba(239, 68, 68, 0.1)', label: '✗ HOLD' },
  Pass: { color: '#10b981', bgColor: 'rgba(16, 185, 129, 0.1)', label: '✓ PASS' },
  Warning: { color: '#f59e0b', bgColor: 'rgba(245, 158, 11, 0.1)', label: '⚠ WARNING' },
  Fail: { color: '#ef4444', bgColor: 'rgba(239, 68, 68, 0.1)', label: '✗ FAIL' },
};

export const DecisionSummaryCard: React.FC<DecisionSummaryCardProps> = ({
  title,
  verdict,
  deltaYen,
  deltaYenCiLow,
  deltaYenCiHigh,
  casScore,
  riskScore,
  roi,
  reason,
  recommendations,
  onViewDetails,
  detailsLoading,
}) => {
  const config = verdictConfig[verdict];

  return (
    <div
      style={{
        background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
        border: `2px solid ${config.color}`,
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '24px',
        boxShadow: `0 4px 16px ${config.color}33`,
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h2 style={{ margin: 0, color: '#f1f5f9', fontSize: '20px', fontWeight: '600' }}>
          {title}
        </h2>
        <div
          style={{
            background: config.bgColor,
            color: config.color,
            padding: '8px 20px',
            borderRadius: '24px',
            fontWeight: '700',
            fontSize: '16px',
            border: `2px solid ${config.color}`,
          }}
        >
          {config.label}
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', marginBottom: '16px' }}>
        {deltaYen !== undefined && (
          <div>
            <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Expected Δ¥
            </div>
            <div style={{ color: '#f1f5f9', fontSize: '28px', fontWeight: '700' }}>
              {deltaYen >= 0 ? '+' : ''}{formatYenShort(deltaYen)}
            </div>
            <div style={{ color: '#94a3b8', fontSize: '11px', marginTop: '4px' }}>
              {formatYenMan(deltaYen)}
            </div>
            {deltaYenCiLow !== undefined && deltaYenCiHigh !== undefined && (
              <div style={{ color: '#cbd5e1', fontSize: '11px', marginTop: '4px' }}>
                95% CI: [{formatYenShort(deltaYenCiLow)}, {formatYenShort(deltaYenCiHigh)}]
              </div>
            )}
          </div>
        )}

        {casScore !== undefined && (
          <div>
            <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              CAS Score
            </div>
            <div style={{ color: casScore >= 0.8 ? '#10b981' : casScore >= 0.6 ? '#f59e0b' : '#ef4444', fontSize: '28px', fontWeight: '700' }}>
              {casScore.toFixed(2)}
            </div>
            <div style={{ color: '#cbd5e1', fontSize: '11px', marginTop: '4px' }}>
              {casScore >= 0.8 ? 'High Confidence' : casScore >= 0.6 ? 'Moderate' : 'Low Confidence'}
            </div>
          </div>
        )}

        {riskScore !== undefined && (
          <div>
            <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Risk Score
            </div>
            <div style={{ color: riskScore <= 0.3 ? '#10b981' : riskScore <= 0.6 ? '#f59e0b' : '#ef4444', fontSize: '28px', fontWeight: '700' }}>
              {riskScore.toFixed(2)}
            </div>
            <div style={{ color: '#cbd5e1', fontSize: '11px', marginTop: '4px' }}>
              {riskScore <= 0.3 ? 'Low Risk' : riskScore <= 0.6 ? 'Medium Risk' : 'High Risk'}
            </div>
          </div>
        )}

        {roi !== undefined && (
          <div>
            <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              ROI
            </div>
            <div style={{ color: '#f1f5f9', fontSize: '28px', fontWeight: '700' }}>
              {roi.toFixed(1)}x
            </div>
            <div style={{ color: '#cbd5e1', fontSize: '11px', marginTop: '4px' }}>
              Return on Investment
            </div>
          </div>
        )}
      </div>

      {/* Reason */}
      {reason && (
        <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', borderLeft: `4px solid ${config.color}` }}>
          <div style={{ color: '#94a3b8', fontSize: '11px', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Decision Rationale
          </div>
          <div style={{ color: '#e2e8f0', fontSize: '14px', lineHeight: '1.6' }}>
            {reason}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {recommendations && recommendations.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <div style={{ color: '#94a3b8', fontSize: '11px', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Recommendations
          </div>
          <ul style={{ margin: 0, paddingLeft: '20px', color: '#cbd5e1', fontSize: '13px', lineHeight: '1.8' }}>
            {recommendations.map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      {/* View Details Button */}
      {onViewDetails && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
          <button
            onClick={onViewDetails}
            style={{
              background: config.color,
              color: '#ffffff',
              padding: '10px 24px',
              borderRadius: '6px',
              border: 'none',
              fontWeight: '600',
              cursor: 'pointer',
              fontSize: '14px',
              transition: 'opacity 0.2s',
              opacity: detailsLoading ? 0.6 : 1,
            }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.8')}
            onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
            disabled={detailsLoading}
          >
            {detailsLoading ? 'Loading…' : 'View Detailed Diagnostics →'}
          </button>
        </div>
      )}
    </div>
  );
};

export default DecisionSummaryCard;
