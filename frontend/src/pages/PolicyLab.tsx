import { useEffect, useMemo, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { policiesAPI, Policy } from '../api/v1/policies'
import { datasetsAPI } from '../api/v1/datasets'
import { formatYenShort, formatYenMan } from '../utils/format'
import { useI18n } from '../contexts/I18nContext'

interface CustomScenario {
  name: string
  targetSegment: string
  channel: string[]
  frequency: 'daily' | 'weekly' | 'biweekly' | 'monthly' | 'one-time'
  discountRate: number
  budgetCap: number
  evaluationMetric: string
  duration: number
}

const CHANNEL_OPTIONS = ['Email', 'SMS', 'Push', 'LINE', 'In-App', 'Direct Mail']

const frequencyLabelFromCap = (cap?: number): CustomScenario['frequency'] => {
  if (!cap) return 'weekly'
  if (cap <= 1) return 'one-time'
  if (cap <= 2) return 'weekly'
  if (cap <= 4) return 'biweekly'
  if (cap >= 30) return 'monthly'
  return 'weekly'
}

const capFromFrequencyLabel = (label: CustomScenario['frequency']): number => {
  switch (label) {
    case 'daily':
      return 30
    case 'biweekly':
      return 4
    case 'monthly':
      return 12
    case 'one-time':
      return 1
    case 'weekly':
    default:
      return 2
  }
}

const FREQUENCY_SLIDER_STEPS: Array<{ value: CustomScenario['frequency']; label: string; description: string }> = [
  { value: 'one-time', label: 'One-time', description: '単発施策（1回のみ）' },
  { value: 'weekly', label: 'Weekly', description: '週次〜隔週（最大2回）' },
  { value: 'biweekly', label: 'Bi-weekly', description: '隔週〜月4回' },
  { value: 'monthly', label: 'Monthly', description: '月1回（定期リマインド）' },
  { value: 'daily', label: 'Daily', description: '高頻度（最大30回/月）' },
]

const frequencyToSliderValue = (label: CustomScenario['frequency']): number => {
  const index = FREQUENCY_SLIDER_STEPS.findIndex((step) => step.value === label)
  return index === -1 ? 1 : index
}

const sliderValueToFrequency = (value: number): CustomScenario['frequency'] => {
  const clamped = Math.min(Math.max(Math.round(value), 0), FREQUENCY_SLIDER_STEPS.length - 1)
  return FREQUENCY_SLIDER_STEPS[clamped].value
}

const isValidFrequency = (value: any): value is CustomScenario['frequency'] => {
  return ['daily', 'weekly', 'biweekly', 'monthly', 'one-time'].includes(value)
}

type ColumnType = 'number' | 'category' | 'boolean'

type ConditionOperator =
  | 'gte'
  | 'gt'
  | 'lte'
  | 'lt'
  | 'between'
  | 'eq'
  | 'neq'
  | 'in'
  | 'contains'
  | 'is_true'
  | 'is_false'

interface TargetCondition {
  id: string
  column: string | null
  operator: ConditionOperator
  value: string
  secondaryValue?: string
  joiner: 'AND' | 'OR'
}

const createEmptyCondition = (): TargetCondition => ({
  id: `cond-${Math.random().toString(36).slice(2, 9)}`,
  column: null,
  operator: 'gte',
  value: '',
  secondaryValue: '',
  joiner: 'AND'
})

const inferColumnType = (schemaType?: string): ColumnType => {
  if (!schemaType) return 'category'
  const type = schemaType.toLowerCase()
  if (type.includes('int') || type.includes('float') || type.includes('double') || type.includes('decimal') || type.includes('numeric') || type.includes('real')) {
    return 'number'
  }
  if (type.includes('bool')) {
    return 'boolean'
  }
  return 'category'
}

const getDefaultOperator = (columnType: ColumnType): ConditionOperator => {
  if (columnType === 'number') {
    return 'gte'
  }
  if (columnType === 'boolean') {
    return 'is_true'
  }
  return 'eq'
}

const operatorOptions: Record<ColumnType, { value: ConditionOperator; label: string }[]> = {
  number: [
    { value: 'gte', label: '>= (以上)' },
    { value: 'gt', label: '> (より大きい)' },
    { value: 'lte', label: '<= (以下)' },
    { value: 'lt', label: '< (より小さい)' },
    { value: 'between', label: 'Between (範囲)' }
  ],
  category: [
    { value: 'eq', label: '= (一致)' },
    { value: 'neq', label: '≠ (除外)' },
    { value: 'in', label: 'IN (複数含む)' },
    { value: 'contains', label: 'LIKE %...%' }
  ],
  boolean: [
    { value: 'is_true', label: 'is TRUE' },
    { value: 'is_false', label: 'is FALSE' }
  ]
}

const escapeSqlLiteral = (value: string): string => value.replace(/'/g, "''")

const formatNumericValue = (value: string): number | null => {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

const buildClauseForCondition = (
  condition: TargetCondition,
  columnType: ColumnType
): string | null => {
  if (!condition.column) return null
  const column = condition.column
  const primary = condition.value?.trim() ?? ''
  const secondary = condition.secondaryValue?.trim() ?? ''

  switch (condition.operator) {
    case 'gte': {
      const numeric = formatNumericValue(primary)
      if (numeric === null) return null
      return `${column} >= ${numeric}`
    }
    case 'gt': {
      const numeric = formatNumericValue(primary)
      if (numeric === null) return null
      return `${column} > ${numeric}`
    }
    case 'lte': {
      const numeric = formatNumericValue(primary)
      if (numeric === null) return null
      return `${column} <= ${numeric}`
    }
    case 'lt': {
      const numeric = formatNumericValue(primary)
      if (numeric === null) return null
      return `${column} < ${numeric}`
    }
    case 'between': {
      if (columnType !== 'number') return null
      const min = formatNumericValue(primary)
      const max = formatNumericValue(secondary)
      if (min === null || max === null) return null
      return `${column} BETWEEN ${min} AND ${max}`
    }
    case 'eq':
      if (columnType === 'number') {
        const numeric = formatNumericValue(primary)
        if (numeric === null) return null
        return `${column} = ${numeric}`
      }
      return `${column} = '${escapeSqlLiteral(primary)}'`
    case 'neq':
      if (columnType === 'number') {
        const numeric = formatNumericValue(primary)
        if (numeric === null) return null
        return `${column} <> ${numeric}`
      }
      return `${column} <> '${escapeSqlLiteral(primary)}'`
    case 'in': {
      const values = primary.split(',').map((v) => v.trim()).filter(Boolean)
      if (!values.length) return null
      if (columnType === 'number') {
        const numericValues = values.map((v) => formatNumericValue(v)).filter((v) => v !== null) as number[]
        if (!numericValues.length) return null
        return `${column} IN (${numericValues.join(', ')})`
      }
      return `${column} IN (${values.map((v) => `'${escapeSqlLiteral(v)}'`).join(', ')})`
    }
    case 'contains':
      return `LOWER(${column}) LIKE LOWER('%${escapeSqlLiteral(primary)}%')`
    case 'is_true':
      return `${column} = TRUE`
    case 'is_false':
      return `${column} = FALSE`
    default:
      return null
  }
}

const buildWhereClauseFromConditions = (
  conditions: TargetCondition[],
  schema: Record<string, string> | undefined,
  allowedColumns: string[]
): string => {
  if (!schema || !allowedColumns.length) {
    return ''
  }
  const allowed = new Set(allowedColumns)
  const clauses: string[] = []
  conditions.forEach((condition) => {
    if (!condition.column || !allowed.has(condition.column)) return
    const columnType = inferColumnType(schema[condition.column])
    const clause = buildClauseForCondition(condition, columnType)
    if (!clause) return
    if (clauses.length === 0) {
      clauses.push(clause)
    } else {
      clauses.push(`${condition.joiner} ${clause}`)
    }
  })
  return clauses.join(' ')
}

const FORBIDDEN_SQL_KEYWORDS = ['select', 'insert', 'update', 'delete', 'drop', 'alter']

const SQL_ALLOWED_KEYWORDS = new Set([
  'and',
  'or',
  'not',
  'in',
  'between',
  'like',
  'is',
  'null',
  'true',
  'false',
  'exists',
  'case',
  'when',
  'then',
  'else',
  'end',
  'lower',
  'upper',
  'coalesce'
])

const validateSqlWhereClause = (clause: string, allowedColumns: string[]): string | null => {
  const trimmed = (clause || '').trim()
  if (!trimmed) {
    return 'Target Segment を入力してください'
  }
  const lower = trimmed.toLowerCase()
  for (const keyword of FORBIDDEN_SQL_KEYWORDS) {
    if (lower.includes(`${keyword} `) || lower.includes(`${keyword}\n`) || lower.startsWith(keyword)) {
      return `SQLキーワード "${keyword.toUpperCase()}" は使用できません`
    }
  }
  if (trimmed.includes(';')) {
    return 'セミコロン ";" は使用できません'
  }
  if (!allowedColumns.length) {
    return null
  }
  const sanitized = trimmed.replace(/'[^']*'/g, '')
  const tokens = sanitized.match(/[a-zA-Z_][a-zA-Z0-9_]*/g) || []
  const allowedSet = new Set(allowedColumns.map((col) => col.toLowerCase()))
  for (const token of tokens) {
    const normalized = token.toLowerCase()
    if (allowedSet.has(normalized) || SQL_ALLOWED_KEYWORDS.has(normalized) || /^\d+$/.test(token)) {
      continue
    }
    return `未許可の識別子が含まれています: ${token}`
  }
  return null
}

const buildScenarioSpecFromState = (scenario: CustomScenario) => ({
  apiVersion: 'cqox.ai/v1',
  kind: 'Scenario',
  metadata: {
    name: scenario.name || 'custom-scenario',
    createdAt: new Date().toISOString(),
    type: 'custom'
  },
  spec: {
    target_segment: {
      type: 'sql',
      condition: scenario.targetSegment
    },
    channels: scenario.channel,
    frequency: scenario.frequency,
    discount_rate: scenario.discountRate / 100,
    budget_cap: scenario.budgetCap,
    evaluation_metric: scenario.evaluationMetric,
    duration_days: scenario.duration
  }
})

const scenarioSpecToYaml = (spec: ReturnType<typeof buildScenarioSpecFromState>): string => {
  const channels = (spec.spec.channels || []).map((channel) => `    - ${channel}`).join('\n') || '    -'
  return `# CQOx Scenario Specification
apiVersion: ${spec.apiVersion}
kind: ${spec.kind}
metadata:
  name: ${spec.metadata.name}
  createdAt: ${spec.metadata.createdAt}
  type: ${spec.metadata.type}
spec:
  target_segment:
    type: ${spec.spec.target_segment.type}
    condition: "${spec.spec.target_segment.condition}"
  channels:
${channels}
  frequency: ${spec.spec.frequency}
  discount_rate: ${spec.spec.discount_rate}
  budget_cap: ${spec.spec.budget_cap}
  evaluation_metric: ${spec.spec.evaluation_metric}
  duration_days: ${spec.spec.duration_days}
`
}

const DEFAULT_CUSTOM_SCENARIO: CustomScenario = {
  name: '',
  targetSegment: '',
  channel: [],
  frequency: 'weekly',
  discountRate: 0,
  budgetCap: 1000000,
  evaluationMetric: 'revenue',
  duration: 28
}

export default function PolicyLab() {
  const queryClient = useQueryClient()
  const { t } = useI18n()
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null)
  const [editMode, setEditMode] = useState(false)
  const [configContent, setConfigContent] = useState('')
  const [activeTab, setActiveTab] = useState<'predefined' | 'custom'>('predefined')
  const [showScenarioSimulator, setShowScenarioSimulator] = useState(false)
  const [scenarioName, setScenarioName] = useState('')
  const [selectedPolicyIds, setSelectedPolicyIds] = useState<string[]>([])
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newPolicy, setNewPolicy] = useState({
    name: '',
    description: '',
    dataset_id: '',
    channels: [] as string[],
    target_rule: 'propensity_score >= 0.5',
    budget_limit: 500000,
    frequency_cap: 2
  })

  // Custom Scenario State
  const [customScenario, setCustomScenario] = useState<CustomScenario>({ ...DEFAULT_CUSTOM_SCENARIO })
  const [isApplyingScenario, setIsApplyingScenario] = useState(false)
  const [scenarioEditorTab, setScenarioEditorTab] = useState<'quick' | 'precise' | 'advanced'>('quick')
  const [targetBuilderMode, setTargetBuilderMode] = useState<'builder' | 'sql'>('builder')
  const [targetConditions, setTargetConditions] = useState<TargetCondition[]>([createEmptyCondition()])
  const [builderTouched, setBuilderTouched] = useState(false)
  const [sqlValidationError, setSqlValidationError] = useState<string | null>(null)
  const [scenarioSpecDraft, setScenarioSpecDraft] = useState(JSON.stringify(buildScenarioSpecFromState(DEFAULT_CUSTOM_SCENARIO), null, 2))
  const [scenarioSpecDirty, setScenarioSpecDirty] = useState(false)

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: () => datasetsAPI.list()
  })

  const selectedDatasetId = selectedPolicy?.dataset_id
  const { data: selectedDatasetColumns, isLoading: columnsLoading } = useQuery({
    queryKey: ['policy-target-columns', selectedDatasetId],
    queryFn: async () => {
      if (!selectedDatasetId) {
        throw new Error('dataset not selected')
      }
      return await datasetsAPI.getColumns(selectedDatasetId)
    },
    enabled: !!selectedDatasetId,
    staleTime: 60_000
  })

  const allowedTargetColumns = selectedDatasetColumns?.columns || []

  const builderGeneratedSql = useMemo(() => {
    return buildWhereClauseFromConditions(targetConditions, selectedDatasetColumns?.schema, allowedTargetColumns)
  }, [targetConditions, selectedDatasetColumns, allowedTargetColumns])

  const selectedDatasetMeta = useMemo(() => {
    if (!selectedDatasetId || !datasets) return null
    return datasets.find((ds) => ds.id === selectedDatasetId) || null
  }, [selectedDatasetId, datasets])

  const scenarioSpecObject = useMemo(() => buildScenarioSpecFromState(customScenario), [customScenario])
  const frequencySliderValue = frequencyToSliderValue(customScenario.frequency)

  const updateCondition = (id: string, updater: (condition: TargetCondition) => TargetCondition) => {
    setTargetConditions((prev) => prev.map((condition) => (condition.id === id ? updater(condition) : condition)))
    setBuilderTouched(true)
    setTargetBuilderMode('builder')
    setSqlValidationError(null)
  }

  const handleConditionColumnChange = (id: string, column: string | null) => {
    updateCondition(id, (condition) => {
      if (!column) {
        return { ...condition, column: null }
      }
      const columnType = inferColumnType(selectedDatasetColumns?.schema?.[column])
      return {
        ...condition,
        column,
        operator: getDefaultOperator(columnType),
        value: '',
        secondaryValue: ''
      }
    })
  }

  const handleConditionOperatorChange = (id: string, operator: ConditionOperator) => {
    updateCondition(id, (condition) => ({
      ...condition,
      operator,
      secondaryValue: operator === 'between' ? condition.secondaryValue : ''
    }))
  }

  const handleConditionValueChange = (id: string, value: string, field: 'value' | 'secondary' = 'value') => {
    updateCondition(id, (condition) => ({
      ...condition,
      [field === 'value' ? 'value' : 'secondaryValue']: value
    }))
  }

  const handleConditionJoinerChange = (id: string, joiner: 'AND' | 'OR') => {
    updateCondition(id, (condition) => ({
      ...condition,
      joiner
    }))
  }

  const addConditionRow = () => {
    setTargetConditions((prev) => [...prev, createEmptyCondition()])
    setBuilderTouched(true)
    setTargetBuilderMode('builder')
  }

  const removeConditionRow = (id: string) => {
    setTargetConditions((prev) => {
      if (prev.length === 1) {
        return [createEmptyCondition()]
      }
      return prev.filter((condition) => condition.id !== id)
    })
    setBuilderTouched(true)
    setTargetBuilderMode('builder')
  }

  const handleSqlInputChange = (value: string) => {
    setCustomScenario((prev) => ({ ...prev, targetSegment: value }))
    const error = validateSqlWhereClause(value, allowedTargetColumns)
    setSqlValidationError(error)
  }

  const resetCustomScenarioForm = () => {
    setCustomScenario({ ...DEFAULT_CUSTOM_SCENARIO })
    setTargetConditions([createEmptyCondition()])
    setBuilderTouched(false)
    setTargetBuilderMode('builder')
    setScenarioEditorTab('quick')
    setSqlValidationError(null)
    setScenarioSpecDraft(JSON.stringify(buildScenarioSpecFromState(DEFAULT_CUSTOM_SCENARIO), null, 2))
    setScenarioSpecDirty(false)
  }

  const handleScenarioSpecDraftChange = (value: string) => {
    setScenarioSpecDraft(value)
    setScenarioSpecDirty(true)
  }

  const handleScenarioSpecApply = () => {
    try {
      const parsed = JSON.parse(scenarioSpecDraft)
      const spec = parsed?.spec || {}
      const metadata = parsed?.metadata || {}
      const candidateFrequency = spec.frequency
      const normalizedFrequency: CustomScenario['frequency'] = isValidFrequency(candidateFrequency)
        ? candidateFrequency
        : customScenario.frequency

      const nextScenario: CustomScenario = {
        ...customScenario,
        name: typeof metadata.name === 'string' ? metadata.name : customScenario.name,
        targetSegment: spec?.target_segment?.condition || customScenario.targetSegment,
        channel: Array.isArray(spec.channels)
          ? spec.channels.filter((channel: unknown): channel is string => typeof channel === 'string')
          : customScenario.channel,
        frequency: normalizedFrequency,
        discountRate:
          typeof spec.discount_rate === 'number'
            ? Math.round(spec.discount_rate * 100)
            : customScenario.discountRate,
        budgetCap:
          typeof spec.budget_cap === 'number'
            ? spec.budget_cap
            : customScenario.budgetCap,
        evaluationMetric:
          typeof spec.evaluation_metric === 'string'
            ? spec.evaluation_metric
            : customScenario.evaluationMetric,
        duration:
          typeof spec.duration_days === 'number'
            ? spec.duration_days
            : customScenario.duration
      }

      setCustomScenario(nextScenario)
      setScenarioSpecDirty(false)
      setTargetBuilderMode('sql')
      setBuilderTouched(false)
      setTargetConditions([createEmptyCondition()])
      setSqlValidationError(validateSqlWhereClause(nextScenario.targetSegment, allowedTargetColumns))
      alert('ScenarioSpec JSON をフォームに反映しました。')
    } catch (error: any) {
      alert(`ScenarioSpec JSON の解析に失敗しました: ${error?.message || error}`)
    }
  }

  const handleFrequencySliderChange = (value: number) => {
    setCustomScenario((prev) => ({
      ...prev,
      frequency: sliderValueToFrequency(value)
    }))
  }

  const toggleScenarioChannel = (channel: string) => {
    setCustomScenario((prev) => {
      const exists = prev.channel.includes(channel)
      return {
        ...prev,
        channel: exists ? prev.channel.filter((c) => c !== channel) : [...prev.channel, channel]
      }
    })
  }

  useEffect(() => {
    if (!newPolicy.dataset_id && datasets && datasets.length > 0) {
      setNewPolicy((prev) => ({ ...prev, dataset_id: datasets[0].id }))
    }
  }, [datasets, newPolicy.dataset_id])

  useEffect(() => {
    if (targetBuilderMode === 'builder' && builderTouched) {
      setCustomScenario((prev) => {
        if (prev.targetSegment === builderGeneratedSql) {
          return prev
        }
        return { ...prev, targetSegment: builderGeneratedSql }
      })
      setSqlValidationError(null)
      setBuilderTouched(false)
    }
  }, [builderGeneratedSql, targetBuilderMode, builderTouched])

  useEffect(() => {
    if (targetBuilderMode === 'sql') {
      setSqlValidationError(validateSqlWhereClause(customScenario.targetSegment, allowedTargetColumns))
    }
  }, [customScenario.targetSegment, allowedTargetColumns, targetBuilderMode])

  useEffect(() => {
    if (!scenarioSpecDirty) {
      setScenarioSpecDraft(JSON.stringify(buildScenarioSpecFromState(customScenario), null, 2))
    }
  }, [customScenario, scenarioSpecDirty])

  const { data, isLoading, error } = useQuery<Policy[]>({
    queryKey: ['policies'],
    queryFn: async () => {
      const response = await policiesAPI.list()
      return response
    },
  })

  const evaluateMutation = useMutation({
    mutationFn: (policyId: string) => policiesAPI.evaluateOffline(policyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] })
    }
  })

  const createPolicyMutation = useMutation({
    mutationFn: (payload: Partial<Policy>) => policiesAPI.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      setShowCreateModal(false)
      setNewPolicy({
        name: '',
        description: '',
        dataset_id: datasets && datasets.length > 0 ? datasets[0].id : '',
        channels: [],
        target_rule: 'propensity_score >= 0.5',
        budget_limit: 500000,
        frequency_cap: 2
      })
    }
  })

  const scenarioMutation = useMutation({
    mutationFn: () => policiesAPI.simulateScenario(scenarioName, selectedPolicyIds),
  })

  useEffect(() => {
    if (!selectedPolicy) return
    setScenarioName(selectedPolicy.name)
    setCustomScenario((prev) => ({
      ...prev,
      name: selectedPolicy.name,
      targetSegment: selectedPolicy.target_rule || '',
      channel: selectedPolicy.channels || [],
      frequency: frequencyLabelFromCap(selectedPolicy.frequency_cap),
      discountRate: Math.round(((selectedPolicy.offer_config as any)?.discount_rate ?? 0) * 100),
      budgetCap: selectedPolicy.budget_limit ?? prev.budgetCap,
      evaluationMetric: ((selectedPolicy.objectives as any)?.primary as string) || prev.evaluationMetric,
      duration: ((selectedPolicy.objectives as any)?.duration_days as number) || prev.duration
    }))
    setScenarioSpecDirty(false)
    setTargetBuilderMode('sql')
    setBuilderTouched(false)
    setSqlValidationError(null)
    setTargetConditions([createEmptyCondition()])
  }, [selectedPolicy])

  if (isLoading) {
    return (
      <div style={{ padding: '32px', color: '#cbd5e0' }}>
        Loading policies...
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ padding: '32px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px' }}>
          Policy Lab
        </h1>
        <div style={{ 
          background: 'rgba(245, 87, 108, 0.1)', 
          border: '1px solid rgba(245, 87, 108, 0.3)',
          borderRadius: '8px',
          padding: '16px',
          color: '#f5576c'
        }}>
          <div style={{ fontWeight: '600', marginBottom: '8px' }}>データ取得エラー</div>
          <div style={{ fontSize: '14px', opacity: 0.7 }}>
            バックエンドAPIに接続できません。Docker Composeが起動していることを確認してください。
          </div>
        </div>
      </div>
    )
  }

  const policies = data || []

  const handlePolicySelect = (policy: Policy) => {
    setSelectedPolicy(policy)
    setEditMode(false)
    const payload = {
      name: policy.name,
      description: policy.description || '',
      dataset_id: policy.dataset_id,
      target_rule: policy.target_rule || 'propensity_score >= 0.5',
      offer_config: policy.offer_config || { type: 'coupon', value: 1000 },
      channels: policy.channels || [],
      frequency_cap: policy.frequency_cap || 1,
      budget_limit: policy.budget_limit || 0,
      objectives: policy.objectives || { primary: 'incremental_profit', type: 'custom' },
      risk_constraints: policy.risk_constraints || { max_cpi: 800 }
    }
    setConfigContent(JSON.stringify(payload, null, 2))
  }

  const applyCustomScenarioToPolicy = async () => {
    if (!selectedPolicy) {
      alert('編集するポリシーを選択してください')
      return
    }
    const clause = (customScenario.targetSegment || '').trim()
    if (!clause) {
      alert('Target Segment (SQL) を入力してください')
      return
    }
    const clauseError = validateSqlWhereClause(clause, allowedTargetColumns)
    if (clauseError) {
      setSqlValidationError(clauseError)
      alert(clauseError)
      return
    }

    setIsApplyingScenario(true)
    try {
      await policiesAPI.update(selectedPolicy.id, {
        target_rule: clause,
        channels: customScenario.channel,
        frequency_cap: capFromFrequencyLabel(customScenario.frequency),
        budget_limit: customScenario.budgetCap,
        objectives: {
          ...(selectedPolicy.objectives || {}),
          primary: customScenario.evaluationMetric,
          duration_days: customScenario.duration,
        },
        offer_config: {
          ...(selectedPolicy.offer_config || {}),
          discount_rate: customScenario.discountRate / 100,
        },
      })
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      alert('Scenario Builderの内容をポリシーに適用しました。')
    } catch (error) {
      console.error(error)
      alert('シナリオの適用に失敗しました。')
    } finally {
      setIsApplyingScenario(false)
    }
  }

  const handleSavePolicy = async () => {
    if (!selectedPolicy) return
    try {
      const payload = JSON.parse(configContent)
      if (!payload.name || !payload.dataset_id) {
        alert('name と dataset_id は必須です')
        return
      }
      await policiesAPI.update(selectedPolicy.id, payload)
      queryClient.invalidateQueries({ queryKey: ['policies'] })
      setEditMode(false)
    } catch (error) {
      console.error(error)
      alert('ポリシーの保存に失敗しました。JSON形式が正しいか確認してください。')
    }
  }

  const handleCreatePolicy = () => {
    if (!newPolicy.name || !newPolicy.dataset_id) {
      alert('名前とデータセットは必須です')
      return
    }
    createPolicyMutation.mutate({
      name: newPolicy.name,
      description: newPolicy.description,
      dataset_id: newPolicy.dataset_id,
      target_rule: newPolicy.target_rule,
      channels: newPolicy.channels,
      frequency_cap: newPolicy.frequency_cap,
      budget_limit: Number(newPolicy.budget_limit),
      offer_config: { type: 'coupon', value: 1000 },
      objectives: { primary: 'incremental_profit', type: 'custom' },
      risk_constraints: { max_cpi: 800 }
    })
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '8px' }}>{t('policyLab.title')}</h1>
        <p style={{ color: '#94a3b8', fontSize: '16px', marginBottom: '24px' }}>
          {t('policyLab.subtitle')}
        </p>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '16px' }}>
          <button
            onClick={() => setShowCreateModal(true)}
            style={{
              padding: '10px 18px',
              borderRadius: '8px',
              border: 'none',
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              color: '#fff',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            ＋ {t('policyLab.create')}
          </button>
        </div>

        {showCreateModal && (
          <div style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15,23,42,0.7)',
            zIndex: 1000,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <div style={{
              width: 'min(500px, 90vw)',
              background: '#0f172a',
              borderRadius: '16px',
              border: '1px solid #334155',
              padding: '24px',
              color: '#f8fafc',
              boxShadow: '0 20px 60px rgba(0,0,0,0.4)'
            }}>
              <h3 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '12px' }}>新規ポリシー作成</h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '16px' }}>
                <label>
                  <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '4px' }}>データセット</div>
                  <select
                    value={newPolicy.dataset_id}
                    onChange={(e) => setNewPolicy((prev) => ({ ...prev, dataset_id: e.target.value }))}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #334155', background: '#1e293b', color: '#f1f5f9' }}
                  >
                    {datasets && datasets.length > 0 ? (
                      datasets.map((ds) => (
                        <option key={ds.id} value={ds.id}>{ds.name}</option>
                      ))
                    ) : (
                      <option value="">データセットがありません</option>
                    )}
                  </select>
                </label>

                <label>
                  <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '4px' }}>ポリシー名 *</div>
                  <input
                    type="text"
                    value={newPolicy.name}
                    onChange={(e) => setNewPolicy((prev) => ({ ...prev, name: e.target.value }))}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #334155', background: '#1e293b', color: '#f1f5f9' }}
                  />
                </label>

                <label>
                  <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '4px' }}>説明</div>
                  <textarea
                    rows={2}
                    value={newPolicy.description}
                    onChange={(e) => setNewPolicy((prev) => ({ ...prev, description: e.target.value }))}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #334155', background: '#1e293b', color: '#f1f5f9' }}
                  />
                </label>

                <label>
                  <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '4px' }}>ターゲットルール</div>
                  <input
                    type="text"
                    value={newPolicy.target_rule}
                    onChange={(e) => setNewPolicy((prev) => ({ ...prev, target_rule: e.target.value }))}
                    style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #334155', background: '#1e293b', color: '#f1f5f9' }}
                  />
                </label>

    <div>
                  <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '6px' }}>チャネル *</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {CHANNEL_OPTIONS.map((channel) => {
                      const checked = newPolicy.channels.includes(channel)
                      return (
                        <label
                          key={channel}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '8px 12px',
                            borderRadius: '8px',
                            border: `1px solid ${checked ? '#3b82f6' : '#334155'}`,
                            background: checked ? 'rgba(59,130,246,0.15)' : '#1e293b',
                            color: '#e2e8f0',
                            cursor: 'pointer'
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setNewPolicy((prev) => ({ ...prev, channels: [...prev.channels, channel] }))
                              } else {
                                setNewPolicy((prev) => ({ ...prev, channels: prev.channels.filter((c) => c !== channel) }))
                              }
                            }}
                          />
                          {channel}
                        </label>
                      )
                    })}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '12px' }}>
                  <label style={{ flex: 1 }}>
                    <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '4px' }}>予算上限 (¥)</div>
                    <input
                      type="number"
                      min={0}
                      value={newPolicy.budget_limit}
                      onChange={(e) => setNewPolicy((prev) => ({ ...prev, budget_limit: Number(e.target.value) }))}
                      style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #334155', background: '#1e293b', color: '#f1f5f9' }}
                    />
                  </label>
                  <label style={{ flex: 1 }}>
                    <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '4px' }}>Frequency Cap</div>
                    <input
                      type="number"
                      min={1}
                      value={newPolicy.frequency_cap}
                      onChange={(e) => setNewPolicy((prev) => ({ ...prev, frequency_cap: Number(e.target.value) }))}
                      style={{ width: '100%', padding: '10px', borderRadius: '8px', border: '1px solid #334155', background: '#1e293b', color: '#f1f5f9' }}
                    />
                  </label>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button
                  onClick={() => setShowCreateModal(false)}
                  style={{ padding: '10px 16px', borderRadius: '8px', border: '1px solid #475569', background: 'transparent', color: '#e2e8f0' }}
                  disabled={createPolicyMutation.isPending}
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreatePolicy}
                  disabled={createPolicyMutation.isPending || !newPolicy.name || !newPolicy.dataset_id || newPolicy.channels.length === 0}
                  style={{
                    padding: '10px 16px',
                    borderRadius: '8px',
                    border: 'none',
                    background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
                    color: '#fff',
                    fontWeight: 600,
                    opacity: createPolicyMutation.isPending || !newPolicy.name || !newPolicy.dataset_id || newPolicy.channels.length === 0 ? 0.6 : 1,
                    cursor: createPolicyMutation.isPending || !newPolicy.name || !newPolicy.dataset_id || newPolicy.channels.length === 0 ? 'not-allowed' : 'pointer'
                  }}
                >
                  {createPolicyMutation.isPending ? 'Creating...' : 'Create'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div style={{ display: 'flex', gap: '12px', borderBottom: '2px solid #334155', marginBottom: '24px' }}>
          <button
            onClick={() => setActiveTab('predefined')}
            style={{
              padding: '12px 24px',
              background: activeTab === 'predefined' ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'transparent',
              border: 'none',
              borderBottom: activeTab === 'predefined' ? '3px solid #3b82f6' : '3px solid transparent',
              borderRadius: '8px 8px 0 0',
              color: activeTab === 'predefined' ? '#fff' : '#94a3b8',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            📋 Predefined Scenarios
          </button>
          <button
            onClick={() => setActiveTab('custom')}
            style={{
              padding: '12px 24px',
              background: activeTab === 'custom' ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'transparent',
              border: 'none',
              borderBottom: activeTab === 'custom' ? '3px solid #3b82f6' : '3px solid transparent',
              borderRadius: '8px 8px 0 0',
              color: activeTab === 'custom' ? '#fff' : '#94a3b8',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            ⚡ Custom Scenario Builder
          </button>
        </div>
      </div>

      {/* Predefined Scenarios Tab */}
      {activeTab === 'predefined' && (
        <div style={{ marginBottom: '24px', display: 'flex', gap: '12px' }}>
          <button
            onClick={() => setShowScenarioSimulator(false)}
            style={{
              padding: '10px 20px',
              background: !showScenarioSimulator ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'transparent',
              border: `1px solid ${!showScenarioSimulator ? '#3b82f6' : '#334155'}`,
              borderRadius: '8px',
              color: !showScenarioSimulator ? '#fff' : '#94a3b8',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            📋 Policy List
          </button>
          <button
            onClick={() => setShowScenarioSimulator(true)}
            style={{
              padding: '10px 20px',
              background: showScenarioSimulator ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'transparent',
              border: `1px solid ${showScenarioSimulator ? '#3b82f6' : '#334155'}`,
              borderRadius: '8px',
              color: showScenarioSimulator ? '#fff' : '#94a3b8',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            🎯 Scenario Simulator
          </button>
        </div>
      )}

      {activeTab === 'predefined' && showScenarioSimulator && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%)',
          border: '1px solid rgba(139, 92, 246, 0.3)',
          borderRadius: '16px',
          padding: '32px',
          marginBottom: '32px'
        }}>
          <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '16px', color: '#fff' }}>
            🎯 Scenario Simulator
          </h2>
          <p style={{ color: '#cbd5e1', marginBottom: '24px' }}>
            Compare multiple policies and optimize your portfolio
          </p>

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#f1f5f9' }}>
              Scenario Name
            </label>
            <input
              type="text"
              value={scenarioName}
              onChange={(e) => setScenarioName(e.target.value)}
              placeholder="e.g., Q1 Campaign Portfolio"
              style={{
                width: '100%',
                padding: '12px',
                background: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#f1f5f9',
                fontSize: '14px'
              }}
            />
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', marginBottom: '12px', fontWeight: '500', color: '#f1f5f9' }}>
              Select Policies to Include
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '12px' }}>
              {policies.map((policy: Policy) => (
                <label
                  key={policy.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '12px',
                    background: selectedPolicyIds.includes(policy.id) ? 'rgba(139, 92, 246, 0.2)' : '#1e293b',
                    border: `1px solid ${selectedPolicyIds.includes(policy.id) ? 'rgba(139, 92, 246, 0.5)' : '#334155'}`,
                    borderRadius: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedPolicyIds.includes(policy.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedPolicyIds([...selectedPolicyIds, policy.id])
                      } else {
                        setSelectedPolicyIds(selectedPolicyIds.filter(id => id !== policy.id))
                      }
                    }}
                    style={{ marginRight: '12px' }}
                  />
                  <div>
                    <div style={{ fontWeight: '600', color: '#f1f5f9', fontSize: '14px' }}>
                      {policy.name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '4px' }}>
                      {policy.status}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <button
            onClick={() => scenarioMutation.mutate()}
            disabled={!scenarioName || selectedPolicyIds.length === 0 || scenarioMutation.isPending}
            className="btn btn-primary"
            style={{ width: '100%' }}
          >
            {scenarioMutation.isPending ? 'Simulating...' : '▶ Run Scenario Simulation'}
          </button>

          {scenarioMutation.data ? (
            <div style={{
              marginTop: '24px',
              padding: '24px',
              background: '#1e293b',
              borderRadius: '12px',
              border: '1px solid #334155'
            }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px', color: '#fff' }}>
                Simulation Results
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Total Incremental Profit</div>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#10b981' }}>
                    {formatYenShort((scenarioMutation.data as Record<string, any>).total_incremental_profit || 0)}
                  </div>
                  <div style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                    {formatYenMan((scenarioMutation.data as Record<string, any>).total_incremental_profit || 0)}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Portfolio ROI</div>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#3b82f6' }}>
                    {(((scenarioMutation.data as Record<string, any>).total_roi || 0) * 100).toFixed(1)}%
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Risk Score</div>
                  <div style={{ fontSize: '24px', fontWeight: '700', color: '#f59e0b' }}>
                    {((scenarioMutation.data as Record<string, any>).total_risk || 0).toFixed(2)}
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* Policy List and Details */}
      {activeTab === 'predefined' && !showScenarioSimulator && (
        <div style={{ display: 'grid', gridTemplateColumns: selectedPolicy ? '1fr 1fr' : '1fr', gap: '24px' }}>

          {/* Policy List */}
          <div style={{ background: '#1e293b', borderRadius: '16px', padding: '24px', border: '1px solid #334155' }}>
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '20px', color: '#fff' }}>
              Policies ({policies.length})
            </h2>
            <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
              {policies.length === 0 ? (
                <div style={{ padding: '48px', textAlign: 'center', color: '#64748b' }}>
                  <div style={{ fontSize: '16px', marginBottom: '8px' }}>No policies yet</div>
                  <div style={{ fontSize: '14px' }}>Create your first policy to get started</div>
                </div>
              ) : (
                policies.map((policy: Policy) => (
                  <div
                    key={policy.id}
                    onClick={() => handlePolicySelect(policy)}
                    style={{
                      padding: '16px',
                      marginBottom: '12px',
                      background: selectedPolicy?.id === policy.id ? 'rgba(59, 130, 246, 0.1)' : '#0f172a',
                      border: `1px solid ${selectedPolicy?.id === policy.id ? 'rgba(59, 130, 246, 0.5)' : '#1e293b'}`,
                      borderRadius: '12px',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
                      <div style={{ fontWeight: '600', color: '#f1f5f9', fontSize: '15px' }}>
                        {policy.name}
                      </div>
                      <span style={{
                        padding: '4px 10px',
                        borderRadius: '12px',
                        fontSize: '11px',
                        fontWeight: '600',
                        background: policy.status === 'completed' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(100, 116, 139, 0.2)',
                        color: policy.status === 'completed' ? '#10b981' : '#94a3b8',
                        textTransform: 'uppercase'
                      }}>
                    {policy.status || 'draft'}
                  </span>
                    </div>
                    <div style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '8px' }}>
                      {policy.description || 'No description'}
                    </div>
                    <div style={{ display: 'flex', gap: '12px', fontSize: '12px', color: '#64748b' }}>
                      <span>Dataset: {policy.dataset_id?.substring(0, 8)}...</span>
                      <span>•</span>
                      <span>Channels: {policy.channels?.length || 0}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Policy Details */}
          {selectedPolicy && (
            <div style={{ background: '#1e293b', borderRadius: '16px', padding: '24px', border: '1px solid #334155' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#fff' }}>
                  Policy Details
                </h2>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => setEditMode(!editMode)}
                    style={{
                      padding: '8px 16px',
                      background: editMode ? 'rgba(239, 68, 68, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                      border: `1px solid ${editMode ? 'rgba(239, 68, 68, 0.5)' : 'rgba(59, 130, 246, 0.5)'}`,
                      borderRadius: '8px',
                      color: editMode ? '#ef4444' : '#3b82f6',
                      fontSize: '14px',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    {editMode ? 'Cancel' : '✏ Edit JSON'}
                  </button>
                  <button
                    onClick={() => evaluateMutation.mutate(selectedPolicy.id)}
                    disabled={evaluateMutation.isPending}
                    style={{
                      padding: '8px 16px',
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      border: 'none',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    {evaluateMutation.isPending ? '⏳ Evaluating...' : '▶ Evaluate (OPE)'}
                  </button>
                </div>
              </div>

              {editMode ? (
                <div>
                  <textarea
                    value={configContent}
                    onChange={(e) => setConfigContent(e.target.value)}
                    style={{
                      width: '100%',
                      minHeight: '400px',
                      padding: '16px',
                      background: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f1f5f9',
                      fontSize: '13px',
                      fontFamily: 'monospace',
                      resize: 'vertical'
                    }}
                  />
                  <button
                    style={{
                      marginTop: '16px',
                      padding: '10px 20px',
                      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      border: 'none',
                      borderRadius: '8px',
                      color: 'white',
                      fontSize: '14px',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                    onClick={handleSavePolicy}
                  >
                    💾 Save Changes
                  </button>
                </div>
              ) : (
                <div>
                  <div style={{ marginBottom: '24px' }}>
                    <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '1px' }}>
                      Policy Configuration
                    </div>
                    <pre style={{
                      padding: '16px',
                      background: '#0f172a',
                      border: '1px solid #1e293b',
                      borderRadius: '8px',
                      color: '#cbd5e1',
                      fontSize: '13px',
                      fontFamily: 'monospace',
                      overflow: 'auto',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {configContent}
                    </pre>
                  </div>

                  {evaluateMutation.data ? (
                    <div style={{
                      padding: '20px',
                      background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                      borderRadius: '12px'
                    }}>
                      <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', color: '#10b981' }}>
                        📊 Offline Policy Evaluation Results
                      </h3>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                        <div>
                          <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>Expected Incremental Profit</div>
                          <div style={{ fontSize: '20px', fontWeight: '700', color: '#10b981' }}>
                            {formatYenShort((evaluateMutation.data as Record<string, any>).expected_incremental_profit || 0)}
                          </div>
                          <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                            {formatYenMan((evaluateMutation.data as Record<string, any>).expected_incremental_profit || 0)}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>ROI</div>
                          <div style={{ fontSize: '20px', fontWeight: '700', color: '#3b82f6' }}>
                            {(((evaluateMutation.data as Record<string, any>).roi || 0) * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>CAS Score</div>
                          <div style={{ fontSize: '20px', fontWeight: '700', color: '#f59e0b' }}>
                            {(((evaluateMutation.data as Record<string, any>).cas_score || 0) * 100).toFixed(0)}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '4px' }}>CVaR (α=0.05)</div>
                          <div style={{ fontSize: '20px', fontWeight: '700', color: '#ef4444' }}>
                            {formatYenShort(((evaluateMutation.data as Record<string, any>).risk as Record<string, any>)?.cvar_alpha_0_05 || 0)}
                          </div>
                          <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                            {formatYenMan(((evaluateMutation.data as Record<string, any>).risk as Record<string, any>)?.cvar_alpha_0_05 || 0)}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : null}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Custom Scenario Builder Tab */}
      {activeTab === 'custom' && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(16, 185, 129, 0.1) 100%)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '16px',
          padding: '32px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '24px' }}>
            <div>
              <h2 style={{ fontSize: '24px', fontWeight: '700', marginBottom: '8px', color: '#fff' }}>
                ⚡ Custom Scenario Builder
              </h2>
              <p style={{ color: '#cbd5e1', maxWidth: '640px' }}>
                GUI で条件を組み立て → SQL をプレビュー → ScenarioSpec として出力、までを1画面で完結できます。
              </p>
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{
                padding: '8px 14px',
                borderRadius: '999px',
                border: '1px solid rgba(148,163,184,0.3)',
                background: '#0f172a',
                color: '#f8fafc',
                fontSize: '12px'
              }}>
                Policy: {selectedPolicy ? selectedPolicy.name : '未選択'}
              </span>
              <span style={{
                padding: '8px 14px',
                borderRadius: '999px',
                border: '1px solid rgba(148,163,184,0.3)',
                background: '#0f172a',
                color: '#f8fafc',
                fontSize: '12px'
              }}>
                Dataset: {selectedDatasetMeta ? selectedDatasetMeta.name : '未選択'}
              </span>
              <span style={{
                padding: '8px 14px',
                borderRadius: '999px',
                border: '1px solid rgba(148,163,184,0.3)',
                background: '#0f172a',
                color: '#f8fafc',
                fontSize: '12px'
              }}>
                Columns: {columnsLoading ? 'loading...' : `${allowedTargetColumns.length} fields`}
              </span>
            </div>
          </div>

          <div style={{ display: 'grid', gap: '24px' }}>
            {/* Scenario configuration */}
            <section style={{
              borderRadius: '16px',
              border: '1px solid rgba(148,163,184,0.3)',
              background: '#0f172a',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}>
              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontWeight: 600, color: '#e2e8f0', fontSize: '14px' }}>
                  📝 Scenario Name *
                </label>
                <input
                  type="text"
                  value={customScenario.name}
                  onChange={(e) => setCustomScenario({ ...customScenario, name: e.target.value })}
                  placeholder="例: High-Value Weekend Campaign"
                  style={{
                    width: '100%',
                    padding: '12px',
                    borderRadius: '10px',
                    border: '1px solid #1e293b',
                    background: '#020617',
                    color: '#f8fafc',
                    fontSize: '14px'
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: '8px', border: '1px solid #1e293b', borderRadius: '12px', padding: '4px', alignSelf: 'flex-start' }}>
                {(['quick', 'precise', 'advanced'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setScenarioEditorTab(tab)}
                    style={{
                      border: 'none',
                      borderRadius: '10px',
                      padding: '8px 16px',
                      cursor: 'pointer',
                      fontWeight: 600,
                      color: scenarioEditorTab === tab ? '#fff' : '#94a3b8',
                      background: scenarioEditorTab === tab
                        ? tab === 'advanced'
                          ? 'linear-gradient(135deg,#a855f7,#6366f1)'
                          : 'linear-gradient(135deg,#3b82f6,#06b6d4)'
                        : 'transparent'
                    }}
                  >
                    {tab === 'quick' && '⚡ Quick'}
                    {tab === 'precise' && '🧮 Precise'}
                    {tab === 'advanced' && '🧾 Advanced'}
                  </button>
                ))}
              </div>

              {scenarioEditorTab === 'quick' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: '20px' }}>
                  <div>
                    <div style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '6px' }}>🔄 Contact Frequency</div>
                    <input
                      type="range"
                      min={0}
                      max={FREQUENCY_SLIDER_STEPS.length - 1}
                      step={1}
                      value={frequencySliderValue}
                      onChange={(e) => handleFrequencySliderChange(Number(e.target.value))}
                      style={{ width: '100%' }}
                    />
                    <div style={{ marginTop: '6px', color: '#f8fafc', fontWeight: 600 }}>
                      {FREQUENCY_SLIDER_STEPS[frequencySliderValue]?.label || 'Weekly'}
                    </div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                      {FREQUENCY_SLIDER_STEPS[frequencySliderValue]?.description}
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '6px' }}>💰 Discount Rate (%)</div>
                    <input
                      type="range"
                      min={0}
                      max={50}
                      step={1}
                      value={customScenario.discountRate}
                      onChange={(e) => setCustomScenario({ ...customScenario, discountRate: Number(e.target.value) })}
                      style={{ width: '100%' }}
                    />
                    <div style={{ marginTop: '6px', color: '#f8fafc', fontWeight: 700, fontSize: '20px' }}>
                      {customScenario.discountRate}%
                    </div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                      割引を高くするとコンバージョン改善とコスト上昇が見込まれます。
                    </div>
                  </div>
                  <div>
                    <div style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '6px' }}>💵 Budget Cap (¥)</div>
                    <input
                      type="range"
                      min={0}
                      max={10000000}
                      step={50000}
                      value={Math.min(customScenario.budgetCap, 10000000)}
                      onChange={(e) => setCustomScenario({ ...customScenario, budgetCap: Number(e.target.value) })}
                      style={{ width: '100%' }}
                    />
                    <div style={{ marginTop: '6px', color: '#f8fafc', fontWeight: 700 }}>
                      {formatYenShort(Math.min(customScenario.budgetCap, 10000000))}
                    </div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                      精密な値は Precise タブで直接入力できます。
                    </div>
                  </div>
                </div>
              )}

              {scenarioEditorTab === 'precise' && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(200px,1fr))', gap: '16px' }}>
                  <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', color: '#e2e8f0', fontSize: '14px' }}>
                    <span>🔄 Contact Frequency</span>
                    <select
                      value={customScenario.frequency}
                      onChange={(e) => setCustomScenario({ ...customScenario, frequency: e.target.value as CustomScenario['frequency'] })}
                      style={{
                        padding: '10px',
                        borderRadius: '10px',
                        border: '1px solid #1e293b',
                        background: '#020617',
                        color: '#f8fafc'
                      }}
                    >
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                      <option value="biweekly">Bi-weekly</option>
                      <option value="monthly">Monthly</option>
                      <option value="one-time">One-time</option>
                    </select>
                  </label>
                  <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', color: '#e2e8f0', fontSize: '14px' }}>
                    <span>⏱ Campaign Duration (days)</span>
                    <input
                      type="number"
                      min={1}
                      max={365}
                      value={customScenario.duration}
                      onChange={(e) => setCustomScenario({ ...customScenario, duration: Number(e.target.value) || 1 })}
                      style={{
                        padding: '10px',
                        borderRadius: '10px',
                        border: '1px solid #1e293b',
                        background: '#020617',
                        color: '#f8fafc'
                      }}
                    />
                  </label>
                  <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', color: '#e2e8f0', fontSize: '14px' }}>
                    <span>💵 Budget Cap (¥)</span>
                    <input
                      type="number"
                      min={0}
                      step={50000}
                      value={customScenario.budgetCap}
                      onChange={(e) => setCustomScenario({ ...customScenario, budgetCap: Number(e.target.value) || 0 })}
                      style={{
                        padding: '10px',
                        borderRadius: '10px',
                        border: '1px solid #1e293b',
                        background: '#020617',
                        color: '#f8fafc'
                      }}
                    />
                  </label>
                  <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', color: '#e2e8f0', fontSize: '14px' }}>
                    <span>💰 Discount Rate (%)</span>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={customScenario.discountRate}
                      onChange={(e) => setCustomScenario({ ...customScenario, discountRate: Number(e.target.value) || 0 })}
                      style={{
                        padding: '10px',
                        borderRadius: '10px',
                        border: '1px solid #1e293b',
                        background: '#020617',
                        color: '#f8fafc'
                      }}
                    />
                  </label>
                  <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', color: '#e2e8f0', fontSize: '14px' }}>
                    <span>📊 Evaluation Metric</span>
                    <select
                      value={customScenario.evaluationMetric}
                      onChange={(e) => setCustomScenario({ ...customScenario, evaluationMetric: e.target.value })}
                      style={{
                        padding: '10px',
                        borderRadius: '10px',
                        border: '1px solid #1e293b',
                        background: '#020617',
                        color: '#f8fafc'
                      }}
                    >
                      <option value="revenue">Incremental Revenue (Δ¥)</option>
                      <option value="profit">Incremental Profit (Δ¥)</option>
                      <option value="roi">ROI</option>
                      <option value="conversion">Conversion Rate</option>
                      <option value="ltv">Customer Lifetime Value</option>
                      <option value="engagement">Engagement Rate</option>
                    </select>
                  </label>
                </div>
              )}

              {scenarioEditorTab === 'advanced' && (
                <div>
                  <textarea
                    value={scenarioSpecDraft}
                    onChange={(e) => handleScenarioSpecDraftChange(e.target.value)}
                    rows={12}
                    style={{
                      width: '100%',
                      padding: '14px',
                      background: '#020617',
                      border: '1px solid #1e293b',
                      borderRadius: '12px',
                      color: '#e2e8f0',
                      fontSize: '13px',
                      fontFamily: 'monospace'
                    }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                    <small style={{ color: '#94a3b8' }}>
                      ScenarioSpec JSON を直接編集できます。YAML を貼り付ける場合は一度 JSON 化してから利用してください。
                    </small>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <span style={{ color: scenarioSpecDirty ? '#fbbf24' : '#22c55e', fontSize: '12px', alignSelf: 'center' }}>
                        {scenarioSpecDirty ? '未適用の変更あり' : 'UIと同期済み'}
                      </span>
                      <button
                        onClick={handleScenarioSpecApply}
                        style={{
                          padding: '8px 14px',
                          borderRadius: '8px',
                          border: 'none',
                          background: 'linear-gradient(135deg,#f97316,#facc15)',
                          color: '#0f172a',
                          fontWeight: 700,
                          cursor: 'pointer'
                        }}
                      >
                        🪄 JSON をフォームに反映
                      </button>
                    </div>
                  </div>
                </div>
              )}

              <div>
                <div style={{ fontWeight: 600, color: '#e2e8f0', marginBottom: '8px' }}>
                  📡 Communication Channels
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(140px,1fr))', gap: '10px' }}>
                  {CHANNEL_OPTIONS.map((channel) => {
                    const active = customScenario.channel.includes(channel)
                    return (
                      <button
                        key={channel}
                        onClick={() => toggleScenarioChannel(channel)}
                        style={{
                          padding: '10px',
                          borderRadius: '10px',
                          border: active ? '1px solid rgba(34,197,94,0.8)' : '1px solid #1e293b',
                          background: active ? 'rgba(34,197,94,0.15)' : 'rgba(15,23,42,0.7)',
                          color: '#e2e8f0',
                          fontWeight: 600,
                          cursor: 'pointer'
                        }}
                      >
                        {channel}
                      </button>
                    )
                  })}
                </div>
                <div style={{ color: '#94a3b8', fontSize: '12px', marginTop: '6px' }}>
                  最低1つは選択してください。複数選択すると ScenarioSpec の channels に反映されます。
                </div>
              </div>
            </section>

            {/* Target segment builder */}
            <section style={{
              borderRadius: '16px',
              border: '1px solid rgba(34,197,94,0.3)',
              background: 'rgba(15,118,110,0.12)',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
                <div>
                  <h3 style={{ color: '#f8fafc', fontSize: '18px', marginBottom: '4px' }}>🎯 Target Segment Builder</h3>
                  <p style={{ color: '#cbd5e1', fontSize: '13px' }}>GUI 条件ビルダーと SQL 直書きを切り替え。許可済みカラムのみ使用できます。</p>
                </div>
                <div style={{ display: 'flex', borderRadius: '10px', border: '1px solid rgba(148,163,184,0.3)' }}>
                  {(['builder', 'sql'] as const).map((mode) => (
                    <button
                      key={mode}
                      onClick={() => {
                        setTargetBuilderMode(mode)
                        if (mode === 'builder') {
                          setBuilderTouched(false)
                        }
                      }}
                      style={{
                        padding: '8px 16px',
                        borderRadius: '10px',
                        border: 'none',
                        background: targetBuilderMode === mode ? 'rgba(34,197,94,0.2)' : 'transparent',
                        color: targetBuilderMode === mode ? '#22c55e' : '#94a3b8',
                        fontWeight: 600,
                        cursor: 'pointer'
                      }}
                    >
                      {mode === 'builder' ? 'GUI Builder' : 'SQL Editor'}
                    </button>
                  ))}
                </div>
              </div>

              {targetBuilderMode === 'builder' ? (
                allowedTargetColumns.length === 0 ? (
                  <div style={{
                    padding: '20px',
                    borderRadius: '12px',
                    border: '1px dashed rgba(148,163,184,0.4)',
                    color: '#94a3b8',
                    background: 'rgba(15,23,42,0.5)'
                  }}>
                    {columnsLoading
                      ? 'データセットのカラム情報を取得中です…'
                      : '対象データセットからカラム情報を取得できません。Policy を選択し直してください。'}
                  </div>
                ) : (
                  <>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {targetConditions.map((condition, index) => {
                        const columnType = inferColumnType(condition.column ? selectedDatasetColumns?.schema?.[condition.column] : undefined)
                        const operators = operatorOptions[columnType]
                        const showSecond = condition.operator === 'between'
                        const isBoolean = columnType === 'boolean'
                        return (
                          <div key={condition.id} style={{ padding: '16px', borderRadius: '14px', border: '1px solid rgba(148,163,184,0.3)', background: '#042f2e' }}>
                            {index > 0 && (
                              <div style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                <span style={{ color: '#94a3b8', fontSize: '12px' }}>Join</span>
                                <select
                                  value={condition.joiner}
                                  onChange={(e) => handleConditionJoinerChange(condition.id, e.target.value as 'AND' | 'OR')}
                                  style={{
                                    padding: '6px 10px',
                                    borderRadius: '8px',
                                    border: '1px solid rgba(148,163,184,0.3)',
                                    background: 'rgba(15,23,42,0.8)',
                                    color: '#f8fafc'
                                  }}
                                >
                                  <option value="AND">AND</option>
                                  <option value="OR">OR</option>
                                </select>
                              </div>
                            )}
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                              <select
                                value={condition.column || ''}
                                onChange={(e) => handleConditionColumnChange(condition.id, e.target.value || null)}
                                style={{
                                  flex: '1 1 160px',
                                  minWidth: '150px',
                                  padding: '10px',
                                  borderRadius: '10px',
                                  border: '1px solid rgba(148,163,184,0.3)',
                                  background: '#020617',
                                  color: '#f8fafc'
                                }}
                              >
                                <option value="">カラム選択</option>
                                {allowedTargetColumns.map((column) => (
                                  <option key={column} value={column}>{column}</option>
                                ))}
                              </select>
                              <select
                                value={condition.operator}
                                onChange={(e) => handleConditionOperatorChange(condition.id, e.target.value as ConditionOperator)}
                                style={{
                                  flex: '1 1 140px',
                                  minWidth: '140px',
                                  padding: '10px',
                                  borderRadius: '10px',
                                  border: '1px solid rgba(148,163,184,0.3)',
                                  background: '#020617',
                                  color: '#f8fafc'
                                }}
                              >
                                {operators.map((operator) => (
                                  <option key={operator.value} value={operator.value}>{operator.label}</option>
                                ))}
                              </select>
                              {!isBoolean && (
                                <input
                                  type={columnType === 'number' ? 'number' : 'text'}
                                  value={condition.value}
                                  onChange={(e) => handleConditionValueChange(condition.id, e.target.value)}
                                  placeholder={columnType === 'number' ? '数値' : '値'}
                                  style={{
                                    flex: '1 1 140px',
                                    minWidth: '140px',
                                    padding: '10px',
                                    borderRadius: '10px',
                                    border: '1px solid rgba(148,163,184,0.3)',
                                    background: '#020617',
                                    color: '#f8fafc'
                                  }}
                                />
                              )}
                              {showSecond && (
                                <input
                                  type="number"
                                  value={condition.secondaryValue}
                                  onChange={(e) => handleConditionValueChange(condition.id, e.target.value, 'secondary')}
                                  placeholder="上限値"
                                  style={{
                                    flex: '1 1 140px',
                                    minWidth: '140px',
                                    padding: '10px',
                                    borderRadius: '10px',
                                    border: '1px solid rgba(148,163,184,0.3)',
                                    background: '#020617',
                                    color: '#f8fafc'
                                  }}
                                />
                              )}
                              <button
                                onClick={() => removeConditionRow(condition.id)}
                                style={{
                                  border: '1px solid rgba(248,113,113,0.4)',
                                  background: 'transparent',
                                  color: '#f87171',
                                  borderRadius: '10px',
                                  padding: '8px 12px',
                                  cursor: 'pointer'
                                }}
                                disabled={targetConditions.length === 1}
                              >
                                ✕ Remove
                              </button>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                    <button
                      onClick={addConditionRow}
                      style={{
                        marginTop: '12px',
                        alignSelf: 'flex-start',
                        padding: '10px 18px',
                        borderRadius: '10px',
                        border: '1px dashed rgba(34,197,94,0.5)',
                        background: 'transparent',
                        color: '#22c55e',
                        cursor: 'pointer'
                      }}
                    >
                      ＋ 条件を追加
                    </button>
                    <div style={{ marginTop: '20px' }}>
                      <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '6px' }}>SQL Preview</div>
                      <textarea
                        value={builderGeneratedSql || ''}
                        readOnly
                        rows={3}
                        style={{
                          width: '100%',
                          padding: '12px',
                          borderRadius: '10px',
                          border: '1px solid rgba(148,163,184,0.3)',
                          background: '#020617',
                          color: '#f8fafc',
                          fontSize: '13px',
                          fontFamily: 'monospace'
                        }}
                      />
                    </div>
                    <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                      使用可能カラム:
                      <span style={{ marginLeft: '4px' }}>
                        {allowedTargetColumns.slice(0, 6).map((column) => (
                          <code key={column} style={{ marginRight: '6px', background: '#022c22', padding: '2px 6px', borderRadius: '6px' }}>{column}</code>
                        ))}
                        {allowedTargetColumns.length > 6 ? `... +${allowedTargetColumns.length - 6}` : ''}
                      </span>
                    </div>
                  </>
                )
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <textarea
                    value={customScenario.targetSegment}
                    onChange={(e) => handleSqlInputChange(e.target.value)}
                    placeholder="customer_value >= 10000 AND churn_risk <= 0.2 AND city IN ('Tokyo','Osaka')"
                    rows={5}
                    style={{
                      width: '100%',
                      padding: '14px',
                      borderRadius: '12px',
                      border: `1px solid ${sqlValidationError ? 'rgba(248,113,113,0.5)' : 'rgba(148,163,184,0.4)'}`,
                      background: '#020617',
                      color: '#f8fafc',
                      fontSize: '13px',
                      fontFamily: 'monospace'
                    }}
                  />
                  {sqlValidationError ? (
                    <div style={{ color: '#f87171', fontSize: '12px' }}>{sqlValidationError}</div>
                  ) : (
                    <div style={{ color: '#22c55e', fontSize: '12px' }}>✅ 許可済みカラム・演算子のみ検出されました。</div>
                  )}
                  <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                    SELECT / INSERT などのキーワードは禁止されています。許可済み演算子: AND, OR, BETWEEN, IN, LIKE, TRUE/FALSE など。
                  </div>
                </div>
              )}
            </section>

            {/* Actions */}
            <section style={{
              borderRadius: '16px',
              border: '1px solid rgba(148,163,184,0.3)',
              background: 'rgba(15,23,42,0.8)',
              padding: '24px',
              display: 'flex',
              flexDirection: 'column',
              gap: '16px'
            }}>
              <div style={{ color: '#cbd5e1', fontSize: '14px' }}>
                ポリシーに適用すると <strong>{selectedPolicy ? selectedPolicy.name : '未選択'}</strong> の target_rule / frequency_cap 等が更新されます。
              </div>
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <button
                  onClick={applyCustomScenarioToPolicy}
                  disabled={!selectedPolicy || isApplyingScenario || !customScenario.targetSegment.trim()}
                  style={{
                    flex: 1,
                    minWidth: '220px',
                    padding: '14px 20px',
                    borderRadius: '12px',
                    border: 'none',
                    background: !selectedPolicy || !customScenario.targetSegment.trim()
                      ? '#1e293b'
                      : 'linear-gradient(135deg,#10b981,#059669)',
                    color: '#fff',
                    fontWeight: 700,
                    cursor: !selectedPolicy || !customScenario.targetSegment.trim() ? 'not-allowed' : 'pointer',
                    opacity: isApplyingScenario ? 0.6 : 1
                  }}
                >
                  {isApplyingScenario ? 'Applying...' : '選択中のポリシーへ適用'}
                </button>
                <button
                  onClick={() => {
                    if (!customScenario.name || !customScenario.targetSegment.trim() || customScenario.channel.length === 0) {
                      alert('Name / Target Segment / Channel を設定してください。')
                      return
                    }
                    const yamlOutput = scenarioSpecToYaml(scenarioSpecObject)
                    const blob = new Blob([yamlOutput], { type: 'text/yaml' })
                    const url = URL.createObjectURL(blob)
                    const a = document.createElement('a')
                    a.href = url
                    a.download = `scenario_${customScenario.name.toLowerCase().replace(/\s+/g, '_')}.yaml`
                    a.click()
                    URL.revokeObjectURL(url)
                    alert('✅ ScenarioSpec を YAML として保存しました。')
                  }}
                  style={{
                    flex: 1,
                    minWidth: '220px',
                    padding: '14px 20px',
                    borderRadius: '12px',
                    border: 'none',
                    background: 'linear-gradient(135deg,#3b82f6,#8b5cf6)',
                    color: '#fff',
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}
                >
                  💾 Save as ScenarioSpec YAML
                </button>
                <button
                  onClick={resetCustomScenarioForm}
                  style={{
                    padding: '14px 20px',
                    borderRadius: '12px',
                    border: '1px solid rgba(148,163,184,0.4)',
                    background: 'transparent',
                    color: '#94a3b8',
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}
                >
                  🔄 Reset Form
                </button>
              </div>
            </section>

            {/* Example scenarios */}
            <section style={{
              borderRadius: '16px',
              border: '1px solid rgba(59,130,246,0.2)',
              background: 'rgba(30,64,175,0.15)',
              padding: '20px'
            }}>
              <div style={{ fontSize: '14px', fontWeight: 700, color: '#60a5fa', marginBottom: '12px' }}>
                💡 Example Target Segments
              </div>
              <ul style={{ margin: 0, paddingLeft: '20px', color: '#e2e8f0', fontSize: '13px', lineHeight: 1.8 }}>
                <li>
                  <strong>High-Value Dormant Users:</strong>{' '}
                  <code style={{ background: '#1e293b', padding: '2px 6px', borderRadius: '4px' }}>customer_value &gt;= 50000 AND last_purchase_days &gt; 90</code>
                </li>
                <li>
                  <strong>Weekend Shoppers in Major Cities:</strong>{' '}
                  <code style={{ background: '#1e293b', padding: '2px 6px', borderRadius: '4px' }}>purchase_dow IN (0, 6) AND city IN ('Tokyo','Osaka','Nagoya')</code>
                </li>
                <li>
                  <strong>Mobile App Power Users:</strong>{' '}
                  <code style={{ background: '#1e293b', padding: '2px 6px', borderRadius: '4px' }}>app_sessions_30d &gt;= 20 AND mobile_order_ratio &gt; 0.8</code>
                </li>
                <li>
                  <strong>Cart Abandoners with High Intent:</strong>{' '}
                  <code style={{ background: '#1e293b', padding: '2px 6px', borderRadius: '4px' }}>cart_value &gt; 10000 AND abandoned_hours &lt; 24 AND view_count &gt;= 3</code>
                </li>
              </ul>
            </section>
          </div>
        </div>
      )}
    </div>
  )
}
