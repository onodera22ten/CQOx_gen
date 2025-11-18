import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { policiesAPI } from '../api/v1/policies'
import { ContextBar } from '../components/ContextBar'
import { getCASQualityBadge, CAS_THRESHOLDS } from '../utils/casQuality'

/**
 * Policy-as-Code Export Gate
 * YAML/JSONファイル管理とCI/CD統合用エクスポート
 */

interface ExportConfig {
  format: 'yaml' | 'json'
  includeMetadata: boolean
  includeResults: boolean
  includeDiagnostics: boolean
  minifyJson: boolean
  targetEnv: 'staging' | 'production'
  targetSystem: 'karte' | 'braze' | 'in-house'
}

interface ExportHistory {
  id: string
  policy_id: string
  policy_name: string
  format: string
  exported_at: string
  exported_by: string
  file_size: number
  download_count: number
}

export default function PolicyExportGate() {
  const queryClient = useQueryClient()
  const [selectedPolicies, setSelectedPolicies] = useState<string[]>([])
  const [exportConfig, setExportConfig] = useState<ExportConfig>({
    format: 'yaml',
    includeMetadata: true,
    includeResults: false,
    includeDiagnostics: false,
    minifyJson: false,
    targetEnv: 'staging',
    targetSystem: 'in-house'
  })
  const [showPreview, setShowPreview] = useState(false)
  const [previewContent, setPreviewContent] = useState('')

  // Mock CAS scores for quality gates
  const policyCAS: Record<string, number> = {
    'pol-1': 0.92,
    'pol-2': 0.75,
    'pol-3': 0.88,
    'pol-4': 0.55,
  }

  // CASスコアから品質バッジを取得（統一ユーティリティを使用）
  const getQualityBadge = (policyId: string) => {
    const cas = policyCAS[policyId] || 0.5
    return getCASQualityBadge(cas)
  }

  // Fetch policies
  const { data: policies = [], isLoading } = useQuery({
    queryKey: ['policies'],
    queryFn: () => policiesAPI.list()
  })

  // Mock export history
  const exportHistory: ExportHistory[] = [
    {
      id: 'export-1',
      policy_id: 'pol-1',
      policy_name: 'High-Value Marketing',
      format: 'yaml',
      exported_at: '2025-01-15T10:30:00Z',
      exported_by: 'user@example.com',
      file_size: 2048,
      download_count: 5
    },
    {
      id: 'export-2',
      policy_id: 'pol-2',
      policy_name: 'Retention Campaign',
      format: 'json',
      exported_at: '2025-01-14T14:20:00Z',
      exported_by: 'admin@example.com',
      file_size: 3072,
      download_count: 3
    }
  ]

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: async (params: { policy_ids: string[], config: ExportConfig }) => {
      // Mock export - in production this would call backend API
      const selectedPols = policies.filter(p => params.policy_ids.includes(p.id))

      const exportData = selectedPols.map(policy => {
        const base = {
          apiVersion: 'cqox.ai/v1',
          kind: 'Policy',
          metadata: {
            name: policy.name,
            id: policy.id,
            created_at: policy.created_at,
            dataset_id: policy.dataset_id
          },
          spec: {
            target_rule: policy.target_rule || 'uplift_score > threshold',
            offer_config: policy.offer_config || {},
            channels: policy.channels || [],
            frequency_cap: policy.frequency_cap,
            budget_limit: policy.budget_limit,
            objectives: policy.objectives || {},
            risk_constraints: policy.risk_constraints || {}
          }
        }

        if (!params.config.includeMetadata) {
          delete (base as any).metadata.created_at
          delete (base as any).metadata.dataset_id
        }

        if (params.config.includeResults) {
          (base as any).status = {
            phase: policy.status,
            results: {
              estimated_profit: 150000,
              roi: 3.2,
              coverage: 0.35
            }
          }
        }

        if (params.config.includeDiagnostics) {
          (base as any).diagnostics = {
            cas_score: 0.85,
            quality_level: 'HIGH',
            checks_passed: 13,
            checks_total: 14
          }
        }

        return base
      })

      // Generate preview
      if (params.config.format === 'yaml') {
        const yamlContent = exportData.map(policy => {
          const lines = [`---`]
          lines.push(`apiVersion: ${policy.apiVersion}`)
          lines.push(`kind: ${policy.kind}`)
          lines.push(`metadata:`)
          lines.push(`  name: "${policy.metadata.name}"`)
          lines.push(`  id: "${policy.metadata.id}"`)
          if ((policy.metadata as any).created_at) {
            lines.push(`  created_at: "${(policy.metadata as any).created_at}"`)
          }
          lines.push(`spec:`)
          lines.push(`  target_rule: "${policy.spec.target_rule}"`)
          lines.push(`  channels: [${policy.spec.channels.join(', ')}]`)
          if (policy.spec.budget_limit) {
            lines.push(`  budget_limit: ${policy.spec.budget_limit}`)
          }
          if ((policy as any).status) {
            lines.push(`status:`)
            lines.push(`  phase: ${(policy as any).status.phase}`)
            lines.push(`  results:`)
            lines.push(`    estimated_profit: ${(policy as any).status.results.estimated_profit}`)
            lines.push(`    roi: ${(policy as any).status.results.roi}`)
          }
          return lines.join('\n')
        }).join('\n\n')
        return { content: yamlContent, filename: `policies-export-${Date.now()}.yaml` }
      } else {
        const jsonContent = params.config.minifyJson
          ? JSON.stringify(exportData)
          : JSON.stringify(exportData, null, 2)
        return { content: jsonContent, filename: `policies-export-${Date.now()}.json` }
      }
    },
    onSuccess: (data) => {
      setPreviewContent(data.content)
      setShowPreview(true)
      queryClient.invalidateQueries({ queryKey: ['export-history'] })
    }
  })

  // Download exported file
  const handleDownload = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  // Handle export
  const handleExport = () => {
    if (selectedPolicies.length === 0) {
      alert('Please select at least one policy to export')
      return
    }

    exportMutation.mutate({
      policy_ids: selectedPolicies,
      config: exportConfig
    })
  }

  if (isLoading) {
    return (
      <div style={{ padding: '32px', color: '#cbd5e0', textAlign: 'center' }}>
        Loading policies...
      </div>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px' }}>
        Policy-as-Code Export Gate
      </h1>

      {/* Context Bar */}
      <ContextBar
        scenario={{
          id: 'policy-export',
          name: `Export to ${exportConfig.targetEnv} (${exportConfig.targetSystem})`,
          type: 'Policy-as-Code Deployment',
        }}
        targetMetric={{
          outcome: `${selectedPolicies.length} policies selected`,
        }}
      />

      {/* Source Information Bar */}
      <div style={{
        padding: '16px',
        background: 'rgba(59, 130, 246, 0.1)',
        border: '1px solid rgba(59, 130, 246, 0.3)',
        borderRadius: '12px',
        marginBottom: '24px',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px'
      }}>
        <div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px', fontWeight: '600' }}>📊 SOURCE</div>
          <div style={{ fontSize: '14px', color: '#f1f5f9', fontWeight: '600' }}>Portfolio Optimization</div>
          <div style={{ fontSize: '12px', color: '#3b82f6', fontFamily: 'monospace' }}>analysis_NR1</div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px', fontWeight: '600' }}>📅 ANALYZED</div>
          <div style={{ fontSize: '14px', color: '#f1f5f9' }}>2025-01-18 15:30</div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>~2 hours ago</div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px', fontWeight: '600' }}>✓ QUALITY GATE</div>
          <div style={{ fontSize: '14px', color: '#10b981', fontWeight: '600' }}>All Policies Passed</div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>Min CAS: {CAS_THRESHOLDS.EXPORT_MINIMUM}</div>
        </div>
        <div>
          <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '4px', fontWeight: '600' }}>💰 EXPECTED Δ¥</div>
          <div style={{ fontSize: '14px', color: '#10b981', fontWeight: '700' }}>+¥5.2M</div>
          <div style={{ fontSize: '12px', color: '#94a3b8' }}>Portfolio Total</div>
        </div>
      </div>

      <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '24px' }}>
        Export policies as {exportConfig.format.toUpperCase()} files for version control and CI/CD integration
      </p>

      <div style={{ display: 'grid', gridTemplateColumns: showPreview ? '1fr 1fr' : '1fr', gap: '24px' }}>
        <div>
          {/* Export Environment Configuration */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-title">🎯 Export Destination</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', color: '#94a3b8', fontSize: '13px', marginBottom: '8px' }}>
                  Target Environment
                </label>
                <select
                  value={exportConfig.targetEnv}
                  onChange={(e) => setExportConfig({ ...exportConfig, targetEnv: e.target.value as any })}
                  style={{
                    width: '100%',
                    padding: '10px',
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    color: '#f1f5f9',
                    fontSize: '14px',
                  }}
                >
                  <option value="staging">Staging</option>
                  <option value="production">Production</option>
                </select>
              </div>
              <div>
                <label style={{ display: 'block', color: '#94a3b8', fontSize: '13px', marginBottom: '8px' }}>
                  Target System
                </label>
                <select
                  value={exportConfig.targetSystem}
                  onChange={(e) => setExportConfig({ ...exportConfig, targetSystem: e.target.value as any })}
                  style={{
                    width: '100%',
                    padding: '10px',
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    color: '#f1f5f9',
                    fontSize: '14px',
                  }}
                >
                  <option value="karte">KARTE</option>
                  <option value="braze">Braze</option>
                  <option value="in-house">In-House System</option>
                </select>
              </div>
            </div>
          </div>

          {/* Policy Selection */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-title">Select Policies to Export</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <button
                onClick={() => setSelectedPolicies(policies.map(p => p.id))}
                style={{
                  padding: '6px 12px',
                  background: '#334155',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#cbd5e1',
                  fontSize: '13px',
                  fontWeight: '500',
                  cursor: 'pointer'
                }}
              >
                Select All
              </button>
              <button
                onClick={() => setSelectedPolicies([])}
                style={{
                  padding: '6px 12px',
                  background: '#334155',
                  border: 'none',
                  borderRadius: '6px',
                  color: '#cbd5e1',
                  fontSize: '13px',
                  fontWeight: '500',
                  cursor: 'pointer'
                }}
              >
                Clear All
              </button>
              <div style={{ marginLeft: 'auto', color: '#94a3b8', fontSize: '14px' }}>
                {selectedPolicies.length} / {policies.length} selected
              </div>
            </div>

            <div style={{ display: 'grid', gap: '12px', maxHeight: '400px', overflowY: 'auto' }}>
              {policies.map(policy => {
                const qualityBadge = getQualityBadge(policy.id)
                const cas = policyCAS[policy.id] || 0.5

                return (
                  <div
                    key={policy.id}
                    onClick={() => {
                      if (!qualityBadge.canExport && !selectedPolicies.includes(policy.id)) {
                        alert(`❌ Cannot export policy "${policy.name}"\nCAS Score (${cas.toFixed(2)}) is below minimum threshold (0.6)\n\nPlease review diagnostics and improve causal quality before exporting.`)
                        return
                      }
                      setSelectedPolicies(prev =>
                        prev.includes(policy.id)
                          ? prev.filter(id => id !== policy.id)
                          : [...prev, policy.id]
                      )
                    }}
                    style={{
                      padding: '12px 16px',
                      background: selectedPolicies.includes(policy.id) ? 'rgba(59, 130, 246, 0.2)' : '#0f172a',
                      border: `2px solid ${selectedPolicies.includes(policy.id) ? '#3b82f6' : qualityBadge.canExport ? '#1e293b' : '#ef4444'}`,
                      borderRadius: '8px',
                      cursor: qualityBadge.canExport ? 'pointer' : 'not-allowed',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      transition: 'all 0.2s',
                      opacity: qualityBadge.canExport ? 1 : 0.6
                    }}
                  >
                    <div
                      style={{
                        width: '20px',
                        height: '20px',
                        borderRadius: '4px',
                        background: selectedPolicies.includes(policy.id) ? '#3b82f6' : qualityBadge.canExport ? '#334155' : '#64748b',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '14px',
                        color: '#fff'
                      }}
                    >
                      {selectedPolicies.includes(policy.id) ? '✓' : !qualityBadge.canExport ? '⚠' : ''}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <span style={{ fontWeight: '600', color: '#f1f5f9', fontSize: '14px' }}>
                          {policy.name}
                        </span>
                        <div
                          style={{
                            padding: '2px 8px',
                            background: `${qualityBadge.color}22`,
                            border: `1px solid ${qualityBadge.color}`,
                            borderRadius: '4px',
                            fontSize: '10px',
                            fontWeight: '700',
                            color: qualityBadge.color,
                            textTransform: 'uppercase',
                            letterSpacing: '0.5px'
                          }}
                        >
                          Quality: {qualityBadge.label}
                        </div>
                        <div style={{ fontSize: '11px', color: '#94a3b8' }}>
                          CAS: {cas.toFixed(2)}
                        </div>
                      </div>
                      <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                        Status: <span style={{ textTransform: 'capitalize' }}>{policy.status}</span> · ID: {policy.id}
                      </div>
                    </div>
                    <div
                      style={{
                        padding: '4px 10px',
                        borderRadius: '12px',
                        fontSize: '11px',
                        fontWeight: '600',
                        background:
                          policy.status === 'completed' ? '#dcfce7' :
                          policy.status === 'running' ? '#dbeafe' :
                          policy.status === 'failed' ? '#fee2e2' : '#f3f4f6',
                        color:
                          policy.status === 'completed' ? '#166534' :
                          policy.status === 'running' ? '#1e3a8a' :
                          policy.status === 'failed' ? '#991b1b' : '#1f2937'
                      }}
                    >
                      {policy.status.toUpperCase()}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Export Configuration */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-title">Export Configuration</div>

            {/* Format Selection */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', color: '#cbd5e1', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
                Export Format
              </label>
              <div style={{ display: 'flex', gap: '12px' }}>
                <button
                  onClick={() => setExportConfig(prev => ({ ...prev, format: 'yaml' }))}
                  style={{
                    flex: 1,
                    padding: '10px 16px',
                    background: exportConfig.format === 'yaml' ? '#3b82f6' : '#1e293b',
                    border: `2px solid ${exportConfig.format === 'yaml' ? '#3b82f6' : '#334155'}`,
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  📄 YAML
                </button>
                <button
                  onClick={() => setExportConfig(prev => ({ ...prev, format: 'json' }))}
                  style={{
                    flex: 1,
                    padding: '10px 16px',
                    background: exportConfig.format === 'json' ? '#3b82f6' : '#1e293b',
                    border: `2px solid ${exportConfig.format === 'json' ? '#3b82f6' : '#334155'}`,
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '14px',
                    fontWeight: '600',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  🗂️ JSON
                </button>
              </div>
            </div>

            {/* Export Options */}
            <div style={{ display: 'grid', gap: '12px' }}>
              {[
                { key: 'includeMetadata', label: 'Include Full Metadata', desc: 'Export creation timestamps, dataset IDs, etc.' },
                { key: 'includeResults', label: 'Include Evaluation Results', desc: 'Export estimated profit, ROI, and coverage metrics' },
                { key: 'includeDiagnostics', label: 'Include Diagnostic Scores', desc: 'Export CAS score and quality assessments' },
                ...(exportConfig.format === 'json' ? [{ key: 'minifyJson', label: 'Minify JSON', desc: 'Remove whitespace for smaller file size' }] : [])
              ].map(option => (
                <label
                  key={option.key}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '12px',
                    background: '#0f172a',
                    borderRadius: '8px',
                    cursor: 'pointer'
                  }}
                >
                  <input
                    type="checkbox"
                    checked={exportConfig[option.key as keyof ExportConfig] as boolean}
                    onChange={e => setExportConfig(prev => ({ ...prev, [option.key]: e.target.checked }))}
                    style={{
                      marginTop: '2px',
                      width: '18px',
                      height: '18px',
                      cursor: 'pointer'
                    }}
                  />
                  <div style={{ flex: 1 }}>
                    <div style={{ color: '#f1f5f9', fontSize: '14px', fontWeight: '500', marginBottom: '2px' }}>
                      {option.label}
                    </div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                      {option.desc}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Export Actions */}
          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={handleExport}
              disabled={exportMutation.isPending || selectedPolicies.length === 0}
              style={{
                flex: 1,
                padding: '14px 24px',
                background: exportMutation.isPending || selectedPolicies.length === 0
                  ? '#64748b'
                  : 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                border: 'none',
                borderRadius: '8px',
                color: '#fff',
                fontSize: '16px',
                fontWeight: '600',
                cursor: exportMutation.isPending || selectedPolicies.length === 0 ? 'not-allowed' : 'pointer',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
              }}
            >
              {exportMutation.isPending ? 'Generating...' : '📤 Generate Export'}
            </button>
            {showPreview && (
              <button
                onClick={() => handleDownload(
                  previewContent,
                  `policies-export-${Date.now()}.${exportConfig.format}`
                )}
                style={{
                  padding: '14px 24px',
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                }}
              >
                💾 Download
              </button>
            )}
          </div>
        </div>

        {/* Preview Panel */}
        {showPreview && (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div className="card-title" style={{ marginBottom: 0 }}>
                📄 Export Preview - {exportConfig.format.toUpperCase()}
              </div>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(previewContent)
                  alert('✓ Copied to clipboard!')
                }}
                style={{
                  padding: '8px 16px',
                  background: 'rgba(59, 130, 246, 0.2)',
                  border: '1px solid #3b82f6',
                  borderRadius: '6px',
                  color: '#3b82f6',
                  fontSize: '13px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                📋 Copy
              </button>
            </div>

            <div
              style={{
                background: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '8px',
                padding: '0',
                fontFamily: 'monospace',
                fontSize: '13px',
                lineHeight: '1.6',
                color: '#cbd5e1',
                overflowX: 'auto',
                maxHeight: '600px',
                overflowY: 'auto',
                position: 'relative'
              }}
            >
              {/* Line numbers & content */}
              <div style={{ display: 'flex' }}>
                {/* Line numbers */}
                <div
                  style={{
                    background: '#1e293b',
                    borderRight: '1px solid #334155',
                    padding: '16px 12px',
                    color: '#64748b',
                    fontSize: '12px',
                    textAlign: 'right',
                    userSelect: 'none',
                    minWidth: '50px'
                  }}
                >
                  {previewContent.split('\n').map((_, i) => (
                    <div key={i} style={{ lineHeight: '1.6' }}>{i + 1}</div>
                  ))}
                </div>

                {/* Content */}
                <div style={{ flex: 1, padding: '16px', overflow: 'auto' }}>
                  <pre style={{ margin: 0, whiteSpace: 'pre', color: '#cbd5e1' }}>
                    {previewContent}
                  </pre>
                </div>
              </div>
            </div>

            {/* Preview Info Bar */}
            <div style={{
              marginTop: '12px',
              padding: '12px',
              background: 'rgba(59, 130, 246, 0.1)',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: '6px',
              fontSize: '12px',
              color: '#94a3b8',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', gap: '16px' }}>
                <span>📏 {previewContent.split('\n').length} lines</span>
                <span>💾 {(new Blob([previewContent]).size / 1024).toFixed(2)} KB</span>
                <span>🎯 {selectedPolicies.length} {selectedPolicies.length === 1 ? 'policy' : 'policies'}</span>
              </div>
              <div style={{ color: '#3b82f6', fontWeight: '600' }}>
                Target: {exportConfig.targetEnv.toUpperCase()} ({exportConfig.targetSystem.toUpperCase()})
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Export History */}
      <div className="card" style={{ marginTop: '24px' }}>
        <div className="card-title">Recent Exports</div>
        <table className="table">
          <thead>
            <tr>
              <th>Policy</th>
              <th>Format</th>
              <th>Exported At</th>
              <th>Exported By</th>
              <th>File Size</th>
              <th>Downloads</th>
            </tr>
          </thead>
          <tbody>
            {exportHistory.map(record => (
              <tr key={record.id}>
                <td style={{ fontWeight: '500' }}>{record.policy_name}</td>
                <td>
                  <span
                    style={{
                      padding: '4px 10px',
                      borderRadius: '12px',
                      fontSize: '11px',
                      fontWeight: '600',
                      background: record.format === 'yaml' ? '#dbeafe' : '#dcfce7',
                      color: record.format === 'yaml' ? '#1e3a8a' : '#166534'
                    }}
                  >
                    {record.format.toUpperCase()}
                  </span>
                </td>
                <td style={{ color: '#94a3b8', fontSize: '13px' }}>
                  {new Date(record.exported_at).toLocaleString()}
                </td>
                <td style={{ color: '#94a3b8', fontSize: '13px' }}>{record.exported_by}</td>
                <td style={{ color: '#94a3b8', fontSize: '13px' }}>
                  {(record.file_size / 1024).toFixed(1)} KB
                </td>
                <td style={{ color: '#64748b' }}>{record.download_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* CI/CD Integration Guide */}
      <div className="card" style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', marginTop: '24px' }}>
        <div className="card-title" style={{ color: '#60a5fa' }}>CI/CD Integration Guide</div>
        <p style={{ color: '#cbd5e1', marginBottom: '16px' }}>
          Integrate exported policies into your CI/CD pipeline for automated deployment and version control:
        </p>
        <div style={{ background: '#0f172a', borderRadius: '8px', padding: '16px', fontFamily: 'monospace', fontSize: '13px', color: '#94a3b8' }}>
          <div style={{ marginBottom: '12px' }}>
            <div style={{ color: '#22c55e', marginBottom: '4px' }}># Example GitHub Actions workflow</div>
            <div>name: Deploy CQOx Policies</div>
            <div>on: [push]</div>
            <div>jobs:</div>
            <div>  deploy:</div>
            <div>    steps:</div>
            <div>      - uses: actions/checkout@v2</div>
            <div>      - name: Validate policies</div>
            <div>        run: cqox validate policies/*.yaml</div>
            <div>      - name: Deploy to production</div>
            <div>        run: cqox apply -f policies/</div>
          </div>
        </div>
      </div>
    </div>
  )
}
