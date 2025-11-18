/**
 * Context Bar Component
 *
 * Displays the current analysis context across all pages:
 * - Dataset information
 * - Policy/Scenario being analyzed
 * - Target metrics
 * - Run/Job ID
 */
import React from 'react';

export interface ContextBarProps {
  dataset?: {
    name: string;
    version?: string;
    updated_at?: string;
    row_count?: number;
  };
  scenario?: {
    id: string;
    name: string;
    type?: string;
  };
  policy?: {
    id: string;
    name: string;
  };
  targetMetric?: {
    outcome: string;
    horizon?: string;
  };
  runId?: string;
  jobId?: string;
}

export const ContextBar: React.FC<ContextBarProps> = ({
  dataset,
  scenario,
  policy,
  targetMetric,
  runId,
  jobId,
}) => {
  return (
    <div
      style={{
        background: 'linear-gradient(135deg, #1e3a5f 0%, #2d4a6f 100%)',
        borderBottom: '1px solid #334155',
        padding: '12px 24px',
        marginBottom: '24px',
        borderRadius: '8px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
      }}
    >
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '16px',
          fontSize: '13px',
        }}
      >
        {/* Dataset Info */}
        {dataset && (
          <div>
            <div style={{ color: '#94a3b8', fontSize: '11px', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Dataset
            </div>
            <div style={{ color: '#f1f5f9', fontWeight: '600' }}>
              {dataset.name}
            </div>
            <div style={{ color: '#cbd5e1', fontSize: '11px', marginTop: '2px' }}>
              {dataset.version && `v${dataset.version}`}
              {dataset.row_count && ` • ${dataset.row_count.toLocaleString()} rows`}
              {dataset.updated_at && ` • ${new Date(dataset.updated_at).toLocaleDateString()}`}
            </div>
          </div>
        )}

        {/* Scenario/Policy Info */}
        {(scenario || policy) && (
          <div>
            <div style={{ color: '#94a3b8', fontSize: '11px', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              {scenario ? 'Scenario' : 'Policy'}
            </div>
            <div style={{ color: '#f1f5f9', fontWeight: '600' }}>
              {scenario?.name || policy?.name}
            </div>
            <div style={{ color: '#cbd5e1', fontSize: '11px', marginTop: '2px' }}>
              ID: {scenario?.id || policy?.id}
              {scenario?.type && ` • Type: ${scenario.type}`}
            </div>
          </div>
        )}

        {/* Target Metric */}
        {targetMetric && (
          <div>
            <div style={{ color: '#94a3b8', fontSize: '11px', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Target Metric
            </div>
            <div style={{ color: '#f1f5f9', fontWeight: '600' }}>
              y = {targetMetric.outcome}
            </div>
            {targetMetric.horizon && (
              <div style={{ color: '#cbd5e1', fontSize: '11px', marginTop: '2px' }}>
                Horizon: {targetMetric.horizon}
              </div>
            )}
          </div>
        )}

        {/* Run/Job ID */}
        {(runId || jobId) && (
          <div>
            <div style={{ color: '#94a3b8', fontSize: '11px', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Run Info
            </div>
            {runId && (
              <div style={{ color: '#f1f5f9', fontSize: '11px', fontFamily: 'monospace' }}>
                Run: {runId}
              </div>
            )}
            {jobId && (
              <div style={{ color: '#cbd5e1', fontSize: '11px', fontFamily: 'monospace', marginTop: '2px' }}>
                Job: {jobId}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ContextBar;
