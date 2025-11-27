/**
 * Money formatting utilities
 * 主表示（短縮形）+ 補助表示（円表記）の二段表示
 */

/**
 * 短縮形：¥2.45M など
 */
const normalizeValue = (value: number | null | undefined): number | null => {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value
  }
  return null
}

const fallbackValue = (value: number | null): number => (value === null ? 0 : value)

export const formatYen = (input: number | null | undefined): string => {
  const value = normalizeValue(input)
  if (value === null) {
    return '–'
  }
  const rounded = Math.round(value)
  return `¥${rounded.toLocaleString('ja-JP')}`
}

export const formatYenShort = (input: number | null | undefined): string => {
  const value = normalizeValue(input)
  if (value === null) {
    return '–'
  }
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
export const formatYenFull = (input: number | null | undefined): string => {
  const value = fallbackValue(normalizeValue(input))
  return value.toLocaleString('ja-JP', {
    style: 'currency',
    currency: 'JPY',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  })
}

export const formatYenApprox = (input: number | null | undefined): string | null => {
  const value = normalizeValue(input)
  if (value === null) return null
  const abs = Math.abs(value)
  if (abs < 10_000) return null
  const man = abs / 10_000
  return `約${man.toFixed(1)}万円`
}

/**
 * 万円表記：約245万円 or – if too small
 */
export const formatYenMan = (input: number | null | undefined): string => {
  const approx = formatYenApprox(input)
  if (!approx) return '–'
  return approx
}

/**
 * 統合表示：短縮形 + 補助情報
 * 例: { main: "¥2.45M", sub: "約245万円" }
 */
export const formatYenWithSub = (
  value: number | null | undefined
): { main: string; sub: string } => {
  return {
    main: formatYenShort(value),
    sub: formatYenMan(value)
  }
}

/**
 * 差分表示（+ or - 付き）
 */
export const formatYenDelta = (input: number | null | undefined): string => {
  const value = fallbackValue(normalizeValue(input))
  const sign = value >= 0 ? '+' : ''
  return `${sign}${formatYenShort(value)}`
}

export const formatDecisionDate = (iso: string | null | undefined): string => {
  if (!iso) return '–'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '–'
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
