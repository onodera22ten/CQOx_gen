import { useState, useEffect, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { multiArmAPI, TreatmentArmRequest, TreatmentType, MultiArmExperiment } from '../api/v2/multiArm'
import { orchestratorAPI, OrchestratorExperiment, AllocationResponse, OutcomePayload } from '../api/v2/orchestrator'
import { useI18n } from '../contexts/I18nContext'
import { datasetsAPI } from '../api/v1/datasets'
import { columnSuggestionsAPI } from '../api/v2/columnSuggestions'

const DEFAULT_MULTI_ARM_PAYLOAD = JSON.stringify(
  {
    X: [
      [0.2, 1.1],
      [0.5, -0.3],
      [0.8, 0.9]
    ],
    T: [0, 1, 2],
    Y: [0.1, 1.4, 2.0]
  },
  null,
  2
)

const DEFAULT_OUTCOMES = JSON.stringify(
  [
    { arm_id: 'control', reward: 1 },
    { arm_id: 'variant_a', reward: 0 }
  ],
  null,
  2
)

const formatDateTime = (value?: string | null) => {
  if (!value) return ''
  return new Date(value).toLocaleString()
}

export default function ExperimentStudio() {
  const { t } = useI18n()
  const queryClient = useQueryClient()

  // Multi-arm configuration state
  const [experimentName, setExperimentName] = useState('New Multi-Arm Experiment')
  const [treatmentType, setTreatmentType] = useState<TreatmentType>('multi_armed')
  const [treatmentColumn, setTreatmentColumn] = useState('treatment_arm')
  const [outcomeColumn, setOutcomeColumn] = useState('delta_yen')
  const [arms, setArms] = useState<TreatmentArmRequest[]>([
    { arm_id: 0, label: 'Control' },
    { arm_id: 1, label: 'Variant A' }
  ])
  const [analysisPayload, setAnalysisPayload] = useState(DEFAULT_MULTI_ARM_PAYLOAD)
  const [selectedExperiment, setSelectedExperiment] = useState<string | null>(null)

  // Orchestrator configuration
  const [orchestratorName, setOrchestratorName] = useState('Campaign Control Tower')
  const [targetMetric, setTargetMetric] = useState('conversion_rate')
  const [orchestratorArms, setOrchestratorArms] = useState<string[]>(['control', 'variant_a'])
  const [selectedOrchestrator, setSelectedOrchestrator] = useState<string | null>(null)
  const [allocationView, setAllocationView] = useState<AllocationResponse | null>(null)
  const [outcomePayload, setOutcomePayload] = useState(DEFAULT_OUTCOMES)
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null)
  const [detectingColumns, setDetectingColumns] = useState(false)
  const [columnDetectMessage, setColumnDetectMessage] = useState<string | null>(null)
  const [analysisResult, setAnalysisResult] = useState<Record<string, number> | null>(null)
  const [generatingPayload, setGeneratingPayload] = useState(false)

  const { data: multiArmExperiments, isLoading: multiArmLoading } = useQuery({
    queryKey: ['multi-arm-experiments'],
    queryFn: () => multiArmAPI.listExperiments()
  })

  const { data: orchestratorExperiments, isLoading: orchestratorLoading } = useQuery({
    queryKey: ['orchestrator-experiments'],
    queryFn: () => orchestratorAPI.listExperiments()
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

  useEffect(() => {
    if (!selectedDatasetId && datasets && datasets.length > 0) {
      setSelectedDatasetId(datasets[0].id)
    }
  }, [datasets, selectedDatasetId])

  useEffect(() => {
    setColumnDetectMessage(null)
  }, [selectedDatasetId])

  useEffect(() => {
    setAnalysisResult(null)
  }, [selectedExperiment])

  const availableColumns = datasetColumns?.columns ?? []
  const datasetNameMap = useMemo(() => {
    const map: Record<string, string> = {}
    datasets?.forEach((dataset) => {
      map[dataset.id] = dataset.name || dataset.id
    })
    return map
  }, [datasets])
  const selectedExperimentDetails = useMemo(() => {
    return multiArmExperiments?.find((exp) => exp.id === selectedExperiment) ?? null
  }, [multiArmExperiments, selectedExperiment])

  const createMultiArmMutation = useMutation({
    mutationFn: multiArmAPI.createExperiment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['multi-arm-experiments'] })
    }
  })

  const analyzeMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: { X: number[][]; T: number[]; Y: number[] } }) =>
      multiArmAPI.analyzeExperiment(id, payload)
  })

  const createOrchestratorMutation = useMutation({
    mutationFn: orchestratorAPI.createExperiment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orchestrator-experiments'] })
    }
  })

  const updateOrchestratorMutation = useMutation({
    mutationFn: ({ id, outcomes }: { id: string; outcomes: OutcomePayload[] }) =>
      orchestratorAPI.updateExperiment(id, outcomes),
    onSuccess: (data) => setAllocationView(data)
  })

  const handleAutoDetectColumns = async () => {
    if (!selectedDatasetId) return
    setDetectingColumns(true)
    try {
      const response = await columnSuggestionsAPI.fetch(selectedDatasetId)
      const treatmentCandidate = response.suggestions['treatment']?.[0]?.column
      const outcomeCandidate = response.suggestions['outcome']?.[0]?.column
      if (treatmentCandidate) {
        setTreatmentColumn(treatmentCandidate)
      }
      if (outcomeCandidate) {
        setOutcomeColumn(outcomeCandidate)
      }
      if (!treatmentCandidate && !outcomeCandidate) {
        setColumnDetectMessage('No matching columns detected. Please select columns manually.')
      } else {
        setColumnDetectMessage('Suggestions applied. Please review before saving.')
      }
    } catch (err) {
      alert('Failed to detect columns')
      setColumnDetectMessage(null)
    } finally {
      setDetectingColumns(false)
    }
  }

  const handleArmChange = (index: number, field: keyof TreatmentArmRequest, value: string) => {
    setArms((prev) =>
      prev.map((arm, idx) =>
        idx === index
          ? {
              ...arm,
              [field]: field === 'arm_id' ? Number(value) : value
            }
          : arm
      )
    )
  }

  const addArm = () => {
    const nextId = arms.length
    setArms((prev) => [...prev, { arm_id: nextId, label: `Variant ${String.fromCharCode(65 + nextId)}` }])
  }

  const removeArm = (index: number) => {
    setArms((prev) => prev.filter((_, idx) => idx !== index))
  }

  const handleCreateMultiArm = (evt: React.FormEvent) => {
    evt.preventDefault()
    if (!selectedDatasetId) {
      alert('Select a dataset before creating an experiment.')
      return
    }
    createMultiArmMutation.mutate({
      experiment_name: experimentName,
      treatment_type: treatmentType,
      dataset_id: selectedDatasetId,
      treatment_column: treatmentColumn,
      outcome_column: outcomeColumn,
      arms
    })
  }

  const handleAnalyze = () => {
    if (!selectedExperiment) return
    try {
      const parsed = JSON.parse(analysisPayload)
      analyzeMutation.mutate({
        id: selectedExperiment,
        payload: parsed
      }, {
        onSuccess: (data) => {
          setAnalysisResult(data.ate_by_arm)
        }
      })
    } catch {
      alert('Invalid JSON payload')
    }
  }

  const handleGeneratePayload = async () => {
    if (!selectedExperiment) {
      alert('Select an experiment from the list to generate payload.')
      return
    }
    if (!selectedExperimentDetails?.dataset_id) {
      alert('Selected experiment is not linked to a dataset.')
      return
    }
    setGeneratingPayload(true)
    try {
      const payload = await multiArmAPI.generatePayload(selectedExperiment)
      const structured = { X: payload.X, T: payload.T, Y: payload.Y }
      setAnalysisPayload(JSON.stringify(structured, null, 2))
      setAnalysisResult(null)
    } catch {
      alert('Failed to generate payload from dataset')
    } finally {
      setGeneratingPayload(false)
    }
  }

  const handleCreateOrchestrator = (evt: React.FormEvent) => {
    evt.preventDefault()
    createOrchestratorMutation.mutate({
      experiment_name: orchestratorName,
      target_metric: targetMetric,
      arms: orchestratorArms
    })
  }

  const fetchAllocation = async (experimentId: string) => {
    const response = await orchestratorAPI.getAllocation(experimentId)
    setAllocationView(response)
    setSelectedOrchestrator(experimentId)
  }

  const handleAllocationUpdate = () => {
    if (!selectedOrchestrator) return
    try {
      const parsed = JSON.parse(outcomePayload)
      updateOrchestratorMutation.mutate({
        id: selectedOrchestrator,
        outcomes: parsed
      })
    } catch {
      alert('Invalid JSON payload')
    }
  }

  const addOrchestratorArm = () => {
    setOrchestratorArms((prev) => [...prev, `variant_${prev.length}`])
  }

  const updateOrchestratorArm = (index: number, value: string) => {
    setOrchestratorArms((prev) => prev.map((arm, idx) => (idx === index ? value : arm)))
  }

  const removeOrchestratorArm = (index: number) => {
    setOrchestratorArms((prev) => prev.filter((_, idx) => idx !== index))
  }

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <header>
        <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '12px' }}>Experiment Studio</h1>
        <p style={{ color: '#94a3b8' }}>
          Multi-Arm Causal Design + Experiment Orchestrator. Configure treatment arms, run offline DR analysis, and manage online allocation updates.
        </p>
      </header>

      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Multi-Arm Experiment Setup</h2>
        <form onSubmit={handleCreateMultiArm} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <label style={labelStyle}>
            Experiment Name
            <input value={experimentName} onChange={(e) => setExperimentName(e.target.value)} style={inputStyle} required />
          </label>

          <label style={labelStyle}>
            Treatment Type
            <select value={treatmentType} onChange={(e) => setTreatmentType(e.target.value as TreatmentType)} style={inputStyle}>
              <option value="binary">Binary</option>
              <option value="multi_armed">Multi-Armed</option>
              <option value="dose_response">Dose-Response</option>
            </select>
          </label>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: '12px' }}>
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
              <button type="button" onClick={handleAutoDetectColumns} disabled={!selectedDatasetId || detectingColumns} style={secondaryButtonStyle}>
                {detectingColumns ? 'Detecting…' : 'Auto Detect'}
              </button>
              <p style={{ fontSize: '12px', color: '#94a3b8', margin: 0 }}>
                Auto Detect scans the selected dataset and fills treatment/outcome fields with the best guess. Please review before saving.
              </p>
              {columnDetectMessage && <p style={{ fontSize: '12px', color: '#bfdbfe', margin: 0 }}>{columnDetectMessage}</p>}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))', gap: '12px' }}>
            <label style={labelStyle}>
              Treatment Column
              {availableColumns.length > 0 ? (
                <select value={treatmentColumn} onChange={(e) => setTreatmentColumn(e.target.value)} style={inputStyle}>
                  {!availableColumns.includes(treatmentColumn) && treatmentColumn && (
                    <option value={treatmentColumn}>{treatmentColumn}</option>
                  )}
                  {availableColumns.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              ) : (
                <input value={treatmentColumn} onChange={(e) => setTreatmentColumn(e.target.value)} style={inputStyle} />
              )}
            </label>
            <label style={labelStyle}>
              Outcome Column
              {availableColumns.length > 0 ? (
                <select value={outcomeColumn} onChange={(e) => setOutcomeColumn(e.target.value)} style={inputStyle}>
                  {!availableColumns.includes(outcomeColumn) && outcomeColumn && (
                    <option value={outcomeColumn}>{outcomeColumn}</option>
                  )}
                  {availableColumns.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              ) : (
                <input value={outcomeColumn} onChange={(e) => setOutcomeColumn(e.target.value)} style={inputStyle} />
              )}
            </label>
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ color: '#cbd5e1', fontWeight: 600 }}>Treatment Arms</span>
              <button type="button" onClick={addArm} style={secondaryButtonStyle}>
                Add Arm
              </button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {arms.map((arm, index) => (
                <div key={index} style={{ display: 'grid', gridTemplateColumns: '80px 1fr auto', gap: '8px', alignItems: 'center' }}>
                  <input type="number" value={arm.arm_id} onChange={(e) => handleArmChange(index, 'arm_id', e.target.value)} style={inputStyle} />
                  <input type="text" value={arm.label} onChange={(e) => handleArmChange(index, 'label', e.target.value)} style={inputStyle} />
                  {index > 0 && (
                    <button type="button" onClick={() => removeArm(index)} style={secondaryButtonStyle}>
                      Remove
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          <button type="submit" style={primaryButtonStyle} disabled={createMultiArmMutation.isLoading}>
            {createMultiArmMutation.isLoading ? 'Creating…' : 'Create Multi-Arm Experiment'}
          </button>
        </form>
      </section>

      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Multi-Arm Experiments</h2>
        <p style={{ color: '#94a3b8', marginBottom: '12px', fontSize: '13px' }}>
          Select an experiment below to run DR analysis or generate payloads from the linked dataset. Δ¥ values appear after an analysis is completed.
        </p>
        {multiArmLoading ? (
          <div style={{ color: '#94a3b8' }}>Loading…</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {(multiArmExperiments ?? []).map((exp) => (
              <ExperimentCard
                key={exp.id}
                experiment={exp}
                onSelect={setSelectedExperiment}
                selectedId={selectedExperiment}
                datasetName={exp.dataset_id ? datasetNameMap[exp.dataset_id] : undefined}
              />
            ))}
            {(!multiArmExperiments || multiArmExperiments.length === 0) && <div style={{ color: '#94a3b8' }}>No experiments yet.</div>}
          </div>
        )}
      </section>

      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Offline Analysis (Multi-Arm)</h2>
        <p style={{ color: '#94a3b8', marginBottom: '12px' }}>
          Paste a JSON payload containing feature matrix `X`, treatment vector `T`, and outcome `Y`. You can generate this payload from the selected experiment’s dataset and then run DR analysis to estimate Δ¥ per arm.
        </p>
        {selectedExperimentDetails && (
          <div style={{ color: '#94a3b8', marginBottom: '12px', fontSize: '13px' }}>
            <div>Dataset: {selectedExperimentDetails.dataset_id ? datasetNameMap[selectedExperimentDetails.dataset_id] : '—'}</div>
            <div>Treatment column: {selectedExperimentDetails.treatment_column ?? '—'}</div>
            <div>Outcome column: {selectedExperimentDetails.outcome_column ?? '—'}</div>
          </div>
        )}
        <textarea
          value={analysisPayload}
          onChange={(e) => setAnalysisPayload(e.target.value)}
          rows={10}
          style={textareaStyle}
        />
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
          <button type="button" onClick={handleGeneratePayload} style={secondaryButtonStyle} disabled={!selectedExperiment || generatingPayload}>
            {generatingPayload ? 'Generating…' : 'Generate From Dataset'}
          </button>
          <button onClick={handleAnalyze} style={primaryButtonStyle} disabled={!selectedExperiment || analyzeMutation.isLoading}>
            {analyzeMutation.isLoading ? 'Analyzing…' : 'Run DR Analysis'}
          </button>
        </div>
        {analysisResult && (
          <div style={{ marginTop: '16px' }}>
            <h3 style={{ color: '#e2e8f0', marginBottom: '8px' }}>Analysis Result</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ color: '#94a3b8', borderBottom: '1px solid rgba(148,163,184,0.2)' }}>
                  <th style={{ textAlign: 'left', padding: '8px' }}>Arm</th>
                  <th style={{ textAlign: 'left', padding: '8px' }}>Δ¥ Estimate</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(analysisResult).map(([armId, value]) => {
                  const matchingArm = selectedExperimentDetails?.arms?.find((arm) => String(arm.arm_id) === armId || arm.label === armId)
                  const label = matchingArm ? `${matchingArm.label} (#${matchingArm.arm_id})` : armId
                  return (
                    <tr key={armId}>
                      <td style={{ padding: '8px', color: '#e2e8f0' }}>{label}</td>
                      <td style={{ padding: '8px', color: '#e2e8f0' }}>{Number(value).toFixed(2)}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section style={sectionStyle}>
        <h2 style={sectionTitleStyle}>Experiment Orchestrator</h2>
        <p style={{ color: '#94a3b8', marginBottom: '12px' }}>
          Define online bandit experiments by naming the campaign, selecting a target metric, and listing arm labels. This orchestrator updates allocation ratios based on outcomes—no dataset columns are required here.
        </p>
        <form onSubmit={handleCreateOrchestrator} style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px' }}>
          <label style={labelStyle}>
            Experiment Name
            <input value={orchestratorName} onChange={(e) => setOrchestratorName(e.target.value)} style={inputStyle} required />
          </label>
          <label style={labelStyle}>
            Target Metric
            <input value={targetMetric} onChange={(e) => setTargetMetric(e.target.value)} style={inputStyle} required />
          </label>
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ color: '#cbd5e1', fontWeight: 600 }}>Arms</span>
              <button type="button" onClick={addOrchestratorArm} style={secondaryButtonStyle}>
                Add Arm
              </button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {orchestratorArms.map((arm, index) => (
                <div key={index} style={{ display: 'flex', gap: '8px' }}>
                  <input value={arm} onChange={(e) => updateOrchestratorArm(index, e.target.value)} style={{ ...inputStyle, flex: 1 }} />
                  {orchestratorArms.length > 1 && (
                    <button type="button" onClick={() => removeOrchestratorArm(index)} style={secondaryButtonStyle}>
                      Remove
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
          <button type="submit" style={primaryButtonStyle} disabled={createOrchestratorMutation.isLoading}>
            {createOrchestratorMutation.isLoading ? 'Creating…' : 'Create Orchestrator Experiment'}
          </button>
        </form>

        <div>
          <h3 style={{ color: '#e2e8f0', marginBottom: '8px' }}>Online Experiments</h3>
          {orchestratorLoading ? (
            <div style={{ color: '#94a3b8' }}>Loading…</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {(orchestratorExperiments ?? []).map((exp) => (
                <OrchestratorCard key={exp.id} experiment={exp} onFetch={fetchAllocation} selectedId={selectedOrchestrator} />
              ))}
              {(!orchestratorExperiments || orchestratorExperiments.length === 0) && <div style={{ color: '#94a3b8' }}>No orchestrator experiments yet.</div>}
            </div>
          )}
        </div>

        {allocationView && (
          <div style={{ marginTop: '16px', padding: '12px', borderRadius: '12px', background: '#0f172a', border: '1px solid rgba(148,163,184,0.2)' }}>
            <div style={{ color: '#e2e8f0', fontWeight: 600, marginBottom: '8px' }}>Latest Allocation</div>
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              {Object.entries(allocationView.allocations).map(([arm, value]) => (
                <div key={arm} style={{ padding: '6px 12px', background: 'rgba(59,130,246,0.15)', borderRadius: '999px', color: '#bfdbfe' }}>
                  {arm}: {(value * 100).toFixed(2)}%
                </div>
              ))}
            </div>
          </div>
        )}

        <div style={{ marginTop: '16px' }}>
          <h3 style={{ color: '#e2e8f0', marginBottom: '8px' }}>Update Outcomes</h3>
          <textarea
            value={outcomePayload}
            onChange={(e) => setOutcomePayload(e.target.value)}
            rows={8}
            style={textareaStyle}
          />
          <button
            onClick={handleAllocationUpdate}
            style={primaryButtonStyle}
            disabled={!selectedOrchestrator || updateOrchestratorMutation.isLoading}
          >
            {updateOrchestratorMutation.isLoading ? 'Updating…' : 'Apply Outcomes'}
          </button>
        </div>
      </section>
    </div>
  )
}

const ExperimentCard = ({
  experiment,
  onSelect,
  selectedId,
  datasetName
}: {
  experiment: MultiArmExperiment
  onSelect: (id: string) => void
  selectedId: string | null
  datasetName?: string
}) => (
  <div
    style={{
      padding: '16px',
      borderRadius: '12px',
      border: selectedId === experiment.id ? '1px solid rgba(59,130,246,0.8)' : '1px solid rgba(148,163,184,0.2)',
      background: '#0f172a',
      cursor: 'pointer'
    }}
    onClick={() => onSelect(experiment.id)}
  >
    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: '#e2e8f0' }}>
      <div>
        <div style={{ fontWeight: 600 }}>{experiment.experiment_name}</div>
        <div style={{ fontSize: '12px', color: '#94a3b8' }}>{experiment.treatment_type}</div>
        {datasetName && <div style={{ fontSize: '12px', color: '#94a3b8' }}>Dataset: {datasetName}</div>}
        {experiment.created_at && <div style={{ fontSize: '12px', color: '#94a3b8' }}>Created: {formatDateTime(experiment.created_at)}</div>}
      </div>
      <div style={{ fontSize: '12px', color: '#94a3b8' }}>{experiment.status}</div>
    </div>
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
      {(experiment.arms || []).map((arm) => (
        <span key={arm.arm_id} style={{ padding: '4px 10px', borderRadius: '999px', background: 'rgba(59,130,246,0.15)', color: '#bfdbfe', fontSize: '12px' }}>
          {arm.label} (#{arm.arm_id}) {typeof arm.delta_yen === 'number' ? `· Δ¥ ${arm.delta_yen.toFixed(2)}` : '· pending'}
        </span>
      ))}
      {(!experiment.arms || experiment.arms.length === 0) && <span style={{ color: '#94a3b8', fontSize: '12px' }}>No arms recorded</span>}
    </div>
  </div>
)

const OrchestratorCard = ({
  experiment,
  onFetch,
  selectedId
}: {
  experiment: OrchestratorExperiment
  onFetch: (id: string) => void
  selectedId: string | null
}) => (
  <div
    style={{
      padding: '16px',
      borderRadius: '12px',
      border: selectedId === experiment.id ? '1px solid rgba(16,185,129,0.7)' : '1px solid rgba(148,163,184,0.2)',
      background: '#0f172a'
    }}
  >
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
      <div style={{ color: '#e2e8f0' }}>
        <div style={{ fontWeight: 600 }}>{experiment.experiment_name}</div>
        <div style={{ fontSize: '12px', color: '#94a3b8' }}>{experiment.target_metric}</div>
        {experiment.created_at && <div style={{ fontSize: '12px', color: '#94a3b8' }}>Created: {formatDateTime(experiment.created_at)}</div>}
      </div>
      <button onClick={() => onFetch(experiment.id)} style={secondaryButtonStyle}>
        View Allocation
      </button>
    </div>
    <div style={{ fontSize: '12px', color: '#94a3b8' }}>Status: {experiment.status}</div>
  </div>
)

const sectionStyle: React.CSSProperties = {
  background: '#101629',
  padding: '20px',
  borderRadius: '16px',
  border: '1px solid rgba(148,163,184,0.2)'
}

const sectionTitleStyle: React.CSSProperties = { fontSize: '18px', fontWeight: 600, marginBottom: '12px', color: '#e2e8f0' }

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

const labelStyle: React.CSSProperties = { display: 'flex', flexDirection: 'column', gap: '4px', color: '#cbd5e1' }

const primaryButtonStyle: React.CSSProperties = {
  background: 'linear-gradient(135deg,#3b82f6,#8b5cf6)',
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
  padding: '6px 10px',
  cursor: 'pointer'
}
