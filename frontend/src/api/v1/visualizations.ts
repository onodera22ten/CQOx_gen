/**
 * Visualizations API Client
 *
 * 7種類の可視化エンドポイント:
 * 1. Pareto Frontier - ポリシーの利益-リスクトレードオフ
 * 2. Balance Plot (Love Plot) - 共変量バランス
 * 3. Overlap Density - 傾向スコアの重なり
 * 4. CATE Distribution - 異質性治療効果の分布
 * 5. Qini Curve - アップリフトモデル性能
 * 6. Calibration Plot - CATE予測の較正
 * 7. Sensitivity Analysis - 感度分析（Gamma）
 */

import { api } from '../../utils/api';

// ============================================================================
// Type Definitions
// ============================================================================

export interface Policy {
  name: string;
  profit: number;
  risk: number;
}

export interface ParetoFrontierRequest {
  policies: Policy[];
}

export interface ParetoFrontierResponse {
  image_url?: string;
  data: {
    efficient_frontier: Policy[];
    dominated_policies: Policy[];
  };
}

export interface BalancePlotRequest {
  variables: string[];
  smd_values: number[];
  threshold?: number;
}

export interface BalancePlotResponse {
  image_url?: string;
  data: {
    balanced_variables: string[];
    imbalanced_variables: string[];
    max_smd: number;
  };
}

export interface OverlapDensityRequest {
  propensity_scores_treatment: number[];
  propensity_scores_control: number[];
}

export interface OverlapDensityResponse {
  image_url?: string;
  data: {
    overlap_score: number;
    common_support_range: [number, number];
  };
}

export interface CATEDistributionRequest {
  cate_values: number[];
}

export interface CATEDistributionResponse {
  image_url?: string;
  data: {
    mean: number;
    std: number;
    median: number;
    q25: number;
    q75: number;
    heterogeneity_score: number;
  };
}

export interface QiniCurveRequest {
  uplift_scores: number[];
  treatment: number[];
  outcomes: number[];
}

export interface QiniCurveResponse {
  image_url?: string;
  data: {
    auc: number;
    optimal_treatment_fraction: number;
    max_uplift: number;
  };
}

export interface CalibrationPlotRequest {
  predicted_cate: number[];
  observed_cate: number[];
}

export interface CalibrationPlotResponse {
  image_url?: string;
  data: {
    calibration_score: number;
    slope: number;
    intercept: number;
  };
}

export interface SensitivityGammaRequest {
  gamma_values: number[];
  p_values: number[];
}

export interface SensitivityGammaResponse {
  image_url?: string;
  data: {
    critical_gamma: number;
    robust_at_gamma_2: boolean;
  };
}

// ============================================================================
// API Client
// ============================================================================

export const visualizationsAPI = {
  /**
   * Pareto Frontier可視化
   * 複数のポリシーの利益-リスクトレードオフを表示
   */
  paretoFrontier: async (
    request: ParetoFrontierRequest
  ): Promise<ParetoFrontierResponse> => {
    return await api.post<ParetoFrontierResponse>(
      '/api/visualizations/pareto-frontier',
      request
    );
  },

  /**
   * Balance Plot (Love Plot)
   * 治療群と対照群の共変量バランスを表示
   */
  balancePlot: async (
    request: BalancePlotRequest
  ): Promise<BalancePlotResponse> => {
    return await api.post<BalancePlotResponse>(
      '/api/visualizations/balance-plot',
      request
    );
  },

  /**
   * Overlap Density Plot
   * 傾向スコアの分布の重なりを表示
   */
  overlapDensity: async (
    request: OverlapDensityRequest
  ): Promise<OverlapDensityResponse> => {
    return await api.post<OverlapDensityResponse>(
      '/api/visualizations/overlap-density',
      request
    );
  },

  /**
   * CATE Distribution
   * 異質性治療効果(CATE)の分布を表示
   */
  cateDistribution: async (
    request: CATEDistributionRequest
  ): Promise<CATEDistributionResponse> => {
    return await api.post<CATEDistributionResponse>(
      '/api/visualizations/cate-distribution',
      request
    );
  },

  /**
   * Qini Curve
   * アップリフトモデリングの性能評価曲線
   */
  qiniCurve: async (
    request: QiniCurveRequest
  ): Promise<QiniCurveResponse> => {
    return await api.post<QiniCurveResponse>(
      '/api/visualizations/qini-curve',
      request
    );
  },

  /**
   * Calibration Plot
   * CATE予測値と実測値の較正プロット
   */
  calibrationPlot: async (
    request: CalibrationPlotRequest
  ): Promise<CalibrationPlotResponse> => {
    return await api.post<CalibrationPlotResponse>(
      '/api/visualizations/calibration-plot',
      request
    );
  },

  /**
   * Sensitivity Analysis (Gamma Plot)
   * 未観測交絡に対する感度分析
   */
  sensitivityGamma: async (
    request: SensitivityGammaRequest
  ): Promise<SensitivityGammaResponse> => {
    return await api.post<SensitivityGammaResponse>(
      '/api/visualizations/sensitivity-gamma',
      request
    );
  },
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * 分析結果から可視化データを生成
 */
export const generateVisualizationData = {
  /**
   * 分析結果からCATE分布データを抽出
   */
  fromAnalysisResult: (analysisResult: any): CATEDistributionRequest => {
    // TODO: 実際の分析結果構造に合わせて実装
    return {
      cate_values: analysisResult.cate_values || [],
    };
  },

  /**
   * 診断結果からバランスプロットデータを抽出
   */
  fromDiagnosticResult: (diagnosticResult: any): BalancePlotRequest => {
    return {
      variables: diagnosticResult.variables || [],
      smd_values: diagnosticResult.smd_values || [],
      threshold: 0.1,
    };
  },

  /**
   * ポリシー評価結果からParetoデータを抽出
   */
  fromPolicyEvaluation: (policies: any[]): ParetoFrontierRequest => {
    return {
      policies: policies.map((p) => ({
        name: p.name,
        profit: p.incremental_profit || 0,
        risk: p.risk_score || 0,
      })),
    };
  },
};

export default visualizationsAPI;
