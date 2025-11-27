import { useState } from 'react'
import { growthAPI } from '../api/v2/growth'
import type { ClvResponse, CohortRecord, RetentionRecord } from '../api/v2/growth'
import { useI18n } from '../contexts/I18nContext'
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'

const DEFAULT_GROWTH_PAYLOAD = JSON.stringify(
  [
    { user_id: 'u1', t: 0, revenue: 0, treated: false, cohort: '2025-W45' },
    { user_id: 'u1', t: 1, revenue: 120, treated: false, cohort: '2025-W45' },
    { user_id: 'u2', t: 0, revenue: 0, treated: true, cohort: '2025-W46' },
    { user_id: 'u2', t: 1, revenue: 80, treated: true, cohort: '2025-W46' },
    { user_id: 'u3', t: 0, revenue: 0, treated: true, cohort: '2025-W46' },
    { user_id: 'u3', t: 2, revenue: 200, treated: true, cohort: '2025-W46' }
  ],
  null,
  2
)

export default function GrowthStudio() {
  const { t } = useI18n()
  const [discountRate, setDiscountRate] = useState(0.01)
  const [dataPayload, setDataPayload] = useState(DEFAULT_GROWTH_PAYLOAD)
  const [clvResult, setClvResult] = useState<ClvResponse | null>(null)
  const [cohortData, setCohortData] = useState<CohortRecord[]>([])
  const [retentionData, setRetentionData] = useState<RetentionRecord[]>([])
  const [retentionTreated, setRetentionTreated] = useState(true)
  const [isRunning, setIsRunning] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const runGrowthAnalysis = async () => {
    setErrorMessage(null)
    let parsed: Array<Record<string, any>>
    try {
      parsed = JSON.parse(dataPayload)
      if (!Array.isArray(parsed)) {
        throw new Error('Payload must be JSON array')
      }
    } catch (err) {
      setErrorMessage('Invalid JSON payload')
      return
    }

    setIsRunning(true)
    try {
      const payload = { discount_rate: discountRate, data: parsed }
      const [clv, cohorts, retention] = await Promise.all([
        growthAPI.calculateClv(payload),
        growthAPI.cohortAnalysis(payload),
        growthAPI.retentionCurve(payload, retentionTreated)
      ])
      setClvResult(clv)
      setCohortData(cohorts)
      setRetentionData(retention)
    } catch (err) {
      setErrorMessage('Failed to run growth analysis')
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      <header>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>Growth & LTV Studio</h1>
        <p style={{ color: '#94a3b8' }}>
          Run CLV, cohort, and retention analyses using the Survival + Discount approach described in V2.pdf.
        </p>
      </header>

      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>{t('growth.input') ?? 'Input Data'}</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: '12px', marginBottom: '12px' }}>
          <label style={labelStyle}>
            Discount Rate
            <input
              type="number"
              min={0}
              max={1}
              step={0.001}
              value={discountRate}
              onChange={(e) => setDiscountRate(Number(e.target.value))}
              style={inputStyle}
            />
          </label>
          <label style={labelStyle}>
            Retention Mode
            <select value={String(retentionTreated)} onChange={(e) => setRetentionTreated(e.target.value === 'true')} style={inputStyle}>
              <option value="true">Treated</option>
              <option value="false">Control</option>
            </select>
          </label>
        </div>
        <textarea
          value={dataPayload}
          onChange={(e) => setDataPayload(e.target.value)}
          rows={10}
          style={textareaStyle}
        />
        <button onClick={runGrowthAnalysis} style={primaryButtonStyle} disabled={isRunning}>
          {isRunning ? 'Running…' : 'Run Growth Analysis'}
        </button>
        {errorMessage && <div style={{ color: '#fecaca', marginTop: '8px' }}>{errorMessage}</div>}
      </section>

      {clvResult && (
        <section style={sectionStyle}>
          <h2 style={sectionTitleStyle}>CLV Summary</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: '12px' }}>
            <SummaryCard title="CLV (Treated)" value={`¥${clvResult.clv_treated.toFixed(2)}`} accent="linear-gradient(135deg,#34d399,#10b981)" />
            <SummaryCard title="CLV (Control)" value={`¥${clvResult.clv_control.toFixed(2)}`} accent="linear-gradient(135deg,#a78bfa,#6366f1)" />
            <SummaryCard title="Δ CLV" value={`¥${clvResult.delta_clv.toFixed(2)}`} accent="linear-gradient(135deg,#f97316,#ea580c)" />
          </div>
        </section>
      )}

      {cohortData.length > 0 && (
        <section style={sectionStyle}>
          <h2 style={sectionTitleStyle}>Cohort Analysis</h2>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={tableHeaderStyle}>
                  <th style={thStyle}>Cohort</th>
                  <th style={thStyle}>CLV (Treated)</th>
                  <th style={thStyle}>CLV (Control)</th>
                  <th style={thStyle}>Δ CLV</th>
                </tr>
              </thead>
              <tbody>
                {cohortData.map((row) => (
                  <tr key={row.cohort} style={trStyle}>
                    <td style={tdStyle}>{row.cohort}</td>
                    <td style={tdStyle}>¥{row.clv_treated.toFixed(2)}</td>
                    <td style={tdStyle}>¥{row.clv_control.toFixed(2)}</td>
                    <td style={tdStyle}>¥{row.delta_clv.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {retentionData.length > 0 && (
        <section style={sectionStyle}>
          <h2 style={sectionTitleStyle}>Retention Curve ({retentionTreated ? 'Treated' : 'Control'})</h2>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={retentionData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                <XAxis dataKey="period" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" domain={[0, 1]} tickFormatter={(value) => `${(value * 100).toFixed(0)}%`} />
                <Tooltip formatter={(value: number) => `${(value * 100).toFixed(1)}%`} />
                <Line type="monotone" dataKey="retention" stroke="#38bdf8" strokeWidth={2} dot={{ r: 2 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}
    </div>
  )
}

const SummaryCard = ({ title, value, accent }: { title: string; value: string; accent: string }) => (
  <div style={{
    borderRadius: '16px',
    padding: '20px',
    background: '#0f172a',
    border: '1px solid rgba(148,163,184,0.2)'
  }}>
    <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '6px' }}>{title}</div>
    <div style={{ fontSize: '28px', fontWeight: 700, background: accent, WebkitBackgroundClip: 'text', color: 'transparent' }}>{value}</div>
  </div>
)

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
  width: '100%',
  borderRadius: '8px',
  padding: '12px',
  background: '#0f172a',
  color: '#e2e8f0',
  border: '1px solid rgba(148,163,184,0.4)',
  marginBottom: '12px'
}

const primaryButtonStyle: React.CSSProperties = {
  background: 'linear-gradient(135deg,#3b82f6,#8b5cf6)',
  color: '#fff',
  border: 'none',
  borderRadius: '8px',
  padding: '10px 16px',
  fontWeight: 600,
  cursor: 'pointer'
}

const tableHeaderStyle: React.CSSProperties = {
  borderBottom: '1px solid rgba(255,255,255,0.1)',
  color: '#94a3b8',
  textTransform: 'uppercase',
  fontSize: '11px'
}

const thStyle: React.CSSProperties = { padding: '10px', textAlign: 'left' }
const trStyle: React.CSSProperties = { borderBottom: '1px solid rgba(255,255,255,0.05)' }
const tdStyle: React.CSSProperties = { padding: '10px', color: '#e2e8f0', fontSize: '13px' }
