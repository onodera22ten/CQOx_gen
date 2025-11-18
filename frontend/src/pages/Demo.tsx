import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  demoAPI,
  DemoDataset,
  DemoAnalysisResult,
  DemoDatasetRequest
} from '../api/v1/demo';

// Step enum for wizard
enum WizardStep {
  DATA_GENERATION = 1,
  ANALYSIS_SETUP = 2,
  RUNNING = 3,
  RESULTS = 4,
}

// Preset scenarios
const PRESET_SCENARIOS = [
  {
    id: 'marketing',
    name: 'マーケティングキャンペーン効果測定',
    description: 'メールキャンペーンの売上への影響を測定',
    icon: '📧',
    dataType: 'observational' as const,
    sampleSize: 10000,
    treatmentEffect: 50,
    estimators: ['DR', 'IPW', 'PSM'],
  },
  {
    id: 'medical',
    name: '医療介入の効果検証',
    description: '新薬の治療効果をRCTで検証',
    icon: '💊',
    dataType: 'rct' as const,
    sampleSize: 5000,
    treatmentEffect: 15,
    estimators: ['DR', 'IPW'],
  },
  {
    id: 'pricing',
    name: '価格変更の影響分析',
    description: '価格変更が需要に与える影響を分析',
    icon: '💰',
    dataType: 'panel' as const,
    sampleSize: 8000,
    treatmentEffect: -25,
    estimators: ['DiD', 'FE'],
  },
];

export default function Demo() {
  // State management
  const [currentStep, setCurrentStep] = useState<WizardStep>(WizardStep.DATA_GENERATION);
  const [autoRun, setAutoRun] = useState(false);
  const [showTutorial, setShowTutorial] = useState(true);

  // Data generation parameters
  const [dataType, setDataType] = useState<'rct' | 'observational' | 'panel'>('rct');
  const [sampleSize, setSampleSize] = useState(5000);
  const [treatmentEffect, setTreatmentEffect] = useState(20);

  // Analysis parameters
  const [selectedEstimators, setSelectedEstimators] = useState<string[]>(['DR', 'IPW']);

  // Results
  const [generatedDataset, setGeneratedDataset] = useState<DemoDataset | null>(null);
  const [analysisResult, setAnalysisResult] = useState<DemoAnalysisResult | null>(null);
  const [polling, setPolling] = useState(false);

  // Generate dataset mutation
  const generateMutation = useMutation({
    mutationFn: async (request: DemoDatasetRequest) => {
      return await demoAPI.generateDataset(request);
    },
    onSuccess: (data) => {
      setGeneratedDataset(data);
      if (autoRun) {
        setTimeout(() => setCurrentStep(WizardStep.ANALYSIS_SETUP), 1000);
      } else {
        setCurrentStep(WizardStep.ANALYSIS_SETUP);
      }
    },
    onError: (error: any) => {
      alert(`データ生成に失敗しました: ${error.message || '不明なエラー'}`);
    }
  });

  // Run analysis mutation
  const analyzeMutation = useMutation({
    mutationFn: async (params: { dataset_id: string; estimators: string[] }) => {
      return await demoAPI.runAnalysis({
        dataset_id: params.dataset_id,
        estimators: params.estimators,
      });
    },
    onSuccess: (data) => {
      setAnalysisResult(data);
      setCurrentStep(WizardStep.RUNNING);
      setPolling(true);
    },
    onError: (error: any) => {
      alert(`分析開始に失敗しました: ${error.message || '不明なエラー'}`);
    }
  });

  // Poll for analysis completion
  useEffect(() => {
    if (!polling || !analysisResult) return;

    const interval = setInterval(async () => {
      try {
        const status = await demoAPI.getAnalysis(analysisResult.analysis_id);
        setAnalysisResult(status);

        if (status.status === 'completed' || status.status === 'failed') {
          setPolling(false);
          setCurrentStep(WizardStep.RESULTS);
        }
      } catch (error) {
        console.error('Failed to poll analysis status:', error);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [polling, analysisResult]);

  // Auto-run effect
  useEffect(() => {
    if (autoRun && currentStep === WizardStep.ANALYSIS_SETUP && generatedDataset) {
      setTimeout(() => handleRunAnalysis(), 1500);
    }
  }, [autoRun, currentStep, generatedDataset]);

  // Handlers
  const handleGenerateDataset = () => {
    generateMutation.mutate({
      data_type: dataType,
      sample_size: sampleSize,
      treatment_effect: treatmentEffect,
    });
  };

  const handleRunAnalysis = () => {
    if (!generatedDataset) return;

    analyzeMutation.mutate({
      dataset_id: generatedDataset.dataset_id,
      estimators: selectedEstimators,
    });
  };

  const handlePresetClick = (preset: typeof PRESET_SCENARIOS[0]) => {
    setDataType(preset.dataType);
    setSampleSize(preset.sampleSize);
    setTreatmentEffect(preset.treatmentEffect);
    setSelectedEstimators(preset.estimators);
    setShowTutorial(false);
  };

  const handleReset = () => {
    setCurrentStep(WizardStep.DATA_GENERATION);
    setGeneratedDataset(null);
    setAnalysisResult(null);
    setPolling(false);
    setAutoRun(false);
  };

  // Get estimator name
  const getEstimatorName = (code: string) => {
    const names: Record<string, string> = {
      'DR': 'Doubly Robust',
      'IPW': 'Inverse Propensity Weighting',
      'PSM': 'Propensity Score Matching',
      'DiD': 'Difference-in-Differences',
      'FE': 'Fixed Effects',
      'IV': 'Instrumental Variables',
    };
    return names[code] || code;
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{
          fontSize: '36px',
          fontWeight: '700',
          marginBottom: '8px',
          background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          因果推論デモ
        </h1>
        <p style={{ color: '#94A3B8', fontSize: '16px' }}>
          因果推論の基本を体験しましょう。データ生成から分析まで、すべてのステップをガイドします。
        </p>
      </div>

      {/* Tutorial banner */}
      {showTutorial && (
        <div style={{
          marginBottom: '24px',
          padding: '20px',
          background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1))',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '16px',
        }}>
          <div style={{ fontSize: '32px' }}>💡</div>
          <div style={{ flex: 1 }}>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px', color: '#F1F5F9' }}>
              初めての方へ
            </h3>
            <p style={{ color: '#94A3B8', marginBottom: '12px', lineHeight: '1.6' }}>
              このデモでは、因果推論の基本的な流れを体験できます。
              データを生成し、適切な推定手法を選択して、治療効果を測定します。
            </p>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => setAutoRun(true)}
                style={{
                  padding: '8px 16px',
                  background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                自動実行で始める
              </button>
              <button
                onClick={() => setShowTutorial(false)}
                style={{
                  padding: '8px 16px',
                  background: 'transparent',
                  color: '#94A3B8',
                  border: '1px solid rgba(148, 163, 184, 0.3)',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                閉じる
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Progress Bar */}
      <div style={{ marginBottom: '32px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
          {[
            { step: WizardStep.DATA_GENERATION, label: 'データ生成', icon: '📊' },
            { step: WizardStep.ANALYSIS_SETUP, label: '分析設定', icon: '⚙️' },
            { step: WizardStep.RUNNING, label: '実行中', icon: '🚀' },
            { step: WizardStep.RESULTS, label: '結果', icon: '📈' },
          ].map((item) => (
            <div
              key={item.step}
              style={{
                flex: 1,
                textAlign: 'center',
                opacity: currentStep >= item.step ? 1 : 0.5,
                transition: 'opacity 0.3s ease',
              }}
            >
              <div style={{
                width: '48px',
                height: '48px',
                margin: '0 auto 8px',
                borderRadius: '50%',
                background: currentStep >= item.step
                  ? 'linear-gradient(135deg, #3b82f6, #8b5cf6)'
                  : 'rgba(148, 163, 184, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '24px',
                transition: 'all 0.3s ease',
              }}>
                {item.icon}
              </div>
              <div style={{
                fontSize: '14px',
                fontWeight: '600',
                color: currentStep >= item.step ? '#F1F5F9' : '#64748B'
              }}>
                {item.label}
              </div>
            </div>
          ))}
        </div>
        <div style={{
          height: '4px',
          background: 'rgba(148, 163, 184, 0.2)',
          borderRadius: '2px',
          overflow: 'hidden',
        }}>
          <div style={{
            height: '100%',
            width: `${((currentStep - 1) / 3) * 100}%`,
            background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
            transition: 'width 0.5s ease',
          }} />
        </div>
      </div>

      {/* Preset Scenarios */}
      {currentStep === WizardStep.DATA_GENERATION && !generatedDataset && (
        <div style={{ marginBottom: '32px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '16px', color: '#F1F5F9' }}>
            プリセットシナリオ
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
            {PRESET_SCENARIOS.map((preset) => (
              <div
                key={preset.id}
                onClick={() => handlePresetClick(preset)}
                style={{
                  padding: '20px',
                  background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(37, 52, 70, 0.8))',
                  border: '1px solid rgba(59, 130, 246, 0.3)',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.borderColor = 'rgba(59, 130, 246, 0.6)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.borderColor = 'rgba(59, 130, 246, 0.3)';
                }}
              >
                <div style={{ fontSize: '48px', marginBottom: '12px' }}>{preset.icon}</div>
                <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px', color: '#F1F5F9' }}>
                  {preset.name}
                </h3>
                <p style={{ color: '#94A3B8', fontSize: '14px', marginBottom: '12px' }}>
                  {preset.description}
                </p>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <span style={{
                    padding: '4px 8px',
                    background: 'rgba(59, 130, 246, 0.2)',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: '#60a5fa',
                  }}>
                    {preset.dataType.toUpperCase()}
                  </span>
                  <span style={{
                    padding: '4px 8px',
                    background: 'rgba(16, 185, 129, 0.2)',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: '#10b981',
                  }}>
                    N={preset.sampleSize.toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Step 1: Data Generation */}
      {currentStep === WizardStep.DATA_GENERATION && (
        <div className="card">
          <div className="card-title">ステップ1: データ生成</div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
            {/* Data Type */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#F1F5F9' }}>
                データタイプ
                <span style={{
                  marginLeft: '8px',
                  fontSize: '12px',
                  color: '#94A3B8',
                  cursor: 'help',
                  borderBottom: '1px dotted #94A3B8',
                }}>
                  ？
                </span>
              </label>
              <select
                value={dataType}
                onChange={(e) => setDataType(e.target.value as any)}
                disabled={generateMutation.isPending}
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  background: '#253446',
                  color: '#F1F5F9',
                  fontSize: '14px',
                }}
              >
                <option value="rct">RCT (ランダム化比較試験)</option>
                <option value="observational">Observational (観察研究)</option>
                <option value="panel">Panel (パネルデータ)</option>
              </select>
              <div style={{ marginTop: '8px', fontSize: '12px', color: '#94A3B8' }}>
                {dataType === 'rct' && '完全にランダム化された治療割り当て'}
                {dataType === 'observational' && '交絡因子が存在する観察データ'}
                {dataType === 'panel' && '時系列×個体のパネル構造'}
              </div>
            </div>

            {/* Sample Size */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#F1F5F9' }}>
                サンプル数: {sampleSize.toLocaleString()}
              </label>
              <input
                type="range"
                min="1000"
                max="100000"
                step="1000"
                value={sampleSize}
                onChange={(e) => setSampleSize(parseInt(e.target.value))}
                disabled={generateMutation.isPending}
                style={{ width: '100%' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
                <span>1K</span>
                <span>100K</span>
              </div>
            </div>

            {/* Treatment Effect */}
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', color: '#F1F5F9' }}>
                真の治療効果: {treatmentEffect > 0 ? '+' : ''}{treatmentEffect}
              </label>
              <input
                type="range"
                min="-100"
                max="100"
                step="5"
                value={treatmentEffect}
                onChange={(e) => setTreatmentEffect(parseInt(e.target.value))}
                disabled={generateMutation.isPending}
                style={{ width: '100%' }}
              />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
                <span>-100</span>
                <span>0</span>
                <span>+100</span>
              </div>
            </div>
          </div>

          <button
            className="btn btn-primary"
            onClick={handleGenerateDataset}
            disabled={generateMutation.isPending}
            style={{ marginTop: '24px', width: '100%' }}
          >
            {generateMutation.isPending ? '生成中...' : 'データを生成'}
          </button>
        </div>
      )}

      {/* Dataset Preview */}
      {generatedDataset && currentStep === WizardStep.ANALYSIS_SETUP && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <div className="card-title">生成されたデータセット</div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '20px' }}>
            <div style={{ padding: '16px', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '8px' }}>
              <div style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '4px' }}>データタイプ</div>
              <div style={{ fontSize: '18px', fontWeight: '600', color: '#F1F5F9' }}>
                {generatedDataset.data_type.toUpperCase()}
              </div>
            </div>
            <div style={{ padding: '16px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '8px' }}>
              <div style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '4px' }}>サンプル数</div>
              <div style={{ fontSize: '18px', fontWeight: '600', color: '#F1F5F9' }}>
                {generatedDataset.sample_size.toLocaleString()}
              </div>
            </div>
            <div style={{ padding: '16px', background: 'rgba(245, 158, 11, 0.1)', borderRadius: '8px' }}>
              <div style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '4px' }}>真の効果</div>
              <div style={{ fontSize: '18px', fontWeight: '600', color: '#F1F5F9' }}>
                {generatedDataset.treatment_effect > 0 ? '+' : ''}{generatedDataset.treatment_effect}
              </div>
            </div>
            <div style={{ padding: '16px', background: 'rgba(139, 92, 246, 0.1)', borderRadius: '8px' }}>
              <div style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '4px' }}>カラム数</div>
              <div style={{ fontSize: '18px', fontWeight: '600', color: '#F1F5F9' }}>
                {generatedDataset.columns.length}
              </div>
            </div>
          </div>

          {/* Data Preview */}
          <div style={{ marginTop: '16px', overflowX: 'auto' }}>
            <div style={{ fontSize: '14px', fontWeight: '600', marginBottom: '8px', color: '#94A3B8' }}>
              データプレビュー (先頭5行)
            </div>
            <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #334155' }}>
                  {generatedDataset.columns.map((col) => (
                    <th key={col} style={{ padding: '8px', textAlign: 'left', color: '#94A3B8', fontWeight: '600' }}>
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {generatedDataset.preview_data.slice(0, 5).map((row, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #1E293B' }}>
                    {generatedDataset.columns.map((col) => (
                      <td key={col} style={{ padding: '8px', color: '#F1F5F9' }}>
                        {typeof row[col] === 'number' ? row[col].toFixed(2) : row[col]}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Step 2: Analysis Setup */}
      {currentStep === WizardStep.ANALYSIS_SETUP && generatedDataset && (
        <div className="card">
          <div className="card-title">ステップ2: 分析設定</div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', marginBottom: '12px', fontWeight: '500', color: '#F1F5F9' }}>
              推定手法を選択
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
              {['DR', 'IPW', 'PSM', 'DiD', 'FE', 'IV'].map((estimator) => (
                <label
                  key={estimator}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    padding: '12px',
                    background: selectedEstimators.includes(estimator)
                      ? 'rgba(59, 130, 246, 0.2)'
                      : 'rgba(148, 163, 184, 0.1)',
                    border: `1px solid ${selectedEstimators.includes(estimator) ? 'rgba(59, 130, 246, 0.5)' : 'rgba(148, 163, 184, 0.2)'}`,
                    borderRadius: '8px',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedEstimators.includes(estimator)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedEstimators([...selectedEstimators, estimator]);
                      } else {
                        setSelectedEstimators(selectedEstimators.filter(e => e !== estimator));
                      }
                    }}
                    disabled={analyzeMutation.isPending}
                    style={{ marginRight: '8px' }}
                  />
                  <div>
                    <div style={{ fontWeight: '600', color: '#F1F5F9', fontSize: '14px' }}>{estimator}</div>
                    <div style={{ fontSize: '11px', color: '#94A3B8' }}>{getEstimatorName(estimator)}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              className="btn btn-secondary"
              onClick={handleReset}
              style={{ flex: 1 }}
            >
              最初に戻る
            </button>
            <button
              className="btn btn-primary"
              onClick={handleRunAnalysis}
              disabled={analyzeMutation.isPending || selectedEstimators.length === 0}
              style={{ flex: 2 }}
            >
              {analyzeMutation.isPending ? '開始中...' : '分析を実行'}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Running */}
      {currentStep === WizardStep.RUNNING && analysisResult && (
        <div className="card">
          <div className="card-title">ステップ3: 分析実行中</div>

          <div style={{ textAlign: 'center', padding: '40px 20px' }}>
            <div style={{
              fontSize: '64px',
              marginBottom: '20px',
              animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }}>
              🚀
            </div>
            <div style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px', color: '#F1F5F9' }}>
              因果推論を実行しています...
            </div>
            <div style={{ fontSize: '14px', color: '#94A3B8', marginBottom: '24px' }}>
              選択した推定手法で治療効果を計算中
            </div>

            <div style={{
              width: '100%',
              maxWidth: '400px',
              margin: '0 auto',
              height: '8px',
              background: 'rgba(148, 163, 184, 0.2)',
              borderRadius: '4px',
              overflow: 'hidden',
            }}>
              <div style={{
                height: '100%',
                width: `${analysisResult.progress * 100}%`,
                background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)',
                transition: 'width 0.5s ease',
              }} />
            </div>
            <div style={{ marginTop: '8px', fontSize: '14px', color: '#94A3B8' }}>
              {(analysisResult.progress * 100).toFixed(0)}% 完了
            </div>
          </div>
        </div>
      )}

      {/* Step 4: Results */}
      {currentStep === WizardStep.RESULTS && analysisResult && analysisResult.status === 'completed' && (
        <div>
          {/* Summary Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginBottom: '24px' }}>
            <div style={{
              padding: '24px',
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(5, 150, 105, 0.1))',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '12px',
            }}>
              <div style={{ fontSize: '14px', color: '#94A3B8', marginBottom: '8px' }}>真の治療効果 (ATE)</div>
              <div style={{ fontSize: '36px', fontWeight: '700', color: '#10b981' }}>
                {analysisResult.true_ate > 0 ? '+' : ''}{analysisResult.true_ate.toFixed(2)}
              </div>
            </div>

            <div style={{
              padding: '24px',
              background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(37, 99, 235, 0.1))',
              border: '1px solid rgba(59, 130, 246, 0.3)',
              borderRadius: '12px',
            }}>
              <div style={{ fontSize: '14px', color: '#94A3B8', marginBottom: '8px' }}>推定された治療効果</div>
              <div style={{ fontSize: '36px', fontWeight: '700', color: '#3b82f6' }}>
                {analysisResult.estimated_ate > 0 ? '+' : ''}{analysisResult.estimated_ate.toFixed(2)}
              </div>
            </div>

            <div style={{
              padding: '24px',
              background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(124, 58, 237, 0.1))',
              border: '1px solid rgba(139, 92, 246, 0.3)',
              borderRadius: '12px',
            }}>
              <div style={{ fontSize: '14px', color: '#94A3B8', marginBottom: '8px' }}>バイアス</div>
              <div style={{ fontSize: '36px', fontWeight: '700', color: '#8b5cf6' }}>
                {Math.abs(analysisResult.estimated_ate - analysisResult.true_ate).toFixed(2)}
              </div>
            </div>
          </div>

          {/* Estimator Results */}
          <div className="card">
            <div className="card-title">推定手法ごとの結果</div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid #334155' }}>
                    <th style={{ padding: '12px', textAlign: 'left', color: '#94A3B8', fontWeight: '600' }}>推定手法</th>
                    <th style={{ padding: '12px', textAlign: 'right', color: '#94A3B8', fontWeight: '600' }}>推定値</th>
                    <th style={{ padding: '12px', textAlign: 'right', color: '#94A3B8', fontWeight: '600' }}>標準誤差</th>
                    <th style={{ padding: '12px', textAlign: 'right', color: '#94A3B8', fontWeight: '600' }}>95% CI</th>
                    <th style={{ padding: '12px', textAlign: 'right', color: '#94A3B8', fontWeight: '600' }}>バイアス</th>
                  </tr>
                </thead>
                <tbody>
                  {analysisResult.estimator_results.map((result) => (
                    <tr key={result.estimator} style={{ borderBottom: '1px solid #1E293B' }}>
                      <td style={{ padding: '12px', color: '#F1F5F9', fontWeight: '600' }}>
                        {result.estimator}
                        <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 'normal' }}>
                          {getEstimatorName(result.estimator)}
                        </div>
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: '#F1F5F9', fontWeight: '600' }}>
                        {result.estimate.toFixed(2)}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: '#94A3B8' }}>
                        {result.std_error.toFixed(3)}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: '#94A3B8', fontSize: '13px' }}>
                        [{result.ci_lower.toFixed(2)}, {result.ci_upper.toFixed(2)}]
                      </td>
                      <td style={{
                        padding: '12px',
                        textAlign: 'right',
                        color: Math.abs(result.bias) < 2 ? '#10b981' : Math.abs(result.bias) < 5 ? '#f59e0b' : '#ef4444',
                        fontWeight: '600',
                      }}>
                        {Math.abs(result.bias).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
            <button
              className="btn btn-secondary"
              onClick={handleReset}
              style={{ flex: 1 }}
            >
              最初からやり直す
            </button>
            <button
              className="btn btn-primary"
              onClick={() => {
                setCurrentStep(WizardStep.DATA_GENERATION);
                setGeneratedDataset(null);
                setAnalysisResult(null);
              }}
              style={{ flex: 1 }}
            >
              新しいデータで試す
            </button>
          </div>
        </div>
      )}

      {/* Error state */}
      {analysisResult && analysisResult.status === 'failed' && (
        <div className="card" style={{
          border: '1px solid rgba(239, 68, 68, 0.5)',
          background: 'rgba(239, 68, 68, 0.1)',
        }}>
          <div style={{ textAlign: 'center', padding: '40px 20px' }}>
            <div style={{ fontSize: '64px', marginBottom: '20px' }}>❌</div>
            <div style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px', color: '#ef4444' }}>
              分析に失敗しました
            </div>
            <div style={{ fontSize: '14px', color: '#94A3B8', marginBottom: '24px' }}>
              {analysisResult.error_message || 'エラーが発生しました'}
            </div>
            <button className="btn btn-secondary" onClick={handleReset}>
              最初に戻る
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
