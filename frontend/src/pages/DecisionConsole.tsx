import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ScatterChart,
  Scatter,
  ZAxis,
  ReferenceLine,
  ComposedChart,
  Line,
  Cell
} from 'recharts'
import {
  decisionConsoleAPI,
  DecisionConsoleSummary,
  TrendPoint,
  SegmentPortfolioPoint,
  ChannelPerformancePoint,
  DecisionPolicyRow,
  Verdict
} from '../api/v1/decisionConsole'
import { formatYen, formatYenShort, formatYenApprox, formatDecisionDate } from '../utils/format'
import { useI18n } from '../contexts/I18nContext'

const DATE_RANGES = [
  { label: 'Last 14 days', days: 14 },
  { label: 'Last 28 days', days: 28 },
  { label: 'Last 56 days', days: 56 }
] as const

type VerdictFilter = 'all' | Verdict
const verdictOptions: VerdictFilter[] = ['all', 'go', 'canary', 'hold']

const formatDateParam = (date: Date) => date.toISOString().slice(0, 10)
const formatDisplayDate = (date: Date) => date.toISOString().slice(0, 10)

const normalizeVerdict = (value: string | null | undefined): Verdict => {
  const normalized = (value || '').toLowerCase()
  if (normalized === 'go' || normalized === 'canary' || normalized === 'hold') {
    return normalized
  }
  return 'hold'
}

export default function DecisionConsole() {
  const { t, language } = useI18n()
  const [selectedRange, setSelectedRange] = useState<(typeof DATE_RANGES)[number]>(DATE_RANGES[1])
  const [selectedWeek, setSelectedWeek] = useState<string | null>(null)
  const [selectedChannel, setSelectedChannel] = useState<string | null>(null)
  const [verdictFilter, setVerdictFilter] = useState<VerdictFilter>('all')

  const endDate = new Date()
  const startDate = new Date(endDate)
  startDate.setDate(startDate.getDate() - (selectedRange.days - 1))

  const { data, isLoading, isFetching, error, refetch } = useQuery({
    queryKey: ['decision-console-overview', selectedRange.days, language],
    queryFn: () => decisionConsoleAPI.overview({
      from: formatDateParam(startDate),
      to: formatDateParam(endDate),
      locale: language
    }),
    staleTime: 60_000
  })

  const filteredPolicies = useMemo(() => {
    if (!data) return []
    return data.decisions.filter((decision) => {
      const channelKey = decision.channel || 'Unknown'
      if (selectedChannel && channelKey !== selectedChannel) return false
      if (verdictFilter !== 'all' && normalizeVerdict(decision.verdict) !== verdictFilter) return false
      if (selectedWeek) {
        const bucket = toWeekKey(new Date(decision.decided_at))
        if (bucket !== selectedWeek) return false
      }
      return true
    })
  }, [data, selectedChannel, verdictFilter, selectedWeek])

  if (isLoading && !data) {
    return (
      <div style={{ padding: '48px', color: '#e2e8f0', fontSize: '16px' }}>
        {t('common.loading')}
      </div>
    )
  }

  if (!data) {
    return (
      <div style={{ padding: '48px', color: '#f87171', fontSize: '16px' }}>
        <p style={{ marginBottom: '16px' }}>Decision Console データの取得に失敗しました。</p>
        <button
          onClick={() => refetch()}
          style={{
            backgroundColor: '#3b82f6',
            border: 'none',
            color: '#fff',
            padding: '8px 16px',
            borderRadius: '6px',
            cursor: 'pointer'
          }}
        >
          再試行
        </button>
      </div>
    )
  }

  const hasError = Boolean(error)

  return (
    <div className="space-y-6" style={{ padding: '24px' }}>
      {hasError && (
        <div style={{
          backgroundColor: '#451a1f',
          border: '1px solid #b91c1c',
          color: '#fecaca',
          padding: '12px 16px',
          borderRadius: '8px',
          marginBottom: '16px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '12px'
        }}>
          <span>Decision Console データの取得に失敗しました。</span>
          <button
            onClick={() => refetch()}
            style={{
              backgroundColor: '#b91c1c',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              padding: '6px 12px',
              cursor: 'pointer'
            }}
          >
            再試行
          </button>
        </div>
      )}

      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '32px', fontWeight: 700 }}>{t('console.title')}</h1>
          <p style={{ color: '#94a3b8', marginTop: '4px' }}>
            {formatDisplayDate(startDate)} 〜 {formatDisplayDate(endDate)} のマーケ施策ポートフォリオ
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {DATE_RANGES.map((range) => (
            <button
              key={range.days}
              onClick={() => {
                setSelectedRange(range)
                setSelectedWeek(null)
                setSelectedChannel(null)
              }}
              style={{
                padding: '8px 14px',
                borderRadius: '999px',
                border: selectedRange.days === range.days ? '1px solid rgba(59,130,246,0.8)' : '1px solid rgba(148,163,184,0.3)',
                background: selectedRange.days === range.days ? 'rgba(59,130,246,0.15)' : 'transparent',
                color: '#e2e8f0',
                fontSize: '13px',
                cursor: 'pointer',
                opacity: isFetching && selectedRange.days === range.days ? 0.7 : 1
              }}
            >
              {range.label}
            </button>
          ))}
        </div>
      </header>

      <SummaryRow summary={data} start={formatDisplayDate(startDate)} end={formatDisplayDate(endDate)} />

      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))', gap: '24px' }}>
        <Card title="Δ¥ Trend">
          <WeeklyDeltaChart
            data={data.trend}
            onSelect={setSelectedWeek}
            selectedWeek={selectedWeek}
          />
        </Card>

        <Card title="Segment Portfolio">
          <SegmentPortfolioChart segments={data.segment_portfolio} />
        </Card>

        <Card title="Channel Performance">
          <ChannelPerformanceChart
            channels={data.channel_performance}
            onSelectChannel={setSelectedChannel}
            selectedChannel={selectedChannel}
          />
        </Card>
      </section>

      <PolicyTable
        policies={filteredPolicies}
        original={data.decisions}
        verdictFilter={verdictFilter}
        setVerdictFilter={setVerdictFilter}
      />
    </div>
  )
}

const SummaryRow = ({ summary, start, end }: { summary: DecisionConsoleSummary; start: string; end: string }) => {
  const totalApprox = formatYenApprox(summary.total_delta_yen)
  const averageApprox = formatYenApprox(summary.avg_delta_yen_per_policy)

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: '20px' }}>
      <SummaryCard
        label="Total Incremental Profit"
        value={formatYen(summary.total_delta_yen)}
        sub={totalApprox ? `${totalApprox} / ${start}〜${end}` : `${start}〜${end}`}
        accent="linear-gradient(135deg,#6366f1,#8b5cf6)"
      />
      <SummaryCard
        label="Average Δ¥ / Policy"
        value={formatYen(summary.avg_delta_yen_per_policy)}
        sub={averageApprox || 'Target: ≥ 0'}
        accent="linear-gradient(135deg,#ec4899,#f97316)"
      />
      <SummaryCard
        label="Mean CAS"
        value={summary.mean_cas !== null ? summary.mean_cas.toFixed(2) : '–'}
        sub="Target ≥ 0.75"
        accent="linear-gradient(135deg,#0ea5e9,#22d3ee)"
      />
      <SummaryCard
        label="CVaR (worst 10%)"
        value={summary.cvar_yen_p10 !== null ? formatYen(summary.cvar_yen_p10) : '–'}
        sub="Lower is better"
        accent="linear-gradient(135deg,#f97316,#ef4444)"
      />
    </div>
  )
}

const SummaryCard = ({ label, value, sub, accent }: { label: string; value: string; sub?: string; accent: string }) => (
  <div style={{
    borderRadius: '16px',
    padding: '24px',
    background: '#1e1f2b',
    border: '1px solid rgba(148,163,184,0.2)'
  }}>
    <div style={{ fontSize: '14px', color: '#94a3b8', marginBottom: '8px' }}>{label}</div>
    <div style={{ fontSize: '32px', fontWeight: 700, background: accent, WebkitBackgroundClip: 'text', color: 'transparent' }}>{value}</div>
    <div style={{ fontSize: '12px', color: '#cbd5e1' }}>{sub || '–'}</div>
  </div>
)

const WeeklyDeltaChart = ({ data, onSelect, selectedWeek }: { data: TrendPoint[]; onSelect: (bucket: string | null) => void; selectedWeek: string | null }) => {
  if (!data || data.length === 0) {
    return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '32px' }}>データがありません</div>
  }

  const handleClick = (point?: TrendPoint) => {
    if (!point) return
    onSelect(point.bucket === selectedWeek ? null : point.bucket)
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <ComposedChart data={data} onClick={(e) => handleClick(e?.activePayload?.[0]?.payload)}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
        <XAxis dataKey="bucket" stroke="#94a3b8" />
        <YAxis stroke="#94a3b8" />
        <Tooltip formatter={(value: number) => formatYenShort(value)} />
        <Bar dataKey="delta_yen" fill="#34d399" name="Δ¥" />
        <Line type="monotone" dataKey="target_yen" stroke="#f97316" strokeDasharray="4 4" dot={false} name="Target" />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

const SegmentPortfolioChart = ({ segments }: { segments: SegmentPortfolioPoint[] }) => {
  if (!segments || segments.length === 0) {
    return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '32px' }}>データがありません</div>
  }

  const populations = segments.map((s) => s.population || 0)
  const deltas = segments.map((s) => s.total_delta_yen || 0)
  const populationMedian = getMedian(populations)
  const deltaMedian = getMedian(deltas)

  const formatted = segments.map((segment) => ({
    population: segment.population,
    delta: segment.total_delta_yen,
    size: segment.policy_count,
    cas: segment.mean_cas ?? 0,
    name: segment.segment_label
  }))

  const colorForCas = (cas: number) => {
    if (cas >= 0.8) return '#22c55e'
    if (cas >= 0.6) return '#facc15'
    return '#ef4444'
  }

  return (
    <div style={{ width: '100%', height: 240, position: 'relative' }}>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart>
          <CartesianGrid stroke="rgba(255,255,255,0.1)" />
          <XAxis type="number" dataKey="population" name="Population" stroke="#94a3b8" />
          <YAxis type="number" dataKey="delta" name="Δ¥" stroke="#94a3b8" />
          <ZAxis dataKey="size" range={[60, 400]} />
          <ReferenceLine x={populationMedian} stroke="rgba(255,255,255,0.2)" />
          <ReferenceLine y={deltaMedian} stroke="rgba(255,255,255,0.2)" />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            formatter={(value: number, name: string) => name === 'Δ¥' ? formatYenShort(value) : value.toFixed(0)}
          />
          <Scatter data={formatted} name="Segments">
            {formatted.map((entry) => (
              <Cell key={entry.name} fill={colorForCas(entry.cas)} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      <div style={{ position: 'absolute', bottom: 8, right: 8, fontSize: '11px', color: '#94a3b8' }}>
        Stars / Question / Cash Cow / Dogs
      </div>
    </div>
  )
}

const ChannelPerformanceChart = ({ channels, onSelectChannel, selectedChannel }: { channels: ChannelPerformancePoint[]; onSelectChannel: (channel: string | null) => void; selectedChannel: string | null }) => {
  if (!channels || channels.length === 0) {
    return <div style={{ color: '#94a3b8', textAlign: 'center', padding: '32px' }}>データがありません</div>
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <ComposedChart data={channels}>
        <CartesianGrid stroke="rgba(255,255,255,0.1)" />
        <XAxis dataKey="channel" stroke="#94a3b8" />
        <YAxis yAxisId="left" stroke="#94a3b8" />
        <YAxis yAxisId="right" orientation="right" stroke="#94a3b8" />
        <Tooltip formatter={(value: number, name: string) => name === 'total_delta_yen' ? formatYenShort(value) : (typeof value === 'number' ? value.toFixed(2) : value)} />
        <Bar
          dataKey="total_delta_yen"
          yAxisId="left"
          fill="#8b5cf6"
          name="Δ¥"
          onClick={(data) => onSelectChannel(data?.channel === selectedChannel ? null : (data?.channel || null))}
        />
        <Line dataKey="roi" yAxisId="right" stroke="#f97316" name="ROI" />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

const PolicyTable = ({
  policies,
  original,
  verdictFilter,
  setVerdictFilter
}: {
  policies: DecisionPolicyRow[]
  original: DecisionPolicyRow[]
  verdictFilter: VerdictFilter
  setVerdictFilter: (v: VerdictFilter) => void
}) => {
  const verdictColor = (v: string) => {
    const lower = normalizeVerdict(v)
    if (lower === 'go') return '#22c55e'
    if (lower === 'canary') return '#fbbf24'
    return '#ef4444'
  }

  return (
    <Card
      title="Decision Cards"
      action={
        <div style={{ display: 'flex', gap: '8px' }}>
          {verdictOptions.map((option) => (
            <button
              key={option}
              onClick={() => setVerdictFilter(option)}
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                border: verdictFilter === option ? '1px solid rgba(59,130,246,0.7)' : '1px solid rgba(148,163,184,0.3)',
                background: verdictFilter === option ? 'rgba(59,130,246,0.15)' : 'transparent',
                color: '#f1f5f9',
                cursor: 'pointer'
              }}
            >
              {option === 'all' ? 'All' : option.charAt(0).toUpperCase() + option.slice(1)}
            </button>
          ))}
        </div>
      }
    >
      {policies.length === 0 ? (
        <div style={{ color: '#94a3b8', padding: '24px', textAlign: 'center' }}>
          {original.length === 0 ? 'No decisions in selected period' : 'No policies matching filters'}
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8', textTransform: 'uppercase', fontSize: '11px' }}>
                <th style={{ padding: '12px', textAlign: 'left' }}>Policy</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Dataset</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Channel</th>
                <th style={{ padding: '12px', textAlign: 'left' }}>Segment</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>Δ¥</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>ROI</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>CAS</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>Risk</th>
                <th style={{ padding: '12px', textAlign: 'center' }}>Verdict</th>
                <th style={{ padding: '12px', textAlign: 'right' }}>Period</th>
              </tr>
            </thead>
            <tbody>
              {policies.map((policy) => (
                <tr key={policy.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '12px', color: '#f8fafc' }}>{policy.policy_name}</td>
                  <td style={{ padding: '12px', color: '#cbd5e1' }}>{policy.dataset_label}</td>
                  <td style={{ padding: '12px', color: '#cbd5e1' }}>{policy.channel || '–'}</td>
                  <td style={{ padding: '12px', color: '#cbd5e1' }}>{policy.segment_label || '–'}</td>
                  <td style={{ padding: '12px', textAlign: 'right', color: policy.delta_yen >= 0 ? '#22c55e' : '#ef4444' }}>
                    {formatYen(policy.delta_yen)}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right', color: '#fbbf24' }}>
                    {policy.roi !== null && policy.roi !== undefined ? policy.roi.toFixed(2) : '–'}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right', color: '#93c5fd' }}>
                    {policy.cas_score !== null && policy.cas_score !== undefined ? policy.cas_score.toFixed(2) : '–'}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right', color: '#f87171' }}>
                    {policy.risk_score !== null && policy.risk_score !== undefined ? policy.risk_score.toFixed(2) : '–'}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'center', color: verdictColor(policy.verdict) }}>
                    {normalizeVerdict(policy.verdict).charAt(0).toUpperCase() + normalizeVerdict(policy.verdict).slice(1)}
                  </td>
                  <td style={{ padding: '12px', textAlign: 'right', color: '#94a3b8', fontSize: '11px' }}>
                    {policy.start_date === policy.end_date
                      ? formatDecisionDate(policy.start_date)
                      : `${formatDecisionDate(policy.start_date)} ~ ${formatDecisionDate(policy.end_date)}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div style={{ marginTop: '12px', fontSize: '12px', color: '#94a3b8' }}>
        Showing {policies.length} / {original.length} policies
      </div>
    </Card>
  )
}

const Card = ({ title, children, action }: { title: string; children: React.ReactNode; action?: React.ReactNode }) => (
  <div style={{ background: '#101629', borderRadius: '16px', border: '1px solid rgba(148,163,184,0.2)', padding: '20px', minHeight: '260px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', alignItems: 'center', color: '#f8fafc' }}>
      <h2 style={{ fontSize: '16px', fontWeight: 600 }}>{title}</h2>
      {action}
    </div>
    {children}
  </div>
)

const toWeekKey = (date: Date) => {
  const { year, week } = getISOWeek(date)
  return `${year}-W${week.toString().padStart(2, '0')}`
}

const getISOWeek = (date: Date) => {
  const tmp = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()))
  const dayNumber = tmp.getUTCDay() || 7
  tmp.setUTCDate(tmp.getUTCDate() + 4 - dayNumber)
  const yearStart = new Date(Date.UTC(tmp.getUTCFullYear(), 0, 1))
  const weekNo = Math.ceil((((tmp.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
  return { year: tmp.getUTCFullYear(), week: weekNo }
}

const getMedian = (values: number[]) => {
  if (!values.length) return 0
  const sorted = [...values].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  if (sorted.length % 2 === 0) {
    return (sorted[mid - 1] + sorted[mid]) / 2
  }
  return sorted[mid]
}
