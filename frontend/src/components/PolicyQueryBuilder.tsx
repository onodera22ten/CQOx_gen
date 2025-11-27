/**
 * 【日本語サマリ】このモジュールはPolicy Lab用のGUIクエリビルダーを提供する。
 * - なぜ必要か: データサイエンティスト/マーケターがコード不要でpolicy候補を絞り込むため
 * - 何をするか: 視覚的なフィルタUI（スライダー/ドロップダウン）でポリシー条件を構築
 * - どう検証するか: フィルタ条件を変更して、結果リストがリアルタイムで更新されることを確認
 */

import React, { useState } from 'react'

export interface QueryFilter {
  field: string
  operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte' | 'contains'
  value: any
}

export interface PolicyQuery {
  filters: QueryFilter[]
  sortBy?: string
  sortOrder?: 'asc' | 'desc'
}

interface PolicyQueryBuilderProps {
  onQueryChange: (query: PolicyQuery) => void
  availableFields?: Array<{ name: string; type: 'number' | 'string' | 'boolean'; label: string }>
}

const defaultFields = [
  { name: 'delta_yen', type: 'number' as const, label: 'Δ¥ (Delta Yen)' },
  { name: 'cas_score', type: 'number' as const, label: 'CAS Score' },
  { name: 'risk_score', type: 'number' as const, label: 'Risk Score' },
  { name: 'roi', type: 'number' as const, label: 'ROI' },
  { name: 'channel', type: 'string' as const, label: 'Channel' },
  { name: 'segment', type: 'string' as const, label: 'Segment' },
  { name: 'verdict', type: 'string' as const, label: 'Verdict' },
]

export const PolicyQueryBuilder: React.FC<PolicyQueryBuilderProps> = ({
  onQueryChange,
  availableFields = defaultFields,
}) => {
  const [filters, setFilters] = useState<QueryFilter[]>([])
  const [sortBy, setSortBy] = useState<string>('delta_yen')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  const handleAddFilter = () => {
    const newFilter: QueryFilter = {
      field: availableFields[0].name,
      operator: 'gte',
      value: 0,
    }
    const newFilters = [...filters, newFilter]
    setFilters(newFilters)
    onQueryChange({ filters: newFilters, sortBy, sortOrder })
  }

  const handleRemoveFilter = (index: number) => {
    const newFilters = filters.filter((_, i) => i !== index)
    setFilters(newFilters)
    onQueryChange({ filters: newFilters, sortBy, sortOrder })
  }

  const handleFilterChange = (index: number, field: keyof QueryFilter, value: any) => {
    const newFilters = [...filters]
    newFilters[index] = { ...newFilters[index], [field]: value }
    setFilters(newFilters)
    onQueryChange({ filters: newFilters, sortBy, sortOrder })
  }

  const handleSortChange = (newSortBy: string, newSortOrder: 'asc' | 'desc') => {
    setSortBy(newSortBy)
    setSortOrder(newSortOrder)
    onQueryChange({ filters, sortBy: newSortBy, sortOrder: newSortOrder })
  }

  const getOperatorsForField = (fieldName: string) => {
    const field = availableFields.find((f) => f.name === fieldName)
    if (field?.type === 'number') {
      return [
        { value: 'gte', label: '≥' },
        { value: 'lte', label: '≤' },
        { value: 'gt', label: '>' },
        { value: 'lt', label: '<' },
        { value: 'eq', label: '=' },
      ]
    }
    return [
      { value: 'eq', label: '=' },
      { value: 'contains', label: '含む' },
    ]
  }

  return (
    <div
      style={{
        background: '#1e293b',
        borderRadius: '12px',
        padding: '24px',
        border: '1px solid #334155',
      }}
    >
      <div style={{ marginBottom: '20px' }}>
        <h3
          style={{
            fontSize: '18px',
            fontWeight: '600',
            color: '#fff',
            marginBottom: '8px',
          }}
        >
          🔍 Policy Query Builder
        </h3>
        <p style={{ fontSize: '13px', color: '#94a3b8' }}>
          Build queries to filter and sort policies visually
        </p>
      </div>

      {/* Filters */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <label style={{ fontSize: '14px', fontWeight: '600', color: '#cbd5e1' }}>
            Filters
          </label>
          <button
            onClick={handleAddFilter}
            style={{
              padding: '6px 12px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
              border: 'none',
              borderRadius: '6px',
              color: '#fff',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
            }}
          >
            + Add Filter
          </button>
        </div>

        {filters.length === 0 ? (
          <div
            style={{
              padding: '32px',
              textAlign: 'center',
              color: '#94a3b8',
              fontSize: '14px',
              background: '#0f172a',
              borderRadius: '8px',
              border: '1px dashed #334155',
            }}
          >
            No filters applied. Click "Add Filter" to start building your query.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {filters.map((filter, index) => {
              const field = availableFields.find((f) => f.name === filter.field)
              return (
                <div
                  key={index}
                  style={{
                    display: 'flex',
                    gap: '8px',
                    alignItems: 'center',
                    padding: '12px',
                    background: '#0f172a',
                    borderRadius: '8px',
                    border: '1px solid #334155',
                  }}
                >
                  {/* Field Select */}
                  <select
                    value={filter.field}
                    onChange={(e) => handleFilterChange(index, 'field', e.target.value)}
                    style={{
                      flex: 1,
                      padding: '8px',
                      background: '#1e293b',
                      border: '1px solid #475569',
                      borderRadius: '6px',
                      color: '#fff',
                      fontSize: '13px',
                    }}
                  >
                    {availableFields.map((f) => (
                      <option key={f.name} value={f.name}>
                        {f.label}
                      </option>
                    ))}
                  </select>

                  {/* Operator Select */}
                  <select
                    value={filter.operator}
                    onChange={(e) => handleFilterChange(index, 'operator', e.target.value)}
                    style={{
                      padding: '8px',
                      background: '#1e293b',
                      border: '1px solid #475569',
                      borderRadius: '6px',
                      color: '#fff',
                      fontSize: '13px',
                    }}
                  >
                    {getOperatorsForField(filter.field).map((op) => (
                      <option key={op.value} value={op.value}>
                        {op.label}
                      </option>
                    ))}
                  </select>

                  {/* Value Input */}
                  {field?.type === 'number' ? (
                    <input
                      type="number"
                      value={filter.value}
                      onChange={(e) => handleFilterChange(index, 'value', parseFloat(e.target.value))}
                      style={{
                        flex: 1,
                        padding: '8px',
                        background: '#1e293b',
                        border: '1px solid #475569',
                        borderRadius: '6px',
                        color: '#fff',
                        fontSize: '13px',
                      }}
                      step="any"
                    />
                  ) : (
                    <input
                      type="text"
                      value={filter.value}
                      onChange={(e) => handleFilterChange(index, 'value', e.target.value)}
                      style={{
                        flex: 1,
                        padding: '8px',
                        background: '#1e293b',
                        border: '1px solid #475569',
                        borderRadius: '6px',
                        color: '#fff',
                        fontSize: '13px',
                      }}
                    />
                  )}

                  {/* Remove Button */}
                  <button
                    onClick={() => handleRemoveFilter(index)}
                    style={{
                      padding: '8px 12px',
                      background: '#ef4444',
                      border: 'none',
                      borderRadius: '6px',
                      color: '#fff',
                      fontSize: '13px',
                      cursor: 'pointer',
                    }}
                    title="Remove filter"
                  >
                    ×
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Sort Controls */}
      <div style={{ marginBottom: '12px' }}>
        <label style={{ fontSize: '14px', fontWeight: '600', color: '#cbd5e1', marginBottom: '8px', display: 'block' }}>
          Sort By
        </label>
        <div style={{ display: 'flex', gap: '8px' }}>
          <select
            value={sortBy}
            onChange={(e) => handleSortChange(e.target.value, sortOrder)}
            style={{
              flex: 1,
              padding: '8px',
              background: '#0f172a',
              border: '1px solid #475569',
              borderRadius: '6px',
              color: '#fff',
              fontSize: '13px',
            }}
          >
            {availableFields.map((f) => (
              <option key={f.name} value={f.name}>
                {f.label}
              </option>
            ))}
          </select>
          <select
            value={sortOrder}
            onChange={(e) => handleSortChange(sortBy, e.target.value as 'asc' | 'desc')}
            style={{
              padding: '8px 16px',
              background: '#0f172a',
              border: '1px solid #475569',
              borderRadius: '6px',
              color: '#fff',
              fontSize: '13px',
            }}
          >
            <option value="desc">↓ Descending</option>
            <option value="asc">↑ Ascending</option>
          </select>
        </div>
      </div>

      {/* Query Summary */}
      {filters.length > 0 && (
        <div
          style={{
            marginTop: '16px',
            padding: '12px',
            background: 'rgba(59, 130, 246, 0.1)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            borderRadius: '8px',
          }}
        >
          <div style={{ fontSize: '12px', color: '#60a5fa', fontWeight: '600', marginBottom: '6px' }}>
            Query Summary:
          </div>
          <div style={{ fontSize: '12px', color: '#cbd5e1', fontFamily: 'monospace' }}>
            {filters.map((f, i) => (
              <div key={i}>
                {i > 0 && 'AND '}
                {availableFields.find((field) => field.name === f.field)?.label} {f.operator} {f.value}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

