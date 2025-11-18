/**
 * Visualizations Page
 * 因果推論の7種類の可視化を統合表示
 */

import { useState } from 'react';
import CATEDistributionChart from '../components/visualizations/CATEDistributionChart';
import BalancePlotChart from '../components/visualizations/BalancePlotChart';
import OverlapDensityChart from '../components/visualizations/OverlapDensityChart';
import ParetoFrontierChart from '../components/visualizations/ParetoFrontierChart';
import QiniCurveChart from '../components/visualizations/QiniCurveChart';
import CalibrationPlotChart from '../components/visualizations/CalibrationPlotChart';
import SensitivityGammaChart from '../components/visualizations/SensitivityGammaChart';

// サンプルデータ生成
const generateSampleData = () => {
  // CATE分布データ
  const cateValues = Array.from({ length: 1000 }, () =>
    Math.random() * 100 - 20 + (Math.random() - 0.5) * 40
  );

  // Balance Plot データ
  const variables = ['Age', 'Income', 'Gender', 'Region', 'Education', 'Employment'];
  const smdValues = variables.map(() => (Math.random() - 0.5) * 0.3);

  // Overlap Density データ
  const propensityTreatment = Array.from({ length: 500 }, () =>
    Math.max(0, Math.min(1, 0.6 + Math.random() * 0.3))
  );
  const propensityControl = Array.from({ length: 500 }, () =>
    Math.max(0, Math.min(1, 0.4 + Math.random() * 0.3))
  );

  // Pareto Frontier データ
  const policies = [
    { name: 'Policy A', profit: 150000, risk: 0.15 },
    { name: 'Policy B', profit: 200000, risk: 0.25 },
    { name: 'Policy C', profit: 120000, risk: 0.10 },
    { name: 'Policy D', profit: 180000, risk: 0.30 },
    { name: 'Policy E', profit: 250000, risk: 0.40 },
    { name: 'Policy F', profit: 100000, risk: 0.08 },
  ];

  // Qini Curve データ
  const upliftScores = Array.from({ length: 1000 }, () => Math.random());
  const treatment = Array.from({ length: 1000 }, () => Math.random() > 0.5 ? 1 : 0);
  const outcomes = upliftScores.map((score, i) =>
    treatment[i] ? score * 100 + 50 : Math.random() * 80
  );

  // Calibration Plot データ
  const predictedCate = Array.from({ length: 100 }, () => Math.random() * 100);
  const observedCate = predictedCate.map(p => p + (Math.random() - 0.5) * 30);

  // Sensitivity Gamma データ
  const gammaValues = [1, 1.2, 1.4, 1.6, 1.8, 2.0, 2.5, 3.0, 4.0, 5.0];
  const pValues = gammaValues.map(g => Math.max(0.001, 0.05 * Math.exp(-(g - 1))));

  return {
    cateValues,
    variables,
    smdValues,
    propensityTreatment,
    propensityControl,
    policies,
    upliftScores,
    treatment,
    outcomes,
    predictedCate,
    observedCate,
    gammaValues,
    pValues,
  };
};

export default function Visualizations() {
  const [activeTab, setActiveTab] = useState<string>('all');
  const sampleData = generateSampleData();

  const tabs = [
    { id: 'all', label: '📊 All Visualizations', icon: '📊' },
    { id: 'cate', label: 'CATE Distribution', icon: '📈' },
    { id: 'balance', label: 'Balance Plot', icon: '⚖️' },
    { id: 'overlap', label: 'Overlap Density', icon: '🔄' },
    { id: 'pareto', label: 'Pareto Frontier', icon: '🎯' },
    { id: 'qini', label: 'Qini Curve', icon: '📉' },
    { id: 'calibration', label: 'Calibration', icon: '🎚️' },
    { id: 'sensitivity', label: 'Sensitivity', icon: '🔬' },
  ];

  const renderVisualization = (id: string) => {
    switch (id) {
      case 'cate':
        return (
          <div key="cate">
            <CATEDistributionChart
              cateValues={sampleData.cateValues}
            />
          </div>
        );
      case 'balance':
        return (
          <div key="balance">
            <BalancePlotChart
              variables={sampleData.variables}
              smdValues={sampleData.smdValues}
              threshold={0.1}
            />
          </div>
        );
      case 'overlap':
        return (
          <div key="overlap">
            <OverlapDensityChart
              propensityScoresTreatment={sampleData.propensityTreatment}
              propensityScoresControl={sampleData.propensityControl}
            />
          </div>
        );
      case 'pareto':
        return (
          <div key="pareto">
            <ParetoFrontierChart
              policies={sampleData.policies}
            />
          </div>
        );
      case 'qini':
        return (
          <div key="qini">
            <QiniCurveChart
              upliftScores={sampleData.upliftScores}
              treatment={sampleData.treatment}
              outcomes={sampleData.outcomes}
            />
          </div>
        );
      case 'calibration':
        return (
          <div key="calibration">
            <CalibrationPlotChart
              predictedCate={sampleData.predictedCate}
              observedCate={sampleData.observedCate}
            />
          </div>
        );
      case 'sensitivity':
        return (
          <div key="sensitivity">
            <SensitivityGammaChart
              gammaValues={sampleData.gammaValues}
              pValues={sampleData.pValues}
            />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{
          fontSize: '32px',
          fontWeight: '700',
          marginBottom: '12px',
          color: '#fff',
          background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}>
          📊 Causal Inference Visualizations
        </h1>
        <p style={{
          fontSize: '16px',
          color: '#94a3b8',
          marginBottom: '24px',
        }}>
          7種類の高度な可視化で因果推論の結果を深く理解
        </p>

        {/* Info Card */}
        <div style={{
          padding: '16px',
          background: 'rgba(59, 130, 246, 0.1)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          borderRadius: '12px',
          marginBottom: '24px',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <span style={{ fontSize: '24px' }}>💡</span>
            <strong style={{ color: '#60a5fa', fontSize: '16px' }}>Using Sample Data</strong>
          </div>
          <p style={{ margin: 0, color: '#cbd5e1', fontSize: '14px', lineHeight: '1.6' }}>
            現在、サンプルデータを使用して可視化を表示しています。実際の分析結果を表示するには、
            <strong style={{ color: '#60a5fa' }}> Causal Design & Evaluation</strong> ページで分析を実行してください。
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: '8px',
        overflowX: 'auto',
        marginBottom: '32px',
        borderBottom: '1px solid #334155',
        paddingBottom: '8px',
      }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '12px 20px',
              background: activeTab === tab.id
                ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)'
                : 'rgba(51, 65, 85, 0.5)',
              border: 'none',
              borderRadius: '8px',
              color: activeTab === tab.id ? '#fff' : '#cbd5e1',
              fontSize: '14px',
              fontWeight: activeTab === tab.id ? '600' : '500',
              cursor: 'pointer',
              transition: 'all 0.2s',
              whiteSpace: 'nowrap',
            }}
            onMouseEnter={(e) => {
              if (activeTab !== tab.id) {
                e.currentTarget.style.background = 'rgba(59, 130, 246, 0.2)';
              }
            }}
            onMouseLeave={(e) => {
              if (activeTab !== tab.id) {
                e.currentTarget.style.background = 'rgba(51, 65, 85, 0.5)';
              }
            }}
          >
            <span style={{ marginRight: '8px' }}>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Visualizations */}
      <div>
        {activeTab === 'all' ? (
          // Show all visualizations
          <div style={{ display: 'grid', gap: '32px' }}>
            {tabs.slice(1).map(tab => renderVisualization(tab.id))}
          </div>
        ) : (
          // Show selected visualization
          renderVisualization(activeTab)
        )}
      </div>

      {/* Footer Info */}
      <div style={{
        marginTop: '48px',
        padding: '24px',
        background: 'rgba(15, 23, 42, 0.6)',
        border: '1px solid #1e293b',
        borderRadius: '12px',
      }}>
        <h3 style={{ margin: '0 0 16px 0', color: '#f1f5f9', fontSize: '18px' }}>
          📚 Visualization Guide
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px', color: '#cbd5e1', fontSize: '14px' }}>
          <div>
            <strong style={{ color: '#60a5fa' }}>CATE Distribution:</strong> 治療効果の異質性を確認。分散が大きい場合は個別化治療の検討を推奨。
          </div>
          <div>
            <strong style={{ color: '#60a5fa' }}>Balance Plot:</strong> 共変量のバランスを確認。SMD &lt; 0.1が目標。
          </div>
          <div>
            <strong style={{ color: '#60a5fa' }}>Overlap Density:</strong> 傾向スコアの重なりを確認。重なりが少ない場合は推定の信頼性が低下。
          </div>
          <div>
            <strong style={{ color: '#60a5fa' }}>Pareto Frontier:</strong> 複数のポリシーの利益-リスクトレードオフを比較。
          </div>
          <div>
            <strong style={{ color: '#60a5fa' }}>Qini Curve:</strong> アップリフトモデルの性能評価。AUCが高いほど良好。
          </div>
          <div>
            <strong style={{ color: '#60a5fa' }}>Calibration Plot:</strong> CATE予測の較正を確認。45度線に近いほど正確。
          </div>
          <div>
            <strong style={{ color: '#60a5fa' }}>Sensitivity Analysis:</strong> 未観測交絡への頑健性を評価。Gamma &gt; 2で頑健なら信頼性高。
          </div>
        </div>
      </div>
    </div>
  );
}
