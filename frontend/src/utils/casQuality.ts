/**
 * CAS (Causal Assurance Score) Quality Utilities
 * 全画面で統一されたCAS品質表記
 */

export interface CASQualityBadge {
  label: string
  color: string
  bgColor: string
  borderColor: string
  canExport: boolean
  level: 'high' | 'medium' | 'low'
}

/**
 * CASスコアから品質バッジを取得
 * ≥0.8 = High, 0.6-0.8 = Medium, <0.6 = Low
 */
export function getCASQualityBadge(cas: number): CASQualityBadge {
  if (cas >= 0.8) {
    return {
      label: 'HIGH',
      color: '#10b981',
      bgColor: 'rgba(16, 185, 129, 0.1)',
      borderColor: '#10b981',
      canExport: true,
      level: 'high'
    }
  } else if (cas >= 0.6) {
    return {
      label: 'MEDIUM',
      color: '#f59e0b',
      bgColor: 'rgba(245, 158, 11, 0.1)',
      borderColor: '#f59e0b',
      canExport: true,
      level: 'medium'
    }
  } else {
    return {
      label: 'LOW',
      color: '#ef4444',
      bgColor: 'rgba(239, 68, 68, 0.1)',
      borderColor: '#ef4444',
      canExport: false,
      level: 'low'
    }
  }
}

/**
 * CASスコアから信頼度ラベルを取得
 */
export function getCASConfidenceLabel(cas: number): string {
  if (cas >= 0.8) return 'High Confidence'
  if (cas >= 0.6) return 'Medium Confidence'
  return 'Low Confidence'
}

/**
 * CASスコアの閾値定義（SSOT）
 */
export const CAS_THRESHOLDS = {
  HIGH: 0.8,
  MEDIUM: 0.6,
  EXPORT_MINIMUM: 0.6
} as const
