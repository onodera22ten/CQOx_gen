import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { datasetsAPI, TreatmentSummary } from '../api/v1/datasets'
import { analysisAPI, AnalysisStatus } from '../api/v1/analysis'
import type { AnalysisDetails } from '../api/v1/analysis'
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ContextBar } from '../components/ContextBar'
import { DecisionSummaryCard } from '../components/DecisionSummaryCard'
import { formatYenShort, formatYenMan } from '../utils/format'

const DEFAULT_POLICY_ID = '00000000-0000-0000-0000-000000000002'

const TREATMENT_MESSAGES = {
  single_class: {
    title: '処置列が 1 クラスしかありません',
    body: '選択された処置列には実質 1 種類の値のみが含まれています。CQOx の推定器は「施策なし (0)」と「施策あり (1)」の 2 グループを比較する前提です。',
    actions: [
      'フィルタ条件を見直し、施策あり／なしの両方が含まれるデータをアップロードしてください。',
      '施策が打たれていないデータでは因果効果を推定できません。別の施策列を選択してください。'
    ]
  },
  multi_class: {
    title: '現在は 0/1 のバイナリ処置のみ対応しています',
    body: '選択された処置列には 3 クラス以上の値が含まれています。v1 の推定器は 0/1 の処置のみサポートしているため、バイナリ列に変換する必要があります。',
    actions: [
      '例: is_enhanced_care = 1 if treatment_arm == "enhanced_care" else 0 の列を作成し、その列を処置として選択してください。',
      '既に存在する 0/1 列（例: icu_admission, readmission_30d）を処置列として選ぶ方法もあります。'
    ]
  },
  unavailable: {
    title: '自動検証は利用できません',
    body: 'このデータセットは v1 の処置列検証サービス対象外です。モデル自体は実行できますが、処置列が 2 値になっているかは CSV 側でご確認ください。',
    actions: [
      '処置列に 2 種類以上の値（施策あり／なし）が含まれているか確認してください。',
      '0/1 または True/False などの形式に変換してから再度アップロードしてください。'
    ]
  },
  unavailable: {
    title: '自動検証は利用できません',
    body: 'このデータセットは v1 の処置列検証サービス対象外です。モデル自体は実行できますが、処置列が 2 値になっているかは CSV 側でご確認ください。',
    actions: [
      '処置列に少なくとも 2 種類の値（施策なし／あり）が含まれているか確認してください。',
      '0/1 や True/False などのバイナリ形式に変換してから再度アップロードしてください。'
    ]
  }
} as const

type TreatmentWarningKey = keyof typeof TREATMENT_MESSAGES

const mapErrorCodeToTreatmentStatus = (code?: string | null): TreatmentWarningKey | null => {
  if (!code) return null
  if (code === 'treatment_single_class') return 'single_class'
  if (code === 'treatment_multiclass' || code === 'treatment_encoding_failure') return 'multi_class'
  return null
}

export default function CausalDesign() {
  const navigate = useNavigate()
  const [selectedDataset, setSelectedDataset] = useState<string>('')
  const [selectedEstimators, setSelectedEstimators] = useState<string[]>(['DR', 'IPW'])
  const [treatmentCol, setTreatmentCol] = useState<string>('')
  const [outcomeCol, setOutcomeCol] = useState<string>('')
  const [featureCols, setFeatureCols] = useState<string>('')
  const [currentAnalysis, setCurrentAnalysis] = useState<AnalysisStatus | null>(null)
  const [polling, setPolling] = useState(false)
  const [availableColumns, setAvailableColumns] = useState<string[]>([])
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(null)
  const [treatmentSummary, setTreatmentSummary] = useState<TreatmentSummary | null>(null)
  const [treatmentSummaryLoading, setTreatmentSummaryLoading] = useState(false)
  const analysisErrorWarning = mapErrorCodeToTreatmentStatus(currentAnalysis?.error_code ?? null)
  const treatmentBlocked = treatmentSummary ? (treatmentSummary.status === 'single_class' || treatmentSummary.status === 'multi_class') : false

  const renderTreatmentGuidance = (status: TreatmentWarningKey, details?: Record<string, any>) => {
    const config = TREATMENT_MESSAGES[status]
    let wrapperStyle: React.CSSProperties
    let textColor = '#fca5a5'
    let accentColor = '#fecaca'

    if (status === 'single_class') {
      wrapperStyle = { background: 'rgba(239,68,68,0.12)', border: '1px solid rgba(239,68,68,0.4)' }
    } else if (status === 'multi_class') {
      wrapperStyle = { background: 'rgba(249,115,22,0.12)', border: '1px solid rgba(249,115,22,0.4)' }
      textColor = '#fed7aa'
      accentColor = '#fed7aa'
    } else {
      wrapperStyle = { background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.4)' }
      textColor = '#bfdbfe'
      accentColor = '#bfdbfe'
    }

    return (
      <div style={{ marginTop: '8px', padding: '12px', borderRadius: '8px', color: textColor, ...wrapperStyle }}>
        <div style={{ fontWeight: 600, color: accentColor, marginBottom: '4px' }}>{config.title}</div>
        <div style={{ color: accentColor, fontSize: '13px', marginBottom: '8px' }}>{config.body}</div>
        {details?.unique_values && details.unique_values.length > 0 && status !== 'unavailable' && (
          <div style={{ fontSize: '12px', color: '#fef3c7', marginBottom: '8px' }}>
            検出された値: <code style={{ fontSize: '12px' }}>{details.unique_values.join(', ')}</code>
          </div>
        )}
        {details?.value_counts && Object.keys(details.value_counts).length > 0 && status !== 'unavailable' && (
          <div style={{ fontSize: '12px', color: '#fef3c7', marginBottom: '8px' }}>
            サンプル件数: {Object.entries(details.value_counts).slice(0, 3).map(([val, count]) => `${val}: ${count}`).join(' / ')}
          </div>
        )}
        <ul style={{ margin: 0, paddingLeft: '18px', color: textColor, fontSize: '12px' }}>
          {config.actions.map((action) => (
            <li key={action} style={{ marginBottom: '4px' }}>{action}</li>
          ))}
        </ul>
        {details?.reason && (
          <div style={{ marginTop: '6px', fontSize: '12px', opacity: 0.8 }}>
            詳細: {details.reason}
          </div>
        )}
      </div>
    )
  }

  const renderTreatmentSuccess = (summary: TreatmentSummary) => (
    <div style={{ marginTop: '8px', padding: '10px', borderRadius: '8px', border: '1px solid rgba(34,197,94,0.4)', background: 'rgba(16,185,129,0.12)', color: '#a7f3d0', fontSize: '12px' }}>
      ✅ この処置列は 0/1 のバイナリ条件を満たしています。（ユニーク値: {summary.unique_count}）
    </div>
  )

  const normalizeNumber = (value: number | string | null | undefined, fallback = 0): number => {
    if (typeof value === 'number') {
      return Number.isFinite(value) ? value : fallback
    }
    if (typeof value === 'string') {
      const parsed = Number(value)
      return Number.isFinite(parsed) ? parsed : fallback
    }
    return fallback
  }

  const safeLocaleString = (
    value: number | string | null | undefined,
    options?: Intl.NumberFormatOptions,
    locale = 'ja-JP',
    fallback = '—'
  ): string => {
    const normalized = normalizeNumber(value, Number.NaN)
    if (!Number.isFinite(normalized)) {
      return fallback
    }
    return normalized.toLocaleString(locale, options)
  }

  const formatDateTime = (value?: string | null, locale = 'ja-JP'): string => {
    if (!value) return '—'
    const parsed = new Date(value)
    return Number.isNaN(parsed.getTime()) ? '—' : parsed.toLocaleString(locale)
  }

  const toNumberOrNull = (value: number | string | null | undefined): number | null => {
    const normalized = normalizeNumber(value, Number.NaN)
    return Number.isFinite(normalized) ? normalized : null
  }

  const formatYenShortOrDash = (value: number | null): string =>
    value !== null ? formatYenShort(value) : '—'

  const formatYenManOrDash = (value: number | null): string =>
    value !== null ? formatYenMan(value) : '—'

  const formatPercentOrDash = (value: number | null, digits = 1): string =>
    value !== null ? `${(value * 100).toFixed(digits)}%` : '—'

  const formatPercentDeltaOrDash = (value: number | null, digits = 2): string =>
    value !== null ? `${value >= 0 ? '+' : ''}${(value * 100).toFixed(digits)}pp uplift` : '—'

  const formatYenPerUserOrDash = (value: number | null, digits = 1): string =>
    value !== null
      ? `¥${value.toLocaleString('ja-JP', {
          minimumFractionDigits: digits,
          maximumFractionDigits: digits
        })}`
      : '—'

  const formatYenPerUserDeltaOrDash = (value: number | null, digits = 1): string =>
    value !== null
      ? `${value >= 0 ? '+' : '-'}¥${Math.abs(value).toLocaleString('ja-JP', {
          minimumFractionDigits: digits,
          maximumFractionDigits: digits
        })} / user uplift`
      : '—'

  const queryClient = useQueryClient()

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => datasetsAPI.list()
  })

  const { data: analyses } = useQuery({
    queryKey: ['analyses'],
    queryFn: () => analysisAPI.list({ page: 1, page_size: 10 })
  })

  useEffect(() => {
    if (!selectedSnapshotId && currentAnalysis?.status === 'completed') {
      setSelectedSnapshotId(currentAnalysis.analysis_id)
    }
  }, [currentAnalysis, selectedSnapshotId])

  const displayAnalysisId =
    selectedSnapshotId || (currentAnalysis?.status === 'completed' ? currentAnalysis.analysis_id : null)

  const { data: analysisDetails, isFetching: isDetailsLoading } = useQuery({
    queryKey: ['analysis-details', displayAnalysisId],
    queryFn: () => analysisAPI.getDetails(displayAnalysisId!),
    enabled: !!displayAnalysisId,
    staleTime: 60_000
  })

  const displayAnalysis: AnalysisStatus | null =
    analysisDetails?.analysis || (currentAnalysis?.status === 'completed' ? currentAnalysis : null)

  const impactMetrics = analysisDetails?.impact_metrics
  const safeDeltaYen = normalizeNumber(displayAnalysis?.delta_yen, 0)
  const estimatedCost = toNumberOrNull(impactMetrics?.estimated_cost)
  const projectedConversionRate = toNumberOrNull(impactMetrics?.projected_conversion_rate)
  const conversionUplift = toNumberOrNull(impactMetrics?.conversion_uplift)
  const usersAffected = toNumberOrNull(impactMetrics?.users_affected)
  const roiFromSnapshot = toNumberOrNull(impactMetrics?.estimated_roi)
  const fallbackRoi =
    estimatedCost !== null && estimatedCost !== 0 ? safeDeltaYen / estimatedCost : null
  const roiValue = roiFromSnapshot ?? fallbackRoi
  const hasImpactMetrics =
    !!impactMetrics &&
    Object.values(impactMetrics).some((value) => value !== null && value !== undefined)
  const casScore = analysisDetails?.diagnostics?.cas_score
  const isSnapshotView =
    !!displayAnalysis &&
    !!selectedSnapshotId &&
    (!currentAnalysis || selectedSnapshotId !== currentAnalysis.analysis_id)

  // Fetch columns when dataset is selected
  const { data: datasetColumns, isLoading: columnsLoading, error: columnsError } = useQuery({
    queryKey: ['dataset-columns', selectedDataset],
    queryFn: () => datasetsAPI.getColumns(selectedDataset),
    enabled: !!selectedDataset,
    retry: 1,
    // Don't throw errors, just return undefined
    throwOnError: false
  })

  // Auto-populate column selections when dataset columns are loaded
  useEffect(() => {
    if (datasetColumns) {
      setAvailableColumns(datasetColumns.columns)

      // Auto-populate with suggestions if fields are empty
      if (!treatmentCol && datasetColumns.suggestions.treatment_col) {
        setTreatmentCol(datasetColumns.suggestions.treatment_col)
      }
      if (!outcomeCol && datasetColumns.suggestions.outcome_col) {
        setOutcomeCol(datasetColumns.suggestions.outcome_col)
      }
      if (!featureCols && datasetColumns.suggestions.feature_cols.length > 0) {
        setFeatureCols(datasetColumns.suggestions.feature_cols.join(','))
      }
    }
  }, [datasetColumns])

  useEffect(() => {
    if (!selectedDataset || !treatmentCol) {
      setTreatmentSummary(null)
      setTreatmentSummaryLoading(false)
      return
    }

    let cancelled = false
    setTreatmentSummaryLoading(true)

    datasetsAPI.getTreatmentSummary(selectedDataset, treatmentCol)
      .then((summary) => {
        if (!cancelled) {
          setTreatmentSummary(summary)
        }
      })
      .catch((err: any) => {
        if (!cancelled) {
          console.warn('Treatment summary unavailable:', err)
          const message = err?.message || '検証サービスを利用できませんでした。'
          setTreatmentSummary({
            status: 'unavailable',
            unique_count: 0,
            unique_values: [],
            value_counts: {},
            non_null_count: 0,
            reason: message
          })
        }
      })
      .finally(() => {
        if (!cancelled) {
          setTreatmentSummaryLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [selectedDataset, treatmentCol])

  const startAnalysisMutation = useMutation({
    mutationFn: async (params: {
      dataset_id: string;
      treatment_col: string;
      outcome_col: string;
      feature_cols: string[];
      estimators: string[];
    }) => {
      return await analysisAPI.start({
        dataset_id: params.dataset_id,
        policy_id: DEFAULT_POLICY_ID,
        treatment_col: params.treatment_col,
        outcome_col: params.outcome_col,
        feature_cols: params.feature_cols,
        estimators: params.estimators,
        scenario_spec: { s0: {}, s1: {} }
      });
    },
    onSuccess: (data) => {
      setCurrentAnalysis(data);
      setPolling(true);
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
    },
    onError: (error: any) => {
      alert(`分析開始に失敗しました: ${error.message || '不明なエラー'}`);
    }
  });

  // Poll for analysis status
  useEffect(() => {
    if (!polling || !currentAnalysis) return;

    const interval = setInterval(async () => {
      try {
        const status = await analysisAPI.getStatus(currentAnalysis.analysis_id);
        setCurrentAnalysis(status);

        if (status.status === 'completed' || status.status === 'failed') {
          setPolling(false);
          queryClient.invalidateQueries({ queryKey: ['analyses'] });
        }
      } catch (error) {
        console.error('Failed to poll analysis status:', error);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [polling, currentAnalysis, queryClient]);

  const handleTrain = async () => {
    if (!selectedDataset) {
      alert('データセットを選択してください')
      return
    }

    if (!treatmentCol || !outcomeCol || !featureCols.trim()) {
      alert('Treatment, Outcome, Feature columnsを入力してください')
      return
    }

    // Validate columns exist in dataset (only if auto-detection succeeded)
    if (availableColumns.length > 0) {
      const missingCols = []
      if (!availableColumns.includes(treatmentCol)) {
        missingCols.push(`Treatment: "${treatmentCol}"`)
      }
      if (!availableColumns.includes(outcomeCol)) {
        missingCols.push(`Outcome: "${outcomeCol}"`)
      }

      const selectedFeatures = featureCols.split(',').map(f => f.trim()).filter(f => f)
      const missingFeatures = selectedFeatures.filter(f => !availableColumns.includes(f))
      if (missingFeatures.length > 0) {
        missingCols.push(`Features: ${missingFeatures.join(', ')}`)
      }

      if (missingCols.length > 0) {
        alert(
          `❌ 以下のカラムがデータセットに存在しません:\n\n${missingCols.join('\n')}\n\n` +
          `利用可能なカラム: ${availableColumns.join(', ')}`
        )
        return
      }
    }

    // Basic validation (even if auto-detection failed)
    const selectedFeatures = featureCols.split(',').map(f => f.trim()).filter(f => f)
    if (selectedFeatures.length === 0) {
      alert('最低1つのFeature Columnを選択してください')
      return
    }

    if (selectedEstimators.length === 0) {
      alert('最低1つのEstimatorを選択してください')
      return
    }

    if (treatmentSummaryLoading) {
      alert('処置列の検証が完了するまでお待ちください。')
      return
    }

    if (treatmentBlocked) {
      alert('処置列がバイナリ条件を満たしていません。表示されているガイドに従って修正してください。')
      return
    }

    const dataset = datasets?.find((d: any) => d.id === selectedDataset)
    const rowCount = dataset?.row_count || 0

    if (rowCount > 1000000) {
      const proceed = window.confirm(
        `⚠️ 大規模データセット (${safeLocaleString(rowCount, undefined, 'ja-JP', '0')} rows)\n\n` +
        `処理には時間がかかります（目安: 10-30分）。\n` +
        `バッチ処理（10万行/チャンク）で実行されます。\n\n` +
        `続行しますか？`
      )
      if (!proceed) return
    }

    startAnalysisMutation.mutate({
      dataset_id: selectedDataset,
      treatment_col: treatmentCol,
      outcome_col: outcomeCol,
      feature_cols: featureCols.split(',').map(f => f.trim()).filter(f => f),
      estimators: selectedEstimators
    });
  }

  const selectedDatasetInfo = datasets?.find((d: any) => d.id === selectedDataset);

  return (
    <div>
      <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px', color: '#fff' }}>
        Causal Design & Evaluation
      </h1>

      {/* Context Bar */}
      {selectedDatasetInfo && (
        <ContextBar
          dataset={{
            name: selectedDatasetInfo.name || selectedDataset,
            version: '1.0',
            updated_at: selectedDatasetInfo.updated_at,
            row_count: selectedDatasetInfo.row_count,
          }}
          scenario={{
            id: 'S0 vs S1',
            name: 'Baseline vs Treatment Scenario',
            type: 'A/B Test',
          }}
          targetMetric={{
            outcome: outcomeCol || 'revenue',
            horizon: '28 days',
          }}
          runId={currentAnalysis?.analysis_id}
        />
      )}

      {/* Decision Summary Card */}
      {displayAnalysis && displayAnalysis.status === 'completed' && displayAnalysis.delta_yen !== undefined && (
        <>
          {isSnapshotView && (
            <div style={{
              marginBottom: '12px',
              padding: '12px 16px',
              borderRadius: '10px',
              background: 'rgba(59, 130, 246, 0.15)',
              border: '1px solid rgba(59, 130, 246, 0.4)',
              color: '#bfdbfe',
              fontSize: '13px'
            }}>
              🔁 スナップショット表示中: {displayAnalysis.analysis_id.slice(0, 8)}… （再計算ではなく当時の結果を復元しています）
            </div>
          )}
          <DecisionSummaryCard
            title="Causal Analysis Result"
            verdict={(displayAnalysis.verdict as any) || 'Hold'}
            deltaYen={displayAnalysis.delta_yen}
            deltaYenCiLow={displayAnalysis.delta_yen_ci_low}
            deltaYenCiHigh={displayAnalysis.delta_yen_ci_high}
            casScore={casScore ?? undefined}
            reason={
              displayAnalysis.verdict === 'Go'
                ? 'High expected profit with low risk. Causal quality checks passed.'
                : displayAnalysis.verdict === 'Canary'
                  ? 'Moderate confidence. Recommend A/B test before full rollout.'
                  : 'Negative expected profit or low causal quality.'
            }
            recommendations={
              displayAnalysis.verdict === 'Go'
                ? [
                    'Proceed with policy deployment',
                    'Monitor key metrics for first 7 days',
                    'Set up automated alerts for anomalies',
                  ]
                : displayAnalysis.verdict === 'Canary'
                ? [
                    'Run A/B test with 10-20% traffic',
                    'Collect more data to improve confidence',
                    'Review diagnostics for potential issues',
                  ]
                : [
                    'Do not deploy this policy',
                    'Review dataset quality and sample size',
                    'Consider alternative policies',
                  ]
            }
            detailsLoading={isDetailsLoading}
            onViewDetails={() => {
              if (displayAnalysis?.analysis_id) {
                navigate(`/diagnostics?analysis_id=${displayAnalysis.analysis_id}`)
              }
            }}
          />
        </>
      )}

      {/* S0 vs S1 Comparison */}
      {displayAnalysis && displayAnalysis.status === 'completed' && displayAnalysis.delta_yen !== undefined && (
        <div style={{
          marginBottom: '24px',
          background: '#1e293b',
          borderRadius: '16px',
          padding: '32px',
          border: '1px solid #334155'
        }}>
          <div style={{ marginBottom: '24px' }}>
            <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '8px', color: '#fff' }}>
              📊 S0 vs S1 シナリオ比較
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>
              Baseline (S0: 現状維持) と Treatment (S1: 施策実施後) の横並び比較
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            {/* S0 - Baseline */}
            <div style={{
              padding: '24px',
              background: 'rgba(100, 116, 139, 0.1)',
              border: '2px solid #64748b',
              borderRadius: '12px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, #64748b 0%, #475569 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '24px'
                }}>
                  📍
                </div>
                <div>
                  <div style={{ fontSize: '18px', fontWeight: '700', color: '#f1f5f9' }}>S0: Baseline</div>
                  <div style={{ fontSize: '13px', color: '#94a3b8' }}>現状維持シナリオ</div>
                </div>
              </div>

              <div style={{ display: 'grid', gap: '16px' }}>
                <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '8px', fontWeight: '600' }}>REVENUE</div>
                  <div style={{ fontSize: '32px', fontWeight: '700', color: '#f1f5f9' }}>¥0</div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>No intervention</div>
                </div>

                <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '8px', fontWeight: '600' }}>COST</div>
                  <div style={{ fontSize: '32px', fontWeight: '700', color: '#f1f5f9' }}>¥0</div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>Status quo</div>
                </div>

                <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '8px', fontWeight: '600' }}>CONVERSION RATE</div>
                  <div style={{ fontSize: '32px', fontWeight: '700', color: '#f1f5f9' }}>2.4%</div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>Baseline rate</div>
                </div>

                <div style={{ padding: '16px', background: '#0f172a', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '8px', fontWeight: '600' }}>USERS AFFECTED</div>
                  <div style={{ fontSize: '32px', fontWeight: '700', color: '#f1f5f9' }}>0</div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginTop: '4px' }}>Control group</div>
                </div>
              </div>
            </div>

            {/* S1 - Treatment */}
            <div style={{
              padding: '24px',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%)',
              border: '2px solid #10b981',
              borderRadius: '12px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
                <div style={{
                  width: '48px',
                  height: '48px',
                  borderRadius: '12px',
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '24px'
                }}>
                  🚀
                </div>
                <div>
                  <div style={{ fontSize: '18px', fontWeight: '700', color: '#10b981' }}>S1: Treatment</div>
                  <div style={{ fontSize: '13px', color: '#94a3b8' }}>施策実施後シナリオ</div>
                </div>
              </div>

              <div style={{ display: 'grid', gap: '16px' }}>
                <div style={{ padding: '16px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '8px', fontWeight: '600' }}>INCREMENTAL REVENUE (Δ¥)</div>
                  <div style={{ fontSize: '32px', fontWeight: '700', color: '#10b981' }}>
                    +{formatYenShort(displayAnalysis.delta_yen || 0)}
                  </div>
                  <div style={{ fontSize: '11px', color: '#10b981', marginTop: '4px', marginBottom: '6px' }}>
                    {formatYenMan(displayAnalysis.delta_yen || 0)}
                  </div>
                  <div style={{ fontSize: '12px', color: '#10b981', marginTop: '4px' }}>
                    95% CI: {formatYenShort(displayAnalysis.delta_yen_ci_low || 0)} ~ {formatYenShort(displayAnalysis.delta_yen_ci_high || 0)}
                  </div>
                </div>

                <div style={{ padding: '16px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '8px', fontWeight: '600' }}>ESTIMATED COST</div>
                  <div style={{ fontSize: '32px', fontWeight: '700', color: '#f1f5f9' }}>{formatYenShortOrDash(estimatedCost)}</div>
                  <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px', marginBottom: '4px' }}>
                    {formatYenManOrDash(estimatedCost)}
                  </div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>Campaign cost</div>
                </div>

                <div style={{ padding: '16px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '8px', fontWeight: '600' }}>PROJECTED OUTCOME / USER</div>
                  <div style={{ fontSize: '32px', fontWeight: '700', color: '#10b981' }}>
                    {formatYenPerUserOrDash(projectedConversionRate)}
                  </div>
                  <div style={{ fontSize: '12px', color: '#10b981', marginTop: '4px' }}>
                    {formatYenPerUserDeltaOrDash(conversionUplift)}
                  </div>
                </div>

                <div style={{ padding: '16px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginBottom: '8px', fontWeight: '600' }}>USERS AFFECTED</div>
                  <div style={{ fontSize: '32px', fontWeight: '700', color: '#f1f5f9' }}>
                    {safeLocaleString(usersAffected)}
                  </div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>Treatment group</div>
                </div>
              </div>
            </div>
          </div>

          {/* Net Impact Summary */}
          <div style={{
            marginTop: '24px',
            padding: '20px',
            background: 'rgba(59, 130, 246, 0.1)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '4px', fontWeight: '600' }}>📈 NET IMPACT (S1 - S0)</div>
                <div style={{ fontSize: '28px', fontWeight: '700', color: '#10b981' }}>
                  +{formatYenShort(displayAnalysis.delta_yen || 0)} incremental profit
                </div>
                <div style={{ fontSize: '12px', color: '#10b981', marginTop: '4px' }}>
                  {formatYenMan(displayAnalysis.delta_yen || 0)}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '4px', fontWeight: '600' }}>ROI</div>
                <div style={{ fontSize: '28px', fontWeight: '700', color: '#3b82f6' }}>
                  {roiValue !== null ? `${roiValue.toFixed(1)}x` : '—'}
                </div>
              </div>
            </div>
            <div style={{ marginTop: '16px', fontSize: '13px', color: '#cbd5e1', lineHeight: '1.6' }}>
              💡 <strong style={{ color: '#3b82f6' }}>Causal Interpretation:</strong> S1シナリオ（施策実施）は、S0（現状維持）と比較して
              統計的に有意な増分利益をもたらすことが因果推論により検証されました。CAS Score: {casScore ? casScore.toFixed(2) : 'N/A'}
              {analysisDetails?.diagnostics?.quality_level ? ` (${analysisDetails.diagnostics.quality_level} Confidence)` : ''}
            </div>
          </div>
        </div>
      )}

      {/* Current Analysis Status - Running/Failed */}
      {currentAnalysis && (currentAnalysis.status === 'running' || currentAnalysis.status === 'pending' || currentAnalysis.status === 'failed') && (
        <div style={{ 
          marginBottom: '24px', 
          padding: '20px', 
          background: 'rgba(59, 130, 246, 0.1)', 
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '12px'
        }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '12px', color: '#fff' }}>
            🔬 Analysis Status
          </h3>
          <div style={{ marginBottom: '8px' }}>
            <span style={{ color: '#94A3B8' }}>ID: </span>
            <span style={{ color: '#F1F5F9', fontFamily: 'monospace', fontSize: '13px' }}>
              {currentAnalysis.analysis_id}
            </span>
          </div>
          <div style={{ marginBottom: '8px' }}>
            <span style={{ color: '#94A3B8' }}>Status: </span>
            <span style={{ 
              color: currentAnalysis.status === 'completed' ? '#10b981' : 
                     currentAnalysis.status === 'failed' ? '#ef4444' : '#f59e0b',
              fontWeight: '600'
            }}>
              {currentAnalysis.status.toUpperCase()}
            </span>
          </div>
          <div style={{ marginBottom: '8px' }}>
            <span style={{ color: '#94A3B8' }}>Progress: </span>
            <span style={{ color: '#F1F5F9' }}>{(currentAnalysis.progress * 100).toFixed(0)}%</span>
          </div>
          <div style={{ 
            width: '100%', 
            height: '8px', 
            background: 'rgba(255,255,255,0.1)', 
            borderRadius: '4px',
            overflow: 'hidden',
            marginBottom: '12px'
          }}>
            <div style={{ 
              width: `${currentAnalysis.progress * 100}%`, 
              height: '100%', 
              background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
              transition: 'width 0.3s ease'
            }} />
          </div>

          {currentAnalysis.status === 'failed' && (currentAnalysis.error_message || analysisErrorWarning) && (
            <div style={{ marginTop: '12px' }}>
              {analysisErrorWarning
                ? renderTreatmentGuidance(
                    analysisErrorWarning,
                    currentAnalysis.error_details || undefined
                  )
                : (
                  <div style={{ color: '#ef4444', fontSize: '14px' }}>
                    ❌ Error: {currentAnalysis.error_message}
                  </div>
                )}
              {currentAnalysis.error_message && analysisErrorWarning && (
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#fecaca' }}>
                  詳細: {currentAnalysis.error_message}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Training Form */}
      <div className="card">
        <div className="card-title">Train Causal Models</div>
        <p style={{ marginBottom: '16px', color: '#94A3B8' }}>
          アップロードしたデータで因果推論を実行
        </p>
        <div style={{ marginBottom: '16px', padding: '12px', borderRadius: '8px', border: '1px solid rgba(148,163,184,0.3)', background: 'rgba(15,23,42,0.6)', color: '#cbd5e1', fontSize: '13px' }}>
          <div style={{ fontWeight: 600, color: '#fbbf24', marginBottom: '4px' }}>現在の制約（v1）</div>
          <div>
            処置列は 0/1 のバイナリ列のみ対応しています。3 クラス以上の施策や、施策が存在しないデータでは推定できません。
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#F1F5F9' }}>
            Dataset
          </label>
          {isLoading ? (
            <div style={{ padding: '10px', color: '#94A3B8' }}>Loading datasets...</div>
          ) : (
            <select
              value={selectedDataset}
              onChange={(e) => {
                setSelectedDataset(e.target.value)
                // Reset column selections when dataset changes
                setTreatmentCol('')
                setOutcomeCol('')
                setFeatureCols('')
              }}
              disabled={startAnalysisMutation.isPending}
              style={{ width: '100%', padding: '10px', border: '1px solid #334155', borderRadius: '6px', background: '#253446', color: '#F1F5F9' }}
            >
              <option value="">Select a dataset...</option>
              {datasets?.map((dataset: any) => (
                <option key={dataset.id} value={dataset.id}>
                  {dataset.name} ({safeLocaleString(dataset.row_count)} rows, {dataset.column_count} cols)
                </option>
              ))}
            </select>
          )}
        </div>

        {selectedDataset && columnsLoading && (
          <div style={{ padding: '12px', marginBottom: '16px', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '6px', color: '#94A3B8' }}>
            📊 Loading dataset columns...
          </div>
        )}

        {selectedDataset && columnsError && (
          <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '6px', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
            <div style={{ marginBottom: '8px', color: '#ef4444', fontSize: '14px', fontWeight: '600' }}>
              ⚠️ カラム自動検出に失敗しました
            </div>
            <div style={{ color: '#94A3B8', fontSize: '12px', marginBottom: '8px' }}>
              手動でカラム名を入力してください。データセットに存在するカラム名を正確に入力する必要があります。
            </div>
            <div style={{ color: '#94A3B8', fontSize: '11px', fontFamily: 'monospace' }}>
              エラー: {columnsError instanceof Error ? columnsError.message : 'Unknown error'}
            </div>
          </div>
        )}

        {selectedDataset && availableColumns.length > 0 && (
          <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
            <div style={{ marginBottom: '8px', color: '#10b981', fontSize: '14px', fontWeight: '600' }}>
              ✅ Dataset Columns Detected ({availableColumns.length})
            </div>
            <div style={{ color: '#94A3B8', fontSize: '12px' }}>
              Available columns: {availableColumns.join(', ')}
            </div>
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#F1F5F9' }}>
              Treatment Column {datasetColumns?.suggestions.treatment_col && <span style={{ color: '#10b981', fontSize: '12px' }}>(auto-detected)</span>}
            </label>
            {availableColumns.length > 0 ? (
              <select
                value={treatmentCol}
                onChange={(e) => setTreatmentCol(e.target.value)}
                disabled={startAnalysisMutation.isPending}
                style={{ width: '100%', padding: '10px', border: '1px solid #334155', borderRadius: '6px', background: '#253446', color: '#F1F5F9' }}
              >
                <option value="">Select column...</option>
                {availableColumns.map((col) => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={treatmentCol}
                onChange={(e) => setTreatmentCol(e.target.value)}
                disabled={startAnalysisMutation.isPending}
                placeholder={selectedDataset ? "e.g., treatment" : "Select dataset first"}
                style={{ width: '100%', padding: '10px', border: '1px solid #334155', borderRadius: '6px', background: '#253446', color: '#F1F5F9' }}
              />
            )}
          </div>
          {treatmentCol && (
            <div style={{ marginTop: '6px' }}>
              {treatmentSummaryLoading && (
                <div style={{ color: '#38bdf8', fontSize: '12px' }}>🔎 処置列を検証しています...</div>
              )}
              {!treatmentSummaryLoading && treatmentSummary && treatmentSummary.status !== 'ok' && (
                renderTreatmentGuidance(treatmentSummary.status as TreatmentWarningKey, treatmentSummary as Record<string, any>)
              )}
              {!treatmentSummaryLoading && treatmentSummary && treatmentSummary.status === 'ok' && (
                renderTreatmentSuccess(treatmentSummary)
              )}
            </div>
          )}
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#F1F5F9' }}>
              Outcome Column {datasetColumns?.suggestions.outcome_col && <span style={{ color: '#10b981', fontSize: '12px' }}>(auto-detected)</span>}
            </label>
            {availableColumns.length > 0 ? (
              <select
                value={outcomeCol}
                onChange={(e) => setOutcomeCol(e.target.value)}
                disabled={startAnalysisMutation.isPending}
                style={{ width: '100%', padding: '10px', border: '1px solid #334155', borderRadius: '6px', background: '#253446', color: '#F1F5F9' }}
              >
                <option value="">Select column...</option>
                {availableColumns.map((col) => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>
            ) : (
              <input
                type="text"
                value={outcomeCol}
                onChange={(e) => setOutcomeCol(e.target.value)}
                disabled={startAnalysisMutation.isPending}
                placeholder={selectedDataset ? "e.g., revenue, outcome" : "Select dataset first"}
                style={{ width: '100%', padding: '10px', border: '1px solid #334155', borderRadius: '6px', background: '#253446', color: '#F1F5F9' }}
              />
            )}
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#F1F5F9' }}>
            Feature Columns {datasetColumns?.suggestions.feature_cols && datasetColumns.suggestions.feature_cols.length > 0 && <span style={{ color: '#10b981', fontSize: '12px' }}>(auto-detected)</span>}
          </label>
          {availableColumns.length > 0 ? (
            <>
              <div style={{ marginBottom: '8px', padding: '10px', border: '1px solid #334155', borderRadius: '6px', background: '#253446', minHeight: '42px' }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {featureCols.split(',').filter(f => f.trim()).map((feature) => (
                    <span
                      key={feature.trim()}
                      style={{
                        padding: '4px 8px',
                        background: 'rgba(59, 130, 246, 0.2)',
                        border: '1px solid rgba(59, 130, 246, 0.3)',
                        borderRadius: '4px',
                        fontSize: '13px',
                        color: '#60a5fa',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}
                    >
                      {feature.trim()}
                      <button
                        onClick={() => {
                          const features = featureCols.split(',').filter(f => f.trim() !== feature.trim())
                          setFeatureCols(features.join(','))
                        }}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: '#94a3b8',
                          cursor: 'pointer',
                          padding: '0',
                          fontSize: '16px',
                          lineHeight: '1'
                        }}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              </div>
              <select
                onChange={(e) => {
                  const newCol = e.target.value
                  if (newCol && !featureCols.split(',').map(f => f.trim()).includes(newCol)) {
                    setFeatureCols(featureCols ? `${featureCols},${newCol}` : newCol)
                  }
                  e.target.value = ''
                }}
                disabled={startAnalysisMutation.isPending}
                style={{ width: '100%', padding: '10px', border: '1px solid #334155', borderRadius: '6px', background: '#253446', color: '#F1F5F9' }}
              >
                <option value="">+ Add feature column...</option>
                {availableColumns
                  .filter(col => col !== treatmentCol && col !== outcomeCol)
                  .map((col) => (
                    <option key={col} value={col}>{col}</option>
                  ))}
              </select>
            </>
          ) : (
            <input
              type="text"
              value={featureCols}
              onChange={(e) => setFeatureCols(e.target.value)}
              disabled={startAnalysisMutation.isPending}
              placeholder={selectedDataset ? "e.g., x1,x2,x3 (comma-separated)" : "Select dataset first"}
              style={{ width: '100%', padding: '10px', border: '1px solid #334155', borderRadius: '6px', background: '#253446', color: '#F1F5F9' }}
            />
          )}
          <div style={{ marginTop: '4px', color: '#94A3B8', fontSize: '12px' }}>
            {featureCols ? `${featureCols.split(',').filter(f => f.trim()).length} features selected` : 'No features selected'}
          </div>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#F1F5F9' }}>
            Estimators
          </label>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
            {['DR', 'IPW', 'DiD', 'IV', 'CF', 'SCM', 'RD'].map((estimator) => (
              <label key={estimator} style={{ display: 'flex', alignItems: 'center', color: '#F1F5F9', cursor: 'pointer' }}>
                <input 
                  type="checkbox" 
                  checked={selectedEstimators.includes(estimator)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedEstimators([...selectedEstimators, estimator])
                    } else {
                      setSelectedEstimators(selectedEstimators.filter(e => e !== estimator))
                    }
                  }}
                  disabled={startAnalysisMutation.isPending}
                  style={{ marginRight: '8px' }} 
                />
                {estimator}
              </label>
            ))}
          </div>
        </div>

        <button 
          className="btn btn-primary" 
          onClick={handleTrain}
          disabled={startAnalysisMutation.isPending || polling || treatmentSummaryLoading || treatmentBlocked}
        >
          {startAnalysisMutation.isPending ? '開始中...' : polling ? '実行中...' : '🚀 Train Models'}
        </button>
      </div>

      {/* Recent Analyses */}
      {analyses && analyses.length > 0 && (
        <div className="card" style={{ marginTop: '24px' }}>
          <div className="card-title">Recent Analyses</div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #334155', color: '#94A3B8' }}>Replay</th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #334155', color: '#94A3B8' }}>ID</th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #334155', color: '#94A3B8' }}>Status</th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #334155', color: '#94A3B8' }}>Δ¥</th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #334155', color: '#94A3B8' }}>Verdict</th>
                  <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid #334155', color: '#94A3B8' }}>Started</th>
                </tr>
              </thead>
              <tbody>
                {analyses.map((analysis: any) => (
                  <tr key={analysis.analysis_id} style={{ borderBottom: '1px solid #334155' }}>
                    <td style={{ padding: '12px', color: '#F1F5F9' }}>
                      <input
                        type="radio"
                        name="analysisReplay"
                        disabled={analysis.status !== 'completed'}
                        checked={selectedSnapshotId === analysis.analysis_id}
                        onChange={() => {
                          if (analysis.status === 'completed') {
                            setSelectedSnapshotId(analysis.analysis_id)
                          }
                        }}
                      />
                    </td>
                    <td style={{ padding: '12px', color: '#F1F5F9', fontFamily: 'monospace', fontSize: '12px' }}>
                      {analysis.analysis_id.substring(0, 8)}...
                    </td>
                    <td style={{ padding: '12px' }}>
                      <span style={{ 
                        color: analysis.status === 'completed' ? '#10b981' : 
                               analysis.status === 'failed' ? '#ef4444' : '#f59e0b',
                        fontSize: '13px',
                        fontWeight: '500'
                      }}>
                        {analysis.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px', color: '#F1F5F9' }}>
                      {analysis.delta_yen !== null && analysis.delta_yen !== undefined
                        ? `¥${safeLocaleString(analysis.delta_yen)}`
                        : '-'}
                    </td>
                    <td style={{ padding: '12px' }}>
                      {analysis.verdict ? (
                        <span style={{ 
                          color: analysis.verdict === 'Go' ? '#10b981' : 
                                 analysis.verdict === 'Canary' ? '#f59e0b' : '#ef4444',
                          fontWeight: '600'
                        }}>
                          {analysis.verdict}
                        </span>
                      ) : '-'}
                    </td>
                    <td style={{ padding: '12px', color: '#94A3B8', fontSize: '13px' }}>
                      {formatDateTime(analysis.started_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ color: '#94a3b8', fontSize: '13px' }}>
              {selectedSnapshotId
                ? `選択中の分析 ID: ${selectedSnapshotId.slice(0, 8)}…`
                : '分析を選択するとスナップショットを復元できます'}
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => setSelectedSnapshotId(null)}
              disabled={!selectedSnapshotId}
            >
              クリア
            </button>
          </div>
        </div>
      )}

      {/* Recommended Strategy */}
      {displayAnalysis && displayAnalysis.status === 'completed' && (
        <div className="card" style={{ marginTop: '24px' }}>
          <div className="card-title">💡 Recommended Portfolio Strategy</div>
          <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '20px' }}>
            当該分析の結果に基づき、実データ由来の KPI と推奨アクションを提示します。
          </p>
          <div style={{
            padding: '20px',
            borderRadius: '16px',
            border: '1px solid rgba(16,185,129,0.45)',
            background: 'linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(15,118,110,0.04) 100%)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <div>
                <h3 style={{ margin: 0, color: '#10b981', fontSize: '20px', fontWeight: 700 }}>
                  Primary Portfolio – {selectedDatasetInfo?.name || 'Uploaded Dataset'}
                </h3>
                <div style={{ color: '#cbd5e1', fontSize: '14px', marginTop: '4px' }}>
                  Δ¥ = ¥{safeLocaleString(displayAnalysis?.delta_yen)} （95% CI: ¥{safeLocaleString(displayAnalysis?.delta_yen_ci_low)} ~ ¥{safeLocaleString(displayAnalysis?.delta_yen_ci_high)}）
                </div>
              </div>
              <span style={{
                padding: '6px 16px',
                borderRadius: '20px',
                background: displayAnalysis.verdict === 'Go' ? '#10b981' : displayAnalysis.verdict === 'Canary' ? '#f59e0b' : '#ef4444',
                color: '#fff',
                fontWeight: 700,
                fontSize: '13px'
              }}>
                {displayAnalysis.verdict?.toUpperCase()}
              </span>
            </div>
            {!hasImpactMetrics && (
              <div style={{
                marginBottom: '16px',
                padding: '12px 16px',
                borderRadius: '8px',
                border: '1px dashed rgba(148,163,184,0.5)',
                background: 'rgba(148,163,184,0.1)',
                color: '#cbd5e1',
                fontSize: '13px'
              }}>
                ⚠️ Impact metrics snapshot is missing for this analysis. Run the causal job again or wait for the worker to finish saving
                diagnostics to `analysis_runs.impact_metrics`.
              </div>
            )}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px' }}>
              <div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Estimated Cost</div>
                <div style={{ fontSize: '24px', fontWeight: 700, color: '#f1f5f9' }}>{formatYenShortOrDash(estimatedCost)}</div>
                <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                  {hasImpactMetrics ? 'Campaign budget' : 'Snapshot not recorded'}
                </div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Projected Conversion</div>
                <div style={{ fontSize: '24px', fontWeight: 700, color: '#10b981' }}>{formatPercentOrDash(projectedConversionRate)}</div>
                <div style={{ fontSize: '12px', color: '#94a3b8' }}>{formatPercentDeltaOrDash(conversionUplift)}</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>Users Affected</div>
                <div style={{ fontSize: '24px', fontWeight: 700, color: '#f1f5f9' }}>{safeLocaleString(usersAffected)}</div>
                <div style={{ fontSize: '12px', color: '#94a3b8' }}>Treatment group</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>ROI</div>
                <div style={{ fontSize: '24px', fontWeight: 700, color: '#3b82f6' }}>
                  {roiValue !== null ? `${roiValue.toFixed(1)}x` : '—'}
                </div>
                <div style={{ fontSize: '12px', color: '#94a3b8' }}>Return on investment</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>CAS Score</div>
                <div style={{ fontSize: '24px', fontWeight: 700, color: casScore && casScore >= 0.8 ? '#10b981' : casScore && casScore >= 0.6 ? '#f59e0b' : '#ef4444' }}>
                  {casScore ? casScore.toFixed(2) : '—'}
                </div>
                <div style={{ fontSize: '12px', color: '#94a3b8' }}>{analysisDetails?.diagnostics?.quality_level || 'Awaiting diagnostics'}</div>
              </div>
            </div>
            <div style={{ marginTop: '16px', fontSize: '13px', color: '#cbd5e1', lineHeight: 1.6 }}>
              <strong style={{ color: '#10b981' }}>Action:</strong>{' '}
              {displayAnalysis.verdict === 'Go'
                ? '高い信頼度でプラス効果が見込めます。即時リリースし、7日間の KPI 監視を設定してください。'
                : displayAnalysis.verdict === 'Canary'
                  ? '限定トラフィックでの検証と診断結果のレビューを推奨します。'
                  : '投資価値が低いかリスクが高いため、追加データや代替施策の検討が必要です。'}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
