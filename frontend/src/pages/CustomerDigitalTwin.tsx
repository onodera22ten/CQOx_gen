import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  BarChart,
  Bar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts'
import { ContextBar } from '../components/ContextBar'
import { DecisionSummaryCard } from '../components/DecisionSummaryCard'

/**
 * Customer Digital Twin
 * 代表的な顧客タイプのシミュレーションとwhat-if分析
 */

// Types
interface CustomerPersona {
  id: string
  name: string
  description: string
  features: Record<string, number>
  segment: string
  color: string
}

interface InterventionScenario {
  name: string
  interventions: Record<string, number>
  description: string
}

interface SimulationResult {
  persona_id: string
  persona_name: string
  baseline_outcome: number
  intervention_outcome: number
  treatment_effect: number
  confidence_interval: [number, number]
  cost: number
  roi: number
  recommendation: string
}

export default function CustomerDigitalTwin() {
  const queryClient = useQueryClient()
  const [selectedPersonas, setSelectedPersonas] = useState<string[]>([])
  const [selectedScenario, setSelectedScenario] = useState<InterventionScenario | null>(null)
  const [customScenario, setCustomScenario] = useState<Record<string, number>>({})
  const [showCustomEditor, setShowCustomEditor] = useState(false)
  const [simulationResults, setSimulationResults] = useState<SimulationResult[]>([])
  const [showResults, setShowResults] = useState(false)

  // Predefined customer personas
  const personas: CustomerPersona[] = [
    {
      id: 'persona-1',
      name: 'High-Value Urban Professional',
      description: 'Age 30-45, high income, urban area, tech-savvy',
      segment: 'premium',
      color: '#3b82f6',
      features: {
        age: 38,
        income: 120000,
        urban: 1,
        tech_affinity: 0.9,
        purchase_frequency: 8,
        lifetime_value: 50000
      }
    },
    {
      id: 'persona-2',
      name: 'Budget-Conscious Family',
      description: 'Age 35-50, moderate income, suburban, price-sensitive',
      segment: 'standard',
      color: '#10b981',
      features: {
        age: 42,
        income: 65000,
        urban: 0,
        tech_affinity: 0.5,
        purchase_frequency: 4,
        lifetime_value: 15000
      }
    },
    {
      id: 'persona-3',
      name: 'Young Digital Native',
      description: 'Age 22-30, moderate income, highly engaged online',
      segment: 'growth',
      color: '#f59e0b',
      features: {
        age: 26,
        income: 55000,
        urban: 1,
        tech_affinity: 0.95,
        purchase_frequency: 12,
        lifetime_value: 25000
      }
    },
    {
      id: 'persona-4',
      name: 'Senior Traditional Shopper',
      description: 'Age 60+, moderate-high income, prefers offline channels',
      segment: 'traditional',
      color: '#8b5cf6',
      features: {
        age: 65,
        income: 85000,
        urban: 0,
        tech_affinity: 0.3,
        purchase_frequency: 3,
        lifetime_value: 35000
      }
    },
    {
      id: 'persona-5',
      name: 'Emerging Market Enthusiast',
      description: 'Age 25-35, low-moderate income, high growth potential',
      segment: 'emerging',
      color: '#ec4899',
      features: {
        age: 29,
        income: 45000,
        urban: 1,
        tech_affinity: 0.7,
        purchase_frequency: 6,
        lifetime_value: 12000
      }
    }
  ]

  // Predefined intervention scenarios
  const scenarios: InterventionScenario[] = [
    {
      name: 'Premium Email Campaign',
      interventions: { email_frequency: 2, discount_rate: 0, personalization: 0.8 },
      description: 'Personalized premium content, no discount'
    },
    {
      name: 'Aggressive Discount',
      interventions: { email_frequency: 1, discount_rate: 0.2, personalization: 0.3 },
      description: '20% discount with basic targeting'
    },
    {
      name: 'Nurture Campaign',
      interventions: { email_frequency: 4, discount_rate: 0.05, personalization: 0.9 },
      description: 'High frequency with light discount and deep personalization'
    },
    {
      name: 'Retention Offer',
      interventions: { email_frequency: 1, discount_rate: 0.15, personalization: 0.6 },
      description: 'Targeted retention with moderate discount'
    }
  ]

  // Simulate intervention effects
  const simulateMutation = useMutation({
    mutationFn: async (params: { persona_ids: string[], scenario: Record<string, number> }) => {
      // Mock simulation - in production this would call backend API with causal model
      const results: SimulationResult[] = params.persona_ids.map(pid => {
        const persona = personas.find(p => p.id === pid)!

        // Simulate treatment effect based on persona characteristics and interventions
        const baselineOutcome = persona.features.lifetime_value * 0.1
        const emailEffect = (params.scenario.email_frequency || 0) * persona.features.tech_affinity * 50
        const discountEffect = (params.scenario.discount_rate || 0) * 1000
        const personalizationEffect = (params.scenario.personalization || 0) * persona.features.purchase_frequency * 20

        const interventionOutcome = baselineOutcome + emailEffect + discountEffect + personalizationEffect
        const treatmentEffect = interventionOutcome - baselineOutcome

        const cost = (params.scenario.email_frequency || 0) * 10 +
                     (params.scenario.discount_rate || 0) * persona.features.lifetime_value * 0.2 +
                     (params.scenario.personalization || 0) * 30

        const roi = cost > 0 ? treatmentEffect / cost : 0

        return {
          persona_id: pid,
          persona_name: persona.name,
          baseline_outcome: baselineOutcome,
          intervention_outcome: interventionOutcome,
          treatment_effect: treatmentEffect,
          confidence_interval: [treatmentEffect * 0.8, treatmentEffect * 1.2] as [number, number],
          cost,
          roi,
          recommendation: roi > 3 ? 'Highly Recommended' : roi > 1.5 ? 'Recommended' : roi > 1 ? 'Consider' : 'Not Recommended'
        }
      })

      return results
    },
    onSuccess: (results) => {
      setSimulationResults(results)
      setShowResults(true)
      queryClient.invalidateQueries({ queryKey: ['digital-twin-simulation'] })
    }
  })

  // Run simulation
  const handleSimulate = () => {
    if (selectedPersonas.length === 0) {
      alert('Please select at least one customer persona')
      return
    }

    const scenario = showCustomEditor ? customScenario : (selectedScenario?.interventions || {})
    if (Object.keys(scenario).length === 0) {
      alert('Please select or create an intervention scenario')
      return
    }

    simulateMutation.mutate({
      persona_ids: selectedPersonas,
      scenario
    })
  }

  const results = simulateMutation.data || []

  // Prepare chart data
  const treatmentEffectData = results.map(r => ({
    persona: r.persona_name.split(' ').slice(0, 2).join(' '),
    baseline: r.baseline_outcome,
    intervention: r.intervention_outcome,
    lift: r.treatment_effect
  }))

  const roiData = results.map(r => ({
    persona: r.persona_name.split(' ').slice(0, 2).join(' '),
    roi: r.roi,
    cost: r.cost
  }))

  // Persona comparison radar chart data
  const radarData = personas
    .filter(p => selectedPersonas.includes(p.id))
    .map(p => ({
      persona: p.name.split(' ').slice(0, 2).join(' '),
      'Tech Affinity': p.features.tech_affinity * 100,
      'Purchase Freq': (p.features.purchase_frequency / 12) * 100,
      'Income Level': (p.features.income / 150000) * 100,
      'LTV Score': (p.features.lifetime_value / 50000) * 100
    }))

  const handleSaveAsPolicy = () => {
    if (simulationResults.length === 0) {
      alert('Please run a simulation first');
      return;
    }
    alert('Save as Policy feature - Navigate to Policy Lab (to be implemented)');
  };

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '24px' }}>
        Customer Digital Twin
      </h1>

      {/* Context Bar */}
      <ContextBar
        scenario={{
          id: 'digital-twin-sim',
          name: selectedScenario?.name || 'No scenario selected',
          type: 'What-If Simulation',
        }}
        targetMetric={{
          outcome: 'Customer Outcome (LTV / Revenue)',
        }}
      />

      {/* Decision Summary Card - Shown after simulation */}
      {showResults && simulationResults.length > 0 && (
        <DecisionSummaryCard
          title="Digital Twin Simulation Result"
          verdict={simulationResults[0].roi > 2 ? 'Go' : simulationResults[0].roi > 1 ? 'Canary' : 'Hold'}
          deltaYen={simulationResults.reduce((sum, r) => sum + r.treatment_effect, 0)}
          roi={simulationResults[0].roi}
          reason={simulationResults[0].recommendation}
          recommendations={[
            `Average treatment effect: ¥${(simulationResults.reduce((sum, r) => sum + r.treatment_effect, 0) / simulationResults.length).toFixed(0)} per customer`,
            `Tested ${simulationResults.length} persona(s)`,
            `Best performing: ${simulationResults.sort((a, b) => b.treatment_effect - a.treatment_effect)[0].persona_name}`,
            'Consider A/B test before full rollout',
          ]}
          onViewDetails={() => {
            // Scroll to results section
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
          }}
        />
      )}

      {/* Save as Policy Button */}
      {showResults && simulationResults.length > 0 && (
        <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'flex-end' }}>
          <button
            onClick={handleSaveAsPolicy}
            style={{
              padding: '12px 24px',
              background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
              border: 'none',
              borderRadius: '8px',
              color: '#fff',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(16, 185, 129, 0.3)',
            }}
          >
            💾 Save as Policy
          </button>
        </div>
      )}

      <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '24px' }}>
        Simulate interventions on representative customer personas using causal models
      </p>

      {/* Persona Selection */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-title">Select Customer Personas</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '16px' }}>
          {personas.map(persona => (
            <div
              key={persona.id}
              onClick={() => {
                setSelectedPersonas(prev =>
                  prev.includes(persona.id)
                    ? prev.filter(id => id !== persona.id)
                    : [...prev, persona.id]
                )
              }}
              style={{
                padding: '16px',
                background: selectedPersonas.includes(persona.id) ? `${persona.color}20` : '#0f172a',
                border: `2px solid ${selectedPersonas.includes(persona.id) ? persona.color : '#1e293b'}`,
                borderRadius: '12px',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                <div
                  style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '50%',
                    background: persona.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '20px'
                  }}
                >
                  {selectedPersonas.includes(persona.id) ? '✓' : '👤'}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: '600', color: '#f1f5f9', fontSize: '15px' }}>
                    {persona.name}
                  </div>
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '2px' }}>
                    {persona.segment.toUpperCase()}
                  </div>
                </div>
              </div>
              <p style={{ fontSize: '13px', color: '#cbd5e1', margin: 0 }}>
                {persona.description}
              </p>
              <div style={{ marginTop: '12px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '12px' }}>
                <div>
                  <span style={{ color: '#94a3b8' }}>Age:</span>{' '}
                  <span style={{ color: '#f1f5f9', fontWeight: '500' }}>{persona.features.age}</span>
                </div>
                <div>
                  <span style={{ color: '#94a3b8' }}>Income:</span>{' '}
                  <span style={{ color: '#f1f5f9', fontWeight: '500' }}>¥{(persona.features.income / 1000).toFixed(0)}K</span>
                </div>
                <div>
                  <span style={{ color: '#94a3b8' }}>LTV:</span>{' '}
                  <span style={{ color: '#f1f5f9', fontWeight: '500' }}>¥{(persona.features.lifetime_value / 1000).toFixed(0)}K</span>
                </div>
                <div>
                  <span style={{ color: '#94a3b8' }}>Freq:</span>{' '}
                  <span style={{ color: '#f1f5f9', fontWeight: '500' }}>{persona.features.purchase_frequency}/yr</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Persona Characteristics Radar */}
      {selectedPersonas.length > 0 && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="card-title">Persona Characteristics Comparison</div>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={radarData.length > 0 ? radarData[0] ? Object.keys(radarData[0]).filter(k => k !== 'persona').map(key => {
              const dataPoint: any = { characteristic: key }
              radarData.forEach(persona => {
                dataPoint[persona.persona] = persona[key as keyof typeof persona]
              })
              return dataPoint
            }) : [] : []}>
              <PolarGrid stroke="#334155" />
              <PolarAngleAxis dataKey="characteristic" stroke="#94a3b8" tick={{ fill: '#cbd5e1' }} />
              <PolarRadiusAxis stroke="#94a3b8" domain={[0, 100]} />
              <Tooltip
                contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                labelStyle={{ color: '#f1f5f9' }}
              />
              <Legend />
              {radarData.map((persona, idx) => (
                <Radar
                  key={idx}
                  name={persona.persona}
                  dataKey={persona.persona}
                  stroke={personas.find(p => p.name.startsWith(persona.persona))?.color || '#3b82f6'}
                  fill={personas.find(p => p.name.startsWith(persona.persona))?.color || '#3b82f6'}
                  fillOpacity={0.3}
                />
              ))}
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Intervention Scenario Selection */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-title">Select Intervention Scenario</div>
        <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
          <button
            onClick={() => setShowCustomEditor(false)}
            style={{
              padding: '10px 20px',
              background: !showCustomEditor ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'rgba(51, 65, 85, 0.5)',
              border: 'none',
              borderRadius: '8px',
              color: '#fff',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Predefined Scenarios
          </button>
          <button
            onClick={() => setShowCustomEditor(true)}
            style={{
              padding: '10px 20px',
              background: showCustomEditor ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' : 'rgba(51, 65, 85, 0.5)',
              border: 'none',
              borderRadius: '8px',
              color: '#fff',
              fontSize: '14px',
              fontWeight: '600',
              cursor: 'pointer'
            }}
          >
            Custom Scenario
          </button>
        </div>

        {!showCustomEditor ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '12px' }}>
            {scenarios.map(scenario => (
              <div
                key={scenario.name}
                onClick={() => setSelectedScenario(scenario)}
                style={{
                  padding: '16px',
                  background: selectedScenario?.name === scenario.name ? 'rgba(59, 130, 246, 0.2)' : '#0f172a',
                  border: `2px solid ${selectedScenario?.name === scenario.name ? '#3b82f6' : '#1e293b'}`,
                  borderRadius: '8px',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                <div style={{ fontWeight: '600', color: '#f1f5f9', marginBottom: '8px' }}>
                  {scenario.name}
                </div>
                <p style={{ fontSize: '13px', color: '#94a3b8', margin: '0 0 12px 0' }}>
                  {scenario.description}
                </p>
                <div style={{ fontSize: '12px', color: '#cbd5e1' }}>
                  {Object.entries(scenario.interventions).map(([key, value]) => (
                    <div key={key} style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ color: '#94a3b8' }}>{key}:</span>
                      <span style={{ fontWeight: '500' }}>{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '12px' }}>
            <p style={{ color: '#94a3b8', fontSize: '14px', margin: 0 }}>
              Define custom intervention values:
            </p>
            {['email_frequency', 'discount_rate', 'personalization'].map(param => (
              <div key={param} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <label style={{ width: '180px', color: '#cbd5e1', fontSize: '14px' }}>
                  {param.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}:
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={customScenario[param] || 0}
                  onChange={e => setCustomScenario(prev => ({ ...prev, [param]: parseFloat(e.target.value) || 0 }))}
                  style={{
                    flex: 1,
                    padding: '8px 12px',
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '6px',
                    color: '#f1f5f9',
                    fontSize: '14px'
                  }}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Simulate Button */}
      <div style={{ marginBottom: '24px', textAlign: 'center' }}>
        <button
          onClick={handleSimulate}
          disabled={simulateMutation.isPending}
          style={{
            padding: '14px 32px',
            background: simulateMutation.isPending ? '#64748b' : 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
            border: 'none',
            borderRadius: '8px',
            color: '#fff',
            fontSize: '16px',
            fontWeight: '600',
            cursor: simulateMutation.isPending ? 'not-allowed' : 'pointer',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
          }}
        >
          {simulateMutation.isPending ? 'Simulating...' : '🎯 Run Simulation'}
        </button>
      </div>

      {/* Simulation Results */}
      {results.length > 0 && (
        <>
          {/* Summary Cards */}
          <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', marginBottom: '24px' }}>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Avg Treatment Effect</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: '#16a34a' }}>
                ¥{(results.reduce((sum, r) => sum + r.treatment_effect, 0) / results.length).toFixed(0)}
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Avg ROI</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: '#3b82f6' }}>
                {(results.reduce((sum, r) => sum + r.roi, 0) / results.length).toFixed(2)}x
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Total Cost</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: '#f59e0b' }}>
                ¥{results.reduce((sum, r) => sum + r.cost, 0).toFixed(0)}
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: '12px', color: '#94a3b8', marginBottom: '8px' }}>Personas Analyzed</div>
              <div style={{ fontSize: '32px', fontWeight: '700', color: '#8b5cf6' }}>
                {results.length}
              </div>
            </div>
          </div>

          {/* Treatment Effect Chart */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-title">Treatment Effect by Persona</div>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={treatmentEffectData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="persona" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" label={{ value: 'Outcome (¥)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Legend />
                <Bar dataKey="baseline" fill="#64748b" name="Baseline" />
                <Bar dataKey="intervention" fill="#3b82f6" name="With Intervention" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* ROI Chart */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div className="card-title">ROI Analysis by Persona</div>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={roiData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="persona" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" label={{ value: 'ROI', angle: -90, position: 'insideLeft', fill: '#94a3b8' }} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Legend />
                <ReferenceLine y={1} stroke="#fbbf24" strokeDasharray="3 3" label={{ value: 'Break-even', fill: '#fbbf24' }} />
                <Bar dataKey="roi" fill="#10b981" name="ROI" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Detailed Results Table */}
          <div className="card">
            <div className="card-title">Detailed Simulation Results</div>
            <table className="table">
              <thead>
                <tr>
                  <th>Persona</th>
                  <th>Baseline</th>
                  <th>With Intervention</th>
                  <th>Treatment Effect</th>
                  <th>Cost</th>
                  <th>ROI</th>
                  <th>Recommendation</th>
                </tr>
              </thead>
              <tbody>
                {results.map(result => {
                  const persona = personas.find(p => p.id === result.persona_id)!
                  return (
                    <tr key={result.persona_id}>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <div
                            style={{
                              width: '12px',
                              height: '12px',
                              borderRadius: '50%',
                              background: persona.color
                            }}
                          />
                          <span style={{ fontWeight: '500' }}>{result.persona_name}</span>
                        </div>
                      </td>
                      <td>¥{result.baseline_outcome.toFixed(0)}</td>
                      <td>¥{result.intervention_outcome.toFixed(0)}</td>
                      <td style={{ color: result.treatment_effect > 0 ? '#16a34a' : '#dc2626', fontWeight: '600' }}>
                        {result.treatment_effect > 0 ? '+' : ''}¥{result.treatment_effect.toFixed(0)}
                      </td>
                      <td>¥{result.cost.toFixed(0)}</td>
                      <td style={{ color: result.roi > 2 ? '#16a34a' : result.roi > 1 ? '#f59e0b' : '#dc2626', fontWeight: '600' }}>
                        {result.roi.toFixed(2)}x
                      </td>
                      <td>
                        <span
                          style={{
                            padding: '4px 12px',
                            borderRadius: '12px',
                            fontSize: '12px',
                            fontWeight: '600',
                            background:
                              result.recommendation === 'Highly Recommended' ? '#dcfce7' :
                              result.recommendation === 'Recommended' ? '#dbeafe' :
                              result.recommendation === 'Consider' ? '#fef3c7' : '#fee2e2',
                            color:
                              result.recommendation === 'Highly Recommended' ? '#166534' :
                              result.recommendation === 'Recommended' ? '#1e3a8a' :
                              result.recommendation === 'Consider' ? '#92400e' : '#991b1b'
                          }}
                        >
                          {result.recommendation}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Explanation */}
      <div className="card" style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', marginTop: '24px' }}>
        <div className="card-title" style={{ color: '#60a5fa' }}>About Customer Digital Twin</div>
        <p style={{ color: '#cbd5e1', margin: 0, lineHeight: '1.6' }}>
          Customer Digital Twin uses your trained causal models to simulate how different customer personas respond to interventions.
          This enables safe what-if analysis before deploying real campaigns. The simulation incorporates learned treatment heterogeneity,
          allowing you to optimize interventions for each customer segment. Results show predicted outcomes, costs, and ROI to support
          data-driven decision making.
        </p>
      </div>
    </div>
  )
}
