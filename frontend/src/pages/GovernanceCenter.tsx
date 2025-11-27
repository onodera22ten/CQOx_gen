import { useState, useEffect, ChangeEvent } from 'react'
import { useQuery } from '@tanstack/react-query'
import { governanceAPI, Violation, GovernanceViolationRecord, GovernanceRule } from '../api/v2/governance'
import { datasetsAPI } from '../api/v1/datasets'
import { columnSuggestionsAPI } from '../api/v2/columnSuggestions'

const SAMPLE_DATA = JSON.stringify(
  [
    { user_id: 'u1', delta_yen: 1200, gender: 'male', age_group: '25-34' },
    { user_id: 'u2', delta_yen: 200, gender: 'female', age_group: '25-34' },
    { user_id: 'u3', delta_yen: 50, gender: 'male', age_group: '18-24' },
    { user_id: 'u4', delta_yen: 20, gender: 'female', age_group: '18-24' }
  ],
  null,
  2
)

const SAMPLE_EXPOSURES = JSON.stringify(
  {
    user_001: 12,
    user_002: 3,
    user_003: 8
  },
  null,
  2
)

export default function GovernanceCenter() {
  const [dataPayload, setDataPayload] = useState(SAMPLE_DATA)
  const [sensitiveAttributes, setSensitiveAttributes] = useState('{"gender": ["male", "female"], "age_group": ["25-34", "18-24"]}')
  const [threshold, setThreshold] = useState(1000)
  const [minSamples, setMinSamples] = useState(100)
  const [maxFrequency, setMaxFrequency] = useState(10)
  const [fairnessResult, setFairnessResult] = useState<Violation[]>([])
  const [dqResult, setDqResult] = useState<Violation[]>([])
  const [compliancePayload, setCompliancePayload] = useState(SAMPLE_EXPOSURES)
  const [complianceResult, setComplianceResult] = useState<Violation[]>([])
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null)
  const [sensitiveColumns, setSensitiveColumns] = useState<string[]>([])
  const [autoDetectLoading, setAutoDetectLoading] = useState(false)
  const [showAdvancedSensitive, setShowAdvancedSensitive] = useState(false)

  const { data: violationLog, refetch: refetchLog } = useQuery({
    queryKey: ['governance-violations'],
    queryFn: () => governanceAPI.listViolations()
  })
  const { data: rulesData, isLoading: rulesLoading } = useQuery({
    queryKey: ['governance-rules'],
    queryFn: () => governanceAPI.listRules()
  })
  const { data: datasets } = useQuery({
    queryKey: ['datasets-list'],
    queryFn: () => datasetsAPI.list()
  })
  const { data: datasetColumns } = useQuery({
    queryKey: ['dataset-columns', selectedDatasetId],
    queryFn: () => (selectedDatasetId ? datasetsAPI.getColumns(selectedDatasetId) : null),
    enabled: Boolean(selectedDatasetId)
  })
  const availableColumns = datasetColumns?.columns ?? []

  useEffect(() => {
    if (!selectedDatasetId && datasets && datasets.length > 0) {
      setSelectedDatasetId(datasets[0].id)
    }
  }, [datasets, selectedDatasetId])

  useEffect(() => {
    if (!showAdvancedSensitive) {
      const suggestionObject = sensitiveColumns.reduce<Record<string, string[]>>((acc, column) => {
        acc[column] = []
        return acc
      }, {})
      setSensitiveAttributes(JSON.stringify(suggestionObject, null, 2))
    }
  }, [sensitiveColumns, showAdvancedSensitive])

  const parseJson = <T,>(payload: string): T | null => {
    try {
      const parsed = JSON.parse(payload)
      return parsed
    } catch {
      setErrorMessage('Invalid JSON payload')
      return null
    }
  }

  const handleSensitiveColumnsChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const values = Array.from(event.target.selectedOptions).map((option) => option.value)
    setSensitiveColumns(values)
  }

  const handleAutoDetectColumns = async () => {
    if (!selectedDatasetId) return
    setErrorMessage(null)
    setAutoDetectLoading(true)
    try {
      const response = await columnSuggestionsAPI.fetch(selectedDatasetId)
      const sensitive = response.suggestions['sensitive'] ?? []
      const ordered = [...sensitive].sort((a, b) => b.score - a.score)
      const next = ordered.slice(0, 3).map((s) => s.column)
      setSensitiveColumns(next)
      if (next.length === 0) {
        setErrorMessage('No sensitive attribute candidates detected. Please select columns manually.')
      } else {
        setErrorMessage(null)
      }
    } catch (err) {
      setErrorMessage('Failed to auto-detect columns')
    } finally {
      setAutoDetectLoading(false)
    }
  }

  const handleFairnessCheck = async () => {
    setErrorMessage(null)
    const parsedData = parseJson<Array<Record<string, any>>>(dataPayload)
    const parsedSensitivity = parseJson<Record<string, string[]>>(sensitiveAttributes)
    if (!parsedData || !parsedSensitivity) return

    const result = await governanceAPI.checkFairness({
      data: parsedData,
      sensitive_attributes: parsedSensitivity,
      threshold
    })
    setFairnessResult(result.violations)
  }

  const handleDataQualityCheck = async () => {
    setErrorMessage(null)
    const parsedData = parseJson<Array<Record<string, any>>>(dataPayload)
    if (!parsedData) return
    const result = await governanceAPI.checkDataQuality({ data: parsedData, min_samples: minSamples })
    setDqResult(result.violations)
  }

  const handleComplianceCheck = async () => {
    setErrorMessage(null)
    const parsedPayload = parseJson<Record<string, number>>(compliancePayload)
    if (!parsedPayload) return
    const result = await governanceAPI.checkCompliance({ user_exposures: parsedPayload, max_frequency: maxFrequency })
    setComplianceResult(result.violations)
  }

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <header>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>Governance Center</h1>
        <p style={{ color: '#94a3b8' }}>Monitor fairness, data quality, and compliance risks before releasing policies.</p>
      </header>

      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Data & Sensitivity</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: '12px', marginBottom: '12px' }}>
          <label style={labelStyle}>
            Fairness Threshold (Δ¥)
            <input type="number" value={threshold} onChange={(e) => setThreshold(Number(e.target.value))} style={inputStyle} />
          </label>
          <label style={labelStyle}>
            Min Samples Required
            <input type="number" value={minSamples} onChange={(e) => setMinSamples(Number(e.target.value))} style={inputStyle} />
          </label>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: '12px', marginBottom: '12px' }}>
          <label style={labelStyle}>
            Dataset
            <select value={selectedDatasetId ?? ''} onChange={(e) => setSelectedDatasetId(e.target.value || null)} style={inputStyle}>
              {datasets?.map((dataset) => (
                <option key={dataset.id} value={dataset.id}>
                  {dataset.name || dataset.id}
                </option>
              ))}
              {!datasets?.length && <option value="">No datasets available</option>}
            </select>
          </label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ color: '#cbd5e1', fontSize: '13px' }}>Column Suggestions</span>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <button type="button" onClick={handleAutoDetectColumns} disabled={!selectedDatasetId || autoDetectLoading} style={secondaryButtonStyle}>
                {autoDetectLoading ? 'Detecting…' : 'Detect Columns'}
              </button>
              <button type="button" onClick={() => setShowAdvancedSensitive((prev) => !prev)} style={secondaryButtonStyle}>
                {showAdvancedSensitive ? 'Hide Raw JSON' : 'Show Raw JSON'}
              </button>
            </div>
            <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
              Detect Columns proposes sensitive attributes based on dataset headers (gender, age, region, etc.). Confirm or adjust the selections before running checks.
            </p>
          </div>
        </div>
        {availableColumns.length > 0 && (
          <label style={labelStyle}>
            Sensitive Attributes
            <select multiple value={sensitiveColumns} onChange={handleSensitiveColumnsChange} style={{ ...inputStyle, minHeight: '120px' }}>
              {availableColumns.map((col) => (
                <option key={col} value={col}>
                  {col}
                </option>
              ))}
            </select>
          </label>
        )}
        {showAdvancedSensitive && (
          <label style={labelStyle}>
            Sensitive Attributes JSON
            <textarea value={sensitiveAttributes} onChange={(e) => setSensitiveAttributes(e.target.value)} rows={4} style={textareaStyle} />
          </label>
        )}
        <label style={labelStyle}>
          Uplift Data JSON
          <textarea value={dataPayload} onChange={(e) => setDataPayload(e.target.value)} rows={8} style={textareaStyle} />
        </label>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button onClick={handleFairnessCheck} style={primaryButtonStyle}>Check Fairness</button>
          <button onClick={handleDataQualityCheck} style={secondaryButtonStyle}>Check Data Quality</button>
        </div>
      </section>

      {fairnessResult.length > 0 && (
        <section style={sectionStyle}>
          <h2 style={sectionTitleStyle}>Fairness Violations</h2>
          <ViolationTable violations={fairnessResult} />
        </section>
      )}

      {dqResult.length > 0 && (
        <section style={sectionStyle}>
          <h2 style={sectionTitleStyle}>Data Quality Warnings</h2>
          <ViolationTable violations={dqResult} />
        </section>
      )}

      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Compliance (Frequency Cap)</h2>
        <label style={labelStyle}>
          User Exposure JSON
          <textarea value={compliancePayload} onChange={(e) => setCompliancePayload(e.target.value)} rows={6} style={textareaStyle} />
        </label>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: '12px', margin: '12px 0' }}>
          <label style={labelStyle}>
            Max Frequency Cap
            <input type="number" value={maxFrequency} onChange={(e) => setMaxFrequency(Number(e.target.value))} style={inputStyle} />
          </label>
        </div>
        <button onClick={handleComplianceCheck} style={primaryButtonStyle}>Check Compliance</button>
        {complianceResult.length > 0 && (
          <div style={{ marginTop: '12px' }}>
            <ViolationTable violations={complianceResult} />
          </div>
        )}
      </section>

      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Quality Gates Overview</h2>
        {rulesLoading && <div style={{ color: '#94a3b8' }}>Loading rules…</div>}
        {!rulesLoading && (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={tableHeaderStyle}>
                <th style={thStyle}>Rule</th>
                <th style={thStyle}>Type</th>
                <th style={thStyle}>Severity</th>
                <th style={thStyle}>Action</th>
                <th style={thStyle}>Threshold</th>
              </tr>
            </thead>
            <tbody>
              {(rulesData?.rules ?? []).map((rule: GovernanceRule) => (
                <tr key={rule.id} style={trStyle}>
                  <td style={tdStyle}>{rule.name}</td>
                  <td style={tdStyle}>{rule.rule_type}</td>
                  <td style={{ ...tdStyle, color: severityColor(rule.severity) }}>{rule.severity}</td>
                  <td style={tdStyle}>{rule.action}</td>
                  <td style={tdStyle}>{rule.threshold_value ?? '—'}</td>
                </tr>
              ))}
              {(rulesData?.rules ?? []).length === 0 && (
                <tr>
                  <td colSpan={5} style={{ color: '#94a3b8', padding: '12px', textAlign: 'center' }}>No configured rules.</td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </section>

      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Violation Log</h2>
        <button onClick={() => refetchLog()} style={secondaryButtonStyle}>Refresh Log</button>
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '12px' }}>
          <thead>
            <tr style={tableHeaderStyle}>
              <th style={thStyle}>Type</th>
              <th style={thStyle}>Severity</th>
              <th style={thStyle}>Details</th>
              <th style={thStyle}>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {(violationLog?.violations ?? []).map((record) => (
              <tr key={record.id} style={trStyle}>
                <td style={tdStyle}>{record.type}</td>
                <td style={{ ...tdStyle, color: severityColor(record.severity) }}>{record.severity}</td>
                <td style={tdStyle}>
                  <code style={{ fontSize: '11px' }}>{formatDetails(record.details)}</code>
                </td>
                <td style={tdStyle}>{record.created_at}</td>
              </tr>
            ))}
            {(violationLog?.violations ?? []).length === 0 && (
              <tr>
                <td colSpan={4} style={{ color: '#94a3b8', padding: '12px', textAlign: 'center' }}>No logged violations.</td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      {errorMessage && <div style={{ color: '#fecaca' }}>{errorMessage}</div>}
    </div>
  )
}

const ViolationTable = ({ violations }: { violations: Violation[] }) => (
  <div style={{ overflowX: 'auto' }}>
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr style={tableHeaderStyle}>
          <th style={thStyle}>Rule</th>
          <th style={thStyle}>Type</th>
          <th style={thStyle}>Severity</th>
          <th style={thStyle}>Details</th>
        </tr>
      </thead>
      <tbody>
        {violations.map((v, idx) => (
          <tr key={idx} style={trStyle}>
            <td style={tdStyle}>{v.rule_id}</td>
            <td style={tdStyle}>{v.type}</td>
            <td style={{ ...tdStyle, color: severityColor(v.severity) }}>{v.severity}</td>
            <td style={tdStyle}>
              <code style={{ fontSize: '11px' }}>{JSON.stringify(v.details)}</code>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
)

const formatDetails = (details: GovernanceViolationRecord['details']) => {
  if (typeof details === 'string') {
    return details
  }
  try {
    return JSON.stringify(details)
  } catch {
    return '—'
  }
}

const severityColor = (severity: string) => {
  if (severity === 'critical') return '#f87171'
  if (severity === 'high') return '#fb923c'
  if (severity === 'medium') return '#facc15'
  return '#a7f3d0'
}

const sectionStyle: React.CSSProperties = {
  background: '#101629',
  padding: '20px',
  borderRadius: '16px',
  border: '1px solid rgba(148,163,184,0.2)'
}

const sectionTitleStyle: React.CSSProperties = { fontSize: '18px', fontWeight: 600, marginBottom: '12px', color: '#e2e8f0' }
const labelStyle: React.CSSProperties = { display: 'flex', flexDirection: 'column', gap: '4px', color: '#cbd5e1' }
const inputStyle: React.CSSProperties = {
  background: '#0f172a',
  border: '1px solid rgba(148,163,184,0.4)',
  borderRadius: '8px',
  padding: '8px 12px',
  color: '#e2e8f0'
}
const textareaStyle: React.CSSProperties = {
  background: '#0f172a',
  border: '1px solid rgba(148,163,184,0.4)',
  borderRadius: '8px',
  color: '#e2e8f0',
  padding: '10px',
  minHeight: '100px'
}
const primaryButtonStyle: React.CSSProperties = {
  background: 'linear-gradient(135deg,#22d3ee,#0ea5e9)',
  color: '#fff',
  border: 'none',
  borderRadius: '8px',
  padding: '10px 16px',
  fontWeight: 600,
  cursor: 'pointer'
}
const secondaryButtonStyle: React.CSSProperties = {
  background: 'rgba(59,130,246,0.15)',
  border: '1px solid rgba(59,130,246,0.5)',
  color: '#cbd5e1',
  borderRadius: '8px',
  padding: '8px 12px',
  cursor: 'pointer'
}
const tableHeaderStyle: React.CSSProperties = {
  borderBottom: '1px solid rgba(255,255,255,0.1)',
  color: '#94a3b8',
  textTransform: 'uppercase',
  fontSize: '11px'
}
const thStyle: React.CSSProperties = { padding: '10px', textAlign: 'left' }
const tdStyle: React.CSSProperties = { padding: '10px', color: '#e2e8f0', fontSize: '13px' }
const trStyle: React.CSSProperties = { borderBottom: '1px solid rgba(255,255,255,0.05)' }
