/**
 * DecisionCard Component
 *
 * Δ¥ + Go/Canary/Hold判定を表示するカード
 */
import React from 'react';
import { DecisionCard as DecisionCardType } from '../../api/v1/decisions';

interface DecisionCardProps {
  card: DecisionCardType;
  onClick?: () => void;
}

const DecisionCard: React.FC<DecisionCardProps> = ({ card, onClick }) => {
  // verdict色分け
  const getVerdictColor = (verdict: string) => {
    switch (verdict) {
      case 'Go':
        return 'green';
      case 'Canary':
        return 'yellow';
      case 'Hold':
        return 'red';
      default:
        return 'gray';
    }
  };

  const getVerdictBadge = (verdict: string) => {
    const baseClass = 'px-3 py-1 rounded-full text-sm font-semibold';
    switch (verdict) {
      case 'Go':
        return <span className={`${baseClass} bg-green-100 text-green-800`}>🟢 Go - すぐ実施推奨</span>;
      case 'Canary':
        return <span className={`${baseClass} bg-yellow-100 text-yellow-800`}>🟡 Canary - A/Bテスト推奨</span>;
      case 'Hold':
        return <span className={`${baseClass} bg-red-100 text-red-800`}>🔴 Hold - 実施非推奨</span>;
      default:
        return <span className={`${baseClass} bg-gray-100 text-gray-800`}>{verdict}</span>;
    }
  };

  const formatYen = (amount: number) => {
    if (Math.abs(amount) >= 1_000_000) {
      return `¥${(amount / 1_000_000).toFixed(1)}M`;
    } else if (Math.abs(amount) >= 1_000) {
      return `¥${(amount / 1_000).toFixed(0)}K`;
    } else {
      return `¥${amount.toFixed(0)}`;
    }
  };

  const verdictColor = getVerdictColor(card.verdict);
  const borderClass = `border-l-4 border-${verdictColor}-500`;

  return (
    <div
      className={`bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow cursor-pointer ${borderClass}`}
      onClick={onClick}
    >
      {/* Verdict Badge */}
      <div className="flex justify-between items-start mb-3">
        {getVerdictBadge(card.verdict)}
        <span className="text-xs text-gray-500">
          {new Date(card.created_at).toLocaleDateString('ja-JP')}
        </span>
      </div>

      {/* Scenario Name */}
      <h3 className="text-lg font-bold text-gray-900 mb-2">{card.scenario_name}</h3>

      {/* Δ¥ Display */}
      <div className="mb-3">
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-blue-600">
            {card.delta_yen >= 0 ? '+' : ''}{formatYen(card.delta_yen)}
          </span>
          <span className="text-sm text-gray-500">Δ¥</span>
        </div>
        {card.delta_yen_ci_low !== undefined && card.delta_yen_ci_high !== undefined && (
          <div className="text-xs text-gray-500 mt-1">
            ({formatYen(card.delta_yen_ci_low)} 〜 {formatYen(card.delta_yen_ci_high)})
          </div>
        )}
      </div>

      {/* Metadata */}
      <div className="space-y-1 text-sm">
        {card.channel && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500">チャネル:</span>
            <span className="font-medium text-gray-700">{card.channel}</span>
          </div>
        )}
        {card.segment && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500">セグメント:</span>
            <span className="font-medium text-gray-700">{card.segment}</span>
          </div>
        )}
      </div>

      {/* Quality Scores (if available) */}
      {card.quality_scores && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="text-xs text-gray-500 space-y-1">
            {card.quality_scores.overlap_coverage !== undefined && (
              <div>Overlap: {(card.quality_scores.overlap_coverage * 100).toFixed(0)}%</div>
            )}
            {card.quality_scores.iv_f_stat !== undefined && (
              <div>IV F-stat: {card.quality_scores.iv_f_stat.toFixed(1)}</div>
            )}
          </div>
        </div>
      )}

      {/* Reason (for Hold/Canary) */}
      {card.reason && (
        <div className="mt-3 p-2 bg-gray-50 rounded text-xs text-gray-700">
          理由: {card.reason}
        </div>
      )}
    </div>
  );
};

export default DecisionCard;
