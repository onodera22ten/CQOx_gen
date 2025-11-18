/**
 * DeltaYenMetricCard Component
 *
 * Δ¥メトリクスカード（Decision Console用）
 */
import React from 'react';

interface DeltaYenMetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'gray';
  trend?: 'up' | 'down' | 'neutral';
  onClick?: () => void;
}

const DeltaYenMetricCard: React.FC<DeltaYenMetricCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  color = 'blue',
  trend,
  onClick
}) => {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200 text-blue-900',
    green: 'bg-green-50 border-green-200 text-green-900',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-900',
    red: 'bg-red-50 border-red-200 text-red-900',
    gray: 'bg-gray-50 border-gray-200 text-gray-900'
  };

  const trendIcons = {
    up: '↗️',
    down: '↘️',
    neutral: '➡️'
  };

  return (
    <div
      className={`rounded-lg border-2 p-4 ${colorClasses[color]} ${onClick ? 'cursor-pointer hover:shadow-md transition-shadow' : ''}`}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-sm font-medium text-gray-600">{title}</h3>
        {icon && <div className="text-2xl">{icon}</div>}
      </div>

      {/* Value */}
      <div className="flex items-baseline gap-2 mb-1">
        <span className="text-3xl font-bold">{value}</span>
        {trend && <span className="text-xl">{trendIcons[trend]}</span>}
      </div>

      {/* Subtitle */}
      {subtitle && (
        <p className="text-xs text-gray-500">{subtitle}</p>
      )}
    </div>
  );
};

export default DeltaYenMetricCard;
