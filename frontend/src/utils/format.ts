/**
 * Money formatting utilities
 * 主表示（短縮形）+ 補助表示（円表記）の二段表示
 */

/**
 * 短縮形：¥2.45M など
 */
export const formatYenShort = (value: number): string => {
  if (Math.abs(value) >= 1_000_000) {
    return `¥${(value / 1_000_000).toFixed(2)}M`
  } else if (Math.abs(value) >= 1_000) {
    return `¥${(value / 1_000).toFixed(0)}K`
  } else {
    return `¥${value.toLocaleString('ja-JP')}`
  }
}

/**
 * フル表記：￥2,450,000
 */
export const formatYenFull = (value: number): string => {
  return value.toLocaleString('ja-JP', {
    style: 'currency',
    currency: 'JPY',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  })
}

/**
 * 万円表記：約245万円
 */
export const formatYenMan = (value: number): string => {
  const man = Math.round(value / 10_000)
  return `約${man.toLocaleString('ja-JP')}万円`
}

/**
 * 統合表示：短縮形 + 補助情報
 * 例: { main: "¥2.45M", sub: "約245万円" }
 */
export const formatYenWithSub = (value: number): { main: string; sub: string } => {
  return {
    main: formatYenShort(value),
    sub: formatYenMan(value)
  }
}

/**
 * 差分表示（+ or - 付き）
 */
export const formatYenDelta = (value: number): string => {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${formatYenShort(value)}`
}
