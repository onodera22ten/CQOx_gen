/**
 * 可視化カード共通コンポーネント
 * すべての可視化チャートの基盤となるラッパー
 */

import { ReactNode, useState } from 'react';

interface VisualizationCardProps {
  title: string;
  description: string;
  children: ReactNode;
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  metrics?: Array<{ label: string; value: string | number }>;
}

export default function VisualizationCard({
  title,
  description,
  children,
  isLoading = false,
  error = null,
  onRefresh,
  metrics,
}: VisualizationCardProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div
      style={{
        background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        border: '1px solid #334155',
        borderRadius: '12px',
        padding: '24px',
        marginBottom: '24px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
        }}
      >
        <div>
          <h3
            style={{
              margin: 0,
              fontSize: '20px',
              fontWeight: '600',
              color: '#f1f5f9',
            }}
          >
            {title}
          </h3>
          <p
            style={{
              margin: '4px 0 0 0',
              fontSize: '14px',
              color: '#94a3b8',
            }}
          >
            {description}
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              style={{
                padding: '8px 16px',
                background: 'rgba(59, 130, 246, 0.1)',
                border: '1px solid rgba(59, 130, 246, 0.3)',
                borderRadius: '6px',
                color: '#60a5fa',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                fontSize: '14px',
              }}
            >
              {isLoading ? '🔄 Loading...' : '🔄 Refresh'}
            </button>
          )}

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            style={{
              padding: '8px 16px',
              background: 'rgba(100, 116, 139, 0.1)',
              border: '1px solid rgba(100, 116, 139, 0.3)',
              borderRadius: '6px',
              color: '#cbd5e1',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            {isExpanded ? '▼ Collapse' : '▶ Expand'}
          </button>
        </div>
      </div>

      {/* Metrics (if provided) */}
      {metrics && metrics.length > 0 && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '12px',
            marginBottom: '16px',
            padding: '16px',
            background: 'rgba(15, 23, 42, 0.6)',
            borderRadius: '8px',
            border: '1px solid #1e293b',
          }}
        >
          {metrics.map((metric, index) => (
            <div key={index}>
              <div
                style={{
                  fontSize: '12px',
                  color: '#94a3b8',
                  marginBottom: '4px',
                }}
              >
                {metric.label}
              </div>
              <div
                style={{
                  fontSize: '20px',
                  fontWeight: '600',
                  color: '#f1f5f9',
                }}
              >
                {metric.value}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Content */}
      {isExpanded && (
        <div style={{ minHeight: '300px' }}>
          {error ? (
            <div
              style={{
                padding: '24px',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '8px',
                color: '#fca5a5',
                textAlign: 'center',
              }}
            >
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
              <div style={{ fontSize: '16px', fontWeight: '500' }}>
                Error loading visualization
              </div>
              <div style={{ fontSize: '14px', marginTop: '8px', opacity: 0.8 }}>
                {error}
              </div>
            </div>
          ) : isLoading ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: '300px',
                color: '#94a3b8',
              }}
            >
              <div
                style={{
                  fontSize: '48px',
                  marginBottom: '16px',
                  animation: 'spin 2s linear infinite',
                }}
              >
                🔄
              </div>
              <div style={{ fontSize: '16px' }}>Loading visualization...</div>
              <style>{`
                @keyframes spin {
                  from { transform: rotate(0deg); }
                  to { transform: rotate(360deg); }
                }
              `}</style>
            </div>
          ) : (
            children
          )}
        </div>
      )}
    </div>
  );
}
