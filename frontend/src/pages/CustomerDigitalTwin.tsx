import { useMemo, useState } from 'react'
import { getApiUrl } from '../utils/env'
import { useI18n } from '../contexts/I18nContext'

type Localized = { en: string; ja: string }

type Persona = {
  id: string
  accent: string
  name: Localized
  description: Localized
  snapshot: { label: Localized; value: string }[]
  tags: string[]
  headline: Localized
}

type Scenario = {
  id: string
  accent: string
  title: Localized
  summary: Localized
  parameters: { label: Localized; value: string }[]
  impact: { label: Localized; value: string }[]
}

const PERSONAS: Persona[] = [
  {
    id: 'urban_pro',
    accent: '#38bdf8',
    name: {
      en: 'High-Value Urban Professional',
      ja: 'ハイバリュー都市型プロフェッショナル'
    },
    description: {
      en: 'Represents metro-area top tier members with high omni-channel engagement and low churn risk.',
      ja: '都市部の上位顧客層。オムニチャネル利用が高く、解約リスクが低い優良会員を表します。'
    },
    snapshot: [
      { label: { en: 'Avg. LTV', ja: '平均LTV' }, value: '¥128,000' },
      { label: { en: 'Churn risk', ja: '離反リスク' }, value: '6% (Low)' },
      { label: { en: 'Pref. channels', ja: '好みのチャネル' }, value: 'App / Email' }
    ],
    tags: ['High LTV', 'Personalized offers', 'Urban'],
    headline: {
      en: 'Values premium content & concierge-like care.',
      ja: 'プレミアムな情報提供と丁寧なコンシェルジュ対応を好みます。'
    }
  },
  {
    id: 'budget_family',
    accent: '#facc15',
    name: {
      en: 'Budget-Conscious Family',
      ja: 'コスパ重視ファミリー層'
    },
    description: {
      en: 'Price-sensitive households who react strongly to coupons and seasonal bundles.',
      ja: '価格感度が高く、クーポンや季節パッケージの反応が高いファミリー層です。'
    },
    snapshot: [
      { label: { en: 'Avg. LTV', ja: '平均LTV' }, value: '¥58,000' },
      { label: { en: 'Churn risk', ja: '離反リスク' }, value: '18% (Medium)' },
      { label: { en: 'Pref. channels', ja: '好みのチャネル' }, value: 'LINE / SMS' }
    ],
    tags: ['Discount seeker', 'Bundle friendly', 'Family'],
    headline: {
      en: 'Responds to value messaging and visible savings.',
      ja: 'お得感や家族向けバンドルの訴求が響きます。'
    }
  },
  {
    id: 'dormant_high_value',
    accent: '#c084fc',
    name: {
      en: 'Dormant High-Value Members',
      ja: '休眠ハイバリュー会員'
    },
    description: {
      en: 'Previously top spenders with declining frequency and high upside for targeted retention offers.',
      ja: 'かつて優良顧客だったが購入頻度が落ちた層。解約防止向け施策の効果が高い。'
    },
    snapshot: [
      { label: { en: 'Avg. LTV', ja: '平均LTV' }, value: '¥96,000' },
      { label: { en: 'Churn risk', ja: '離反リスク' }, value: '27% (High)' },
      { label: { en: 'Pref. channels', ja: '好みのチャネル' }, value: 'Email / Direct Mail' }
    ],
    tags: ['Retention focus', 'Win-back', 'High upside'],
    headline: {
      en: 'Needs tailored win-back flows before lapse.',
      ja: '離脱前に個別の再活性化フローが必要です。'
    }
  },
  {
    id: 'digital_native',
    accent: '#34d399',
    name: {
      en: 'Mobile Digital Native',
      ja: 'モバイルデジタルネイティブ'
    },
    description: {
      en: 'Heavy in-app users with high engagement but low ticket size; prefer product updates over discounts.',
      ja: 'アプリ利用が多くエンゲージメントは高いが客単価は低め。割引より新サービス告知を好む層です。'
    },
    snapshot: [
      { label: { en: 'Avg. LTV', ja: '平均LTV' }, value: '¥42,000' },
      { label: { en: 'Churn risk', ja: '離反リスク' }, value: '12% (Low)' },
      { label: { en: 'Pref. channels', ja: '好みのチャネル' }, value: 'Push / In-App' }
    ],
    tags: ['Engagement', 'App-first', 'Low ticket'],
    headline: {
      en: 'Best served through feature drops and gamified nudges.',
      ja: '新機能の告知やゲーミフィケーション施策が効果的です。'
    }
  }
]

const SCENARIOS: Scenario[] = [
  {
    id: 'premium_email',
    accent: '#38bdf8',
    title: {
      en: 'Premium Email Campaign',
      ja: 'プレミアムメールキャンペーン'
    },
    summary: {
      en: 'Send two high-touch newsletters per month with heavy personalization and no discounts.',
      ja: '月2回、高パーソナライズのプレミアムメールを配信（割引なし）。'
    },
    parameters: [
      { label: { en: 'Email frequency', ja: 'メール頻度' }, value: '2 / month (+1)' },
      { label: { en: 'Discount rate', ja: '割引率' }, value: '0%' },
      { label: { en: 'Personalization', ja: 'パーソナライズ度' }, value: '0.8 (High)' }
    ],
    impact: [
      { label: { en: 'Projected Δ¥', ja: '予測Δ¥' }, value: '¥18.3M' },
      { label: { en: 'Estimated ROI', ja: '推定ROI' }, value: '5.1x' },
      { label: { en: 'Risk level', ja: 'リスクレベル' }, value: 'Low' }
    ]
  },
  {
    id: 'aggressive_discount',
    accent: '#f87171',
    title: {
      en: 'Aggressive Discount Burst',
      ja: 'アグレッシブディスカウント'
    },
    summary: {
      en: 'Short window 20% discount with suppressed frequency to avoid fatigue.',
      ja: '頻度を抑えつつ20%割引を短期集中で実施。'
    },
    parameters: [
      { label: { en: 'Email frequency', ja: 'メール頻度' }, value: '1 / month (-1)' },
      { label: { en: 'Discount rate', ja: '割引率' }, value: '20%' },
      { label: { en: 'Personalization', ja: 'パーソナライズ度' }, value: '0.4 (Std)' }
    ],
    impact: [
      { label: { en: 'Projected Δ¥', ja: '予測Δ¥' }, value: '¥12.6M' },
      { label: { en: 'Estimated ROI', ja: '推定ROI' }, value: '2.4x' },
      { label: { en: 'Risk level', ja: 'リスクレベル' }, value: 'Medium' }
    ]
  },
  {
    id: 'nurture_campaign',
    accent: '#c084fc',
    title: {
      en: 'Always-on Nurture',
      ja: 'ナーチャー強化'
    },
    summary: {
      en: 'Increase touchpoints with lite discounts and strong personalization messages.',
      ja: 'タッチポイントを増やし、軽い割引と高いパーソナライズ訴求を併用。'
    },
    parameters: [
      { label: { en: 'Email frequency', ja: 'メール頻度' }, value: '3 / month (+2)' },
      { label: { en: 'Discount rate', ja: '割引率' }, value: '5%' },
      { label: { en: 'Personalization', ja: 'パーソナライズ度' }, value: '0.9 (Very High)' }
    ],
    impact: [
      { label: { en: 'Projected Δ¥', ja: '予測Δ¥' }, value: '¥9.4M' },
      { label: { en: 'Estimated ROI', ja: '推定ROI' }, value: '3.3x' },
      { label: { en: 'Risk level', ja: 'リスクレベル' }, value: 'Low' }
    ]
  },
  {
    id: 'retention_offer',
    accent: '#34d399',
    title: {
      en: 'Retention Rescue Offer',
      ja: 'リテンション強化オファー'
    },
    summary: {
      en: 'Target high churn personas with monthly moderate discounts and 1:1 concierge.',
      ja: '離反リスクが高い層へ月1回の中程度割引＋1:1ケアを実施。'
    },
    parameters: [
      { label: { en: 'Email frequency', ja: 'メール頻度' }, value: '1 / month' },
      { label: { en: 'Discount rate', ja: '割引率' }, value: '12%' },
      { label: { en: 'Personalization', ja: 'パーソナライズ度' }, value: '0.7 (High)' }
    ],
    impact: [
      { label: { en: 'Projected Δ¥', ja: '予測Δ¥' }, value: '¥15.8M' },
      { label: { en: 'Estimated ROI', ja: '推定ROI' }, value: '4.0x' },
      { label: { en: 'Risk level', ja: 'リスクレベル' }, value: 'Low-Med' }
    ]
  }
]

const CHANNEL_CHOICES = ['Email', 'SMS', 'Push', 'LINE']

const runButtonCopy: Localized = {
  en: 'Run simulation for the selected persona × scenario',
  ja: '③ このペルソナ × シナリオでシミュレーションを実行'
}

const aboutText: Localized = {
  en: 'Customer Digital Twin lets you safely test "What if we deploy this intervention?" on representative personas before rolling out. It combines actual customer data with a trained causal model to estimate the impact on LTV, sales, and retention for each persona × scenario.',
  ja: 'Customer Digital Twin は、実データと学習済み因果モデルを組み合わせて「もしこの施策を実施したら、お客様のLTVや売上、離反がどう変わるか」を事前に試せるシミュレーション環境です。代表的な顧客タイプ（ペルソナ）ごとに施策効果を推定し、リスクを最小化しながら最適な意思決定をサポートします。'
}

const stepGuide: Localized[] = [
  {
    en: '① Choose customer persona',
    ja: '① お客様タイプ（ペルソナ）を選ぶ'
  },
  {
    en: '② Choose intervention scenario',
    ja: '② 施策シナリオを選ぶ'
  },
  {
    en: '③ Run simulation',
    ja: '③ シミュレーションを実行'
  }
]

export default function CustomerDigitalTwin() {
  const { language } = useI18n()
  const pdfUrl = `${getApiUrl()}/docs/twin`
  const [selectedPersonaId, setSelectedPersonaId] = useState<string | null>(null)
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null)
  const [scenarioTab, setScenarioTab] = useState<'predefined' | 'custom'>('predefined')
  const [customScenario, setCustomScenario] = useState({
    name: '',
    emailFrequency: 2,
    discountRate: 10,
    personalization: 0.6,
    channels: ['Email']
  })

  const text = (value: Localized) => value[language]

  const selectedPersona = PERSONAS.find((p) => p.id === selectedPersonaId) || null

  const predefinedScenario = SCENARIOS.find((s) => s.id === selectedScenarioId) || null

  const customScenarioSnapshot: Scenario = useMemo(() => ({
    id: 'custom',
    accent: '#818cf8',
    title: {
      en: customScenario.name || 'Custom Scenario',
      ja: customScenario.name || 'カスタムシナリオ'
    },
    summary: {
      en: `Use ${customScenario.channels.join(', ')} channels with ${customScenario.discountRate}% discount and personalization ${Math.round(customScenario.personalization * 100)}%.`,
      ja: `${customScenario.channels.join(', ')} チャネルで割引率 ${customScenario.discountRate}%・パーソナライズ ${Math.round(customScenario.personalization * 100)}% を設定。`
    },
    parameters: [
      { label: { en: 'Email frequency', ja: 'メール頻度' }, value: `${customScenario.emailFrequency} / month` },
      { label: { en: 'Discount rate', ja: '割引率' }, value: `${customScenario.discountRate}%` },
      { label: { en: 'Personalization', ja: 'パーソナライズ度' }, value: `${Math.round(customScenario.personalization * 100)}%` }
    ],
    impact: [
      { label: { en: 'Projected Δ¥', ja: '予測Δ¥' }, value: 'TBD (requires run)' },
      { label: { en: 'Estimated ROI', ja: '推定ROI' }, value: '—' },
      { label: { en: 'Risk level', ja: 'リスクレベル' }, value: 'Validated after run' }
    ]
  }), [customScenario])

  const selectedScenario = selectedScenarioId === 'custom' ? customScenarioSnapshot : predefinedScenario

  const handleRunSimulation = () => {
    if (!selectedPersona || !selectedScenario) return
    const personaName = text(selectedPersona.name)
    const scenarioName = text(selectedScenario.title)
    alert(`Simulating: ${personaName} × ${scenarioName}`)
  }

  const handleChannelToggle = (channel: string) => {
    setCustomScenario((prev) => {
      const exists = prev.channels.includes(channel)
      return {
        ...prev,
        channels: exists ? prev.channels.filter((c) => c !== channel) : [...prev.channels, channel]
      }
    })
  }

  const isReadyToRun = Boolean(selectedPersona && selectedScenario)

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 700, marginBottom: '8px', color: '#f8fafc' }}>
          Customer Digital Twin
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '15px' }}>
          {text({
            en: 'Simulate persona-level interventions before launching them in production.',
            ja: '代表的なお客様の「仮想コピー」で施策の効果を試す画面です。'
          })}
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '12px',
        padding: '16px',
        borderRadius: '16px',
        border: '1px solid rgba(148,163,184,0.2)',
        marginBottom: '24px',
        background: 'rgba(15,23,42,0.7)'
      }}>
        {stepGuide.map((guide) => (
          <div key={guide.en} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
            <div style={{
              width: '32px',
              height: '32px',
              borderRadius: '999px',
              background: 'rgba(59,130,246,0.15)',
              color: '#3b82f6',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700
            }}>
              {guide.en.slice(0, 1)}
            </div>
            <div>
              <div style={{ color: '#f1f5f9', fontWeight: 600, fontSize: '14px' }}>{text(guide)}</div>
              <div style={{ color: '#94a3b8', fontSize: '12px' }}>
                {guide.en.includes('Persona')
                  ? text({ en: 'Pick which customer type to test.', ja: '試したい顧客タイプを選択。' })
                  : guide.en.includes('Run')
                    ? text({ en: 'Execute the simulation for the selected combo.', ja: '選択中の組み合わせでシミュレーション。' })
                    : text({ en: 'Choose a predefined or custom intervention scenario.', ja: '施策シナリオ（プリセット or カスタム）を選択。' })}
              </div>
            </div>
          </div>
        ))}
      </div>

      <section style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '12px', letterSpacing: '1px' }}>
              Step 1
            </div>
            <h2 style={{ color: '#f8fafc', fontSize: '22px', marginBottom: '4px' }}>
              {text({ en: 'Choose customer persona', ja: '① どのお客様タイプで試しますか？（ペルソナ選択）' })}
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', maxWidth: '640px' }}>
              {text({
                en: 'Each persona bundles real customer cohorts. Select one to inspect baseline KPIs before testing a scenario.',
                ja: '実データから抽出した顧客群をペルソナ化しています。ベースライン指標を確認しながら試したいペルソナを選択してください。'
              })}
            </p>
          </div>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))',
          gap: '16px'
        }}>
          {PERSONAS.map((persona) => {
            const selected = persona.id === selectedPersonaId
            return (
              <button
                key={persona.id}
                onClick={() => setSelectedPersonaId(selected ? null : persona.id)}
                style={{
                  textAlign: 'left',
                  borderRadius: '18px',
                  padding: '20px',
                  border: selected ? `2px solid ${persona.accent}` : '1px solid rgba(148,163,184,0.2)',
                  background: selected ? 'rgba(15,118,110,0.2)' : 'rgba(15,23,42,0.6)',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  boxShadow: selected ? '0 0 30px rgba(15,118,110,0.3)' : 'none'
                }}
              >
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc', marginBottom: '4px' }}>
                  {text(persona.name)}
                </div>
                <div style={{ color: persona.accent, fontSize: '13px', marginBottom: '12px' }}>
                  {text(persona.headline)}
                </div>
                <p style={{ color: '#cbd5e1', fontSize: '13px', minHeight: '48px' }}>
                  {text(persona.description)}
                </p>
                <div style={{ margin: '12px 0', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {persona.snapshot.map((item) => (
                    <div key={item.label.en} style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '13px' }}>
                      <span>{text(item.label)}</span>
                      <span style={{ color: '#f8fafc', fontWeight: 600 }}>{item.value}</span>
                    </div>
                  ))}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {persona.tags.map((tag) => (
                    <span key={tag} style={{
                      padding: '4px 10px',
                      borderRadius: '999px',
                      background: 'rgba(15,23,42,0.9)',
                      border: `1px solid ${persona.accent}33`,
                      color: '#e2e8f0',
                      fontSize: '11px'
                    }}>
                      {tag}
                    </span>
                  ))}
                </div>
              </button>
            )
          })}
        </div>
      </section>

      <section style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '12px', letterSpacing: '1px' }}>Step 2</div>
            <h2 style={{ color: '#f8fafc', fontSize: '22px', marginBottom: '4px' }}>
              {text({ en: 'Choose intervention scenario', ja: '② どんな施策を試しますか？（シナリオ選択）' })}
            </h2>
            <p style={{ color: '#94a3b8', fontSize: '14px', maxWidth: '640px' }}>
              {text({
                en: 'Use scenario cards or craft a custom plan. Cards show: what changes vs baseline and expected indicators.',
                ja: 'プリセットのシナリオカード、もしくはカスタム設定で施策内容を定義します。カードにはベースラインとの差分と想定指標を表示。'
              })}
            </p>
          </div>
          <div style={{ alignSelf: 'flex-end', display: 'flex', gap: '8px', background: '#0f172a', padding: '4px', borderRadius: '12px', border: '1px solid #1e293b' }}>
            <button
              onClick={() => setScenarioTab('predefined')}
              style={{
                padding: '8px 16px',
                borderRadius: '10px',
                border: 'none',
                background: scenarioTab === 'predefined' ? 'linear-gradient(135deg,#3b82f6,#8b5cf6)' : 'transparent',
                color: scenarioTab === 'predefined' ? '#fff' : '#94a3b8',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              📋 {text({ en: 'Sample Scenarios', ja: 'サンプル施策シナリオ' })}
            </button>
            <button
              onClick={() => setScenarioTab('custom')}
              style={{
                padding: '8px 16px',
                borderRadius: '10px',
                border: 'none',
                background: scenarioTab === 'custom' ? 'linear-gradient(135deg,#10b981,#059669)' : 'transparent',
                color: scenarioTab === 'custom' ? '#fff' : '#94a3b8',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              ⚙️ {text({ en: 'Custom Scenario', ja: 'カスタムシナリオ（詳細設定）' })}
            </button>
          </div>
        </div>

        {scenarioTab === 'predefined' ? (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))',
            gap: '16px'
          }}>
            {SCENARIOS.map((scenario) => {
              const selected = scenario.id === selectedScenarioId
              return (
                <button
                  key={scenario.id}
                  onClick={() => setSelectedScenarioId(selected ? null : scenario.id)}
                  style={{
                    textAlign: 'left',
                    borderRadius: '18px',
                    padding: '20px',
                    border: selected ? `2px solid ${scenario.accent}` : '1px solid rgba(148,163,184,0.2)',
                    background: selected ? 'rgba(15,118,110,0.25)' : 'rgba(15,23,42,0.6)',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                >
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#f8fafc', marginBottom: '6px' }}>
                    {text(scenario.title)}
                  </div>
                  <div style={{ color: scenario.accent, fontSize: '13px', marginBottom: '12px' }}>
                    {text(scenario.summary)}
                  </div>
                  <div style={{ marginBottom: '12px' }}>
                    {scenario.parameters.map((param) => (
                      <div key={param.label.en} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: '#94a3b8' }}>
                        <span>{text(param.label)}</span>
                        <span style={{ color: '#f8fafc', fontWeight: 600 }}>{param.value}</span>
                      </div>
                    ))}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {scenario.impact.map((metric) => (
                      <div key={metric.label.en} style={{ fontSize: '13px', color: '#cbd5e1' }}>
                        <span style={{ color: '#94a3b8' }}>{text(metric.label)}:</span> <strong>{metric.value}</strong>
                      </div>
                    ))}
                  </div>
                </button>
              )
            })}
          </div>
        ) : (
          <div style={{
            borderRadius: '16px',
            border: '1px solid rgba(45,212,191,0.4)',
            padding: '24px',
            background: 'rgba(15,118,110,0.15)'
          }}>
            <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fit,minmax(220px,1fr))' }}>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', color: '#e2e8f0' }}>
                <span style={{ fontWeight: 600 }}>📝 {text({ en: 'Scenario name', ja: 'シナリオ名' })}</span>
                <input
                  type="text"
                  value={customScenario.name}
                  onChange={(e) => setCustomScenario((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="Q4 Loyalty Boost"
                  style={{
                    padding: '10px',
                    borderRadius: '8px',
                    border: '1px solid #334155',
                    background: '#0f172a',
                    color: '#f8fafc'
                  }}
                />
              </label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', color: '#e2e8f0' }}>
                <span style={{ fontWeight: 600 }}>📨 Email frequency (/month)</span>
                <input
                  type="range"
                  min={0}
                  max={4}
                  value={customScenario.emailFrequency}
                  onChange={(e) => setCustomScenario((prev) => ({ ...prev, emailFrequency: Number(e.target.value) }))}
                />
                <strong>{customScenario.emailFrequency}</strong>
              </label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', color: '#e2e8f0' }}>
                <span style={{ fontWeight: 600 }}>💰 Discount rate (%)</span>
                <input
                  type="range"
                  min={0}
                  max={30}
                  value={customScenario.discountRate}
                  onChange={(e) => setCustomScenario((prev) => ({ ...prev, discountRate: Number(e.target.value) }))}
                />
                <strong>{customScenario.discountRate}%</strong>
              </label>
              <label style={{ display: 'flex', flexDirection: 'column', gap: '6px', color: '#e2e8f0' }}>
                <span style={{ fontWeight: 600 }}>✨ Personalization</span>
                <input
                  type="range"
                  min={0}
                  max={100}
                  value={Math.round(customScenario.personalization * 100)}
                  onChange={(e) => setCustomScenario((prev) => ({ ...prev, personalization: Number(e.target.value) / 100 }))}
                />
                <strong>{Math.round(customScenario.personalization * 100)}%</strong>
              </label>
            </div>

            <div style={{ marginTop: '16px' }}>
              <div style={{ color: '#94a3b8', marginBottom: '8px' }}>{text({ en: 'Channels', ja: 'チャネル' })}</div>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {CHANNEL_CHOICES.map((channel) => {
                  const active = customScenario.channels.includes(channel)
                  return (
                    <button
                      key={channel}
                      onClick={() => handleChannelToggle(channel)}
                      style={{
                        padding: '8px 12px',
                        borderRadius: '999px',
                        border: active ? '1px solid #22d3ee' : '1px solid rgba(148,163,184,0.3)',
                        background: active ? 'rgba(34,211,238,0.15)' : 'transparent',
                        color: '#f8fafc',
                        cursor: 'pointer'
                      }}
                    >
                      {channel}
                    </button>
                  )
                })}
              </div>
            </div>

            <div style={{ marginTop: '20px', display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
              <button
                onClick={() => setSelectedScenarioId('custom')}
                style={{
                  padding: '12px 20px',
                  borderRadius: '10px',
                  border: 'none',
                  background: 'linear-gradient(135deg,#34d399,#0ea5e9)',
                  color: '#fff',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                ✅ {text({ en: 'Use this custom scenario', ja: 'このカスタム設定を使う' })}
              </button>
              <button
                onClick={() => setCustomScenario({ name: '', emailFrequency: 2, discountRate: 10, personalization: 0.6, channels: ['Email'] })}
                style={{
                  padding: '12px 20px',
                  borderRadius: '10px',
                  border: '1px solid rgba(148,163,184,0.3)',
                  background: 'transparent',
                  color: '#94a3b8',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                🔄 {text({ en: 'Reset form', ja: 'リセット' })}
              </button>
            </div>
          </div>
        )}
      </section>

      <section style={{ marginBottom: '32px' }}>
        <div style={{
          borderRadius: '20px',
          border: '1px solid rgba(148,163,184,0.3)',
          padding: '24px',
          background: 'rgba(15,23,42,0.7)',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit,minmax(280px,1fr))',
          gap: '20px'
        }}>
          <div>
            <h3 style={{ color: '#f8fafc', fontSize: '18px', marginBottom: '6px' }}>
              {selectedPersona && selectedScenario
                ? text({ en: 'Selected combo', ja: '選択中の組み合わせ' })
                : text({ en: 'No scenario selected', ja: 'シナリオ未選択' })}
            </h3>
            {selectedPersona && selectedScenario ? (
              <>
                <div style={{ color: '#94a3b8', marginBottom: '12px' }}>
                  {text(selectedPersona.name)} × {text(selectedScenario.title)}
                </div>
                <ul style={{ color: '#cbd5e1', fontSize: '13px', paddingLeft: '20px' }}>
                  <li>{text({ en: 'Persona baseline LTV and churn will be used as inputs.', ja: 'ペルソナのLTV/離反率をベースラインとして使用。' })}</li>
                  <li>{text({ en: 'Scenario parameters feed the causal simulator as intervention deltas.', ja: 'シナリオの設定値は介入差分として因果シミュレータへ渡されます。' })}</li>
                </ul>
              </>
            ) : (
              <p style={{ color: '#94a3b8', fontSize: '14px' }}>
                {text({
                  en: 'Select a persona and scenario below. The expected LTV / revenue impact will be displayed here once both are set.',
                  ja: '下でペルソナと施策シナリオを選ぶと、ここに想定LTV・売上インパクトが表示されます。'
                })}
              </p>
            )}
          </div>
          <div>
            <div style={{ color: '#94a3b8', fontSize: '12px', marginBottom: '8px' }}>
              {text({ en: 'Simulation preview', ja: 'シミュレーションプレビュー' })}
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(120px,1fr))', gap: '12px' }}>
              {['Projected Δ¥', 'ROI', 'CAS Score'].map((label) => (
                <div key={label} style={{
                  background: 'rgba(15,23,42,0.85)',
                  borderRadius: '12px',
                  padding: '12px',
                  border: '1px solid rgba(148,163,184,0.2)'
                }}>
                  <div style={{ color: '#94a3b8', fontSize: '11px' }}>{label}</div>
                  <div style={{ color: '#f8fafc', fontWeight: 700, fontSize: '16px' }}>
                    {selectedPersona && selectedScenario ? 'Pending run' : '—'}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div style={{ alignSelf: 'center' }}>
            <button
              onClick={handleRunSimulation}
              disabled={!isReadyToRun}
              style={{
                width: '100%',
                padding: '16px',
                borderRadius: '14px',
                border: 'none',
                background: isReadyToRun ? 'linear-gradient(135deg,#3b82f6,#8b5cf6)' : '#1e293b',
                color: '#fff',
                fontSize: '15px',
                fontWeight: 700,
                cursor: isReadyToRun ? 'pointer' : 'not-allowed',
                opacity: isReadyToRun ? 1 : 0.5
              }}
            >
              {text(runButtonCopy)}
            </button>
            <div style={{ color: '#94a3b8', fontSize: '12px', marginTop: '8px' }}>
              {text({
                en: 'Pick persona + scenario first. Outputs appear in Decision Console after the run.',
                ja: '先にペルソナとシナリオを両方選択してください。結果は Decision Console で確認できます。'
              })}
            </div>
          </div>
        </div>
      </section>

      <section style={{ marginBottom: '32px', display: 'grid', gap: '16px', gridTemplateColumns: 'minmax(260px,1fr) minmax(260px,1fr)' }}>
        <div style={{ borderRadius: '16px', border: '1px solid rgba(148,163,184,0.3)', padding: '24px', background: 'rgba(15,23,42,0.7)' }}>
          <h3 style={{ color: '#f8fafc', fontSize: '18px', marginBottom: '8px' }}>
            {text({ en: 'About Customer Digital Twin', ja: 'Customer Digital Twin について' })}
          </h3>
          <p style={{ color: '#cbd5e1', fontSize: '14px', lineHeight: 1.6 }}>
            {text(aboutText)}
          </p>
          <ul style={{ color: '#94a3b8', fontSize: '13px', lineHeight: 1.8, paddingLeft: '18px', marginTop: '12px' }}>
            <li>{text({ en: 'Works with approved persona definitions and intervention schema.', ja: '承認済みペルソナ定義と介入スキーマを利用。' })}</li>
            <li>{text({ en: 'No backend change is required—UI only clarifies the workflow.', ja: 'バックエンド変更なしでワークフローを明確にします。' })}</li>
            <li>{text({ en: 'Simulation logs appear in the Decision Console & Diagnostics tabs.', ja: 'シミュレーションログは Decision Console / Diagnostics に記録されます。' })}</li>
          </ul>
        </div>
        <div style={{ borderRadius: '16px', border: '1px solid rgba(148,163,184,0.3)', padding: '24px', background: 'rgba(15,23,42,0.6)' }}>
          <h3 style={{ color: '#f8fafc', fontSize: '18px', marginBottom: '8px' }}>
            twin.pdf
          </h3>
          <p style={{ color: '#cbd5e1', fontSize: '14px', marginBottom: '16px' }}>
            {text({
              en: 'Need the official specification? Download or open twin.pdf from backend docs.',
              ja: '公式仕様が必要な場合は twin.pdf をダウンロードしてください。'
            })}
          </p>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <a
              href={pdfUrl}
              target="_blank"
              rel="noreferrer"
              style={{
                padding: '12px 20px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg,#3b82f6,#8b5cf6)',
                color: '#fff',
                fontWeight: 600,
                textDecoration: 'none'
              }}
            >
              🔗 {text({ en: 'Open twin.pdf', ja: 'twin.pdf を開く' })}
            </a>
            <a
              href={pdfUrl}
              download="twin.pdf"
              style={{
                padding: '12px 20px',
                borderRadius: '10px',
                border: '1px solid rgba(148,163,184,0.4)',
                color: '#e2e8f0',
                fontWeight: 600,
                textDecoration: 'none'
              }}
            >
              📥 {text({ en: 'Download', ja: 'ダウンロード' })}
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}
