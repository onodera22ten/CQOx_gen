/**
 * CATE分布ヒストグラムチャート
 * 条件付き平均処置効果の分布を可視化
 */

import { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from 'recharts';
import VisualizationCard from './VisualizationCard';

interface CATEDistributionChartProps {
  cateValues: number[];
  isLoading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  binCount?: number;
}

interface HistogramBin {
  binStart: number;
  binEnd: number;
  binCenter: number;
  count: number;
  frequency: number;
}

interface Statistics {
  mean: number;
  median: number;
  q1: number;
  q3: number;
  min: number;
  max: number;
  std: number;
}

export default function CATEDistributionChart({
  cateValues,
  isLoading = false,
  error = null,
  onRefresh,
  binCount = 30,
}: CATEDistributionChartProps) {
  // 統計量とヒストグラムデータを計算
  const { statistics, histogramData } = useMemo(() => {
    if (!cateValues || cateValues.length === 0) {
      return {
        statistics: null,
        histogramData: [],
      };
    }

    // 統計量を計算
    const sorted = [...cateValues].sort((a, b) => a - b);
    const n = sorted.length;
    const mean = sorted.reduce((sum, val) => sum + val, 0) / n;
    const median = n % 2 === 0
      ? (sorted[n / 2 - 1] + sorted[n / 2]) / 2
      : sorted[Math.floor(n / 2)];
    const q1 = sorted[Math.floor(n * 0.25)];
    const q3 = sorted[Math.floor(n * 0.75)];
    const min = sorted[0];
    const max = sorted[n - 1];

    // 標準偏差を計算
    const variance = sorted.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / n;
    const std = Math.sqrt(variance);

    const stats: Statistics = { mean, median, q1, q3, min, max, std };

    // ヒストグラムデータを作成
    const range = max - min;
    const binWidth = range / binCount;
    const bins: HistogramBin[] = [];

    for (let i = 0; i < binCount; i++) {
      const binStart = min + i * binWidth;
      const binEnd = binStart + binWidth;
      const binCenter = (binStart + binEnd) / 2;

      const count = cateValues.filter(
        val => val >= binStart && (i === binCount - 1 ? val <= binEnd : val < binEnd)
      ).length;

      bins.push({
        binStart,
        binEnd,
        binCenter,
        count,
        frequency: (count / n) * 100,
      });
    }

    return {
      statistics: stats,
      histogramData: bins,
    };
  }, [cateValues, binCount]);

  // メトリクス表示用データ
  const metrics = statistics
    ? [
        { label: 'Mean CATE', value: statistics.mean.toFixed(3) },
        { label: 'Median CATE', value: statistics.median.toFixed(3) },
        { label: 'Std Dev', value: statistics.std.toFixed(3) },
        { label: 'IQR', value: (statistics.q3 - statistics.q1).toFixed(3) },
      ]
    : [];

  // カスタムツールチップ
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as HistogramBin;
      return (
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid #334155',
            borderRadius: '6px',
            padding: '12px',
            color: '#f1f5f9',
          }}
        >
          <p style={{ margin: '0 0 4px 0', fontSize: '12px', color: '#94a3b8' }}>
            Range: [{data.binStart.toFixed(3)}, {data.binEnd.toFixed(3)})
          </p>
          <p style={{ margin: '0', fontSize: '14px', fontWeight: '600' }}>
            Count: {data.count}
          </p>
          <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#94a3b8' }}>
            Frequency: {data.frequency.toFixed(2)}%
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <VisualizationCard
      title="CATE Distribution"
      description="Distribution of Conditional Average Treatment Effects across population"
      isLoading={isLoading}
      error={error}
      onRefresh={onRefresh}
      metrics={metrics}
    >
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={histogramData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="binCenter"
            stroke="#94a3b8"
            tickFormatter={(value) => value.toFixed(2)}
            label={{
              value: 'CATE Value',
              position: 'insideBottom',
              offset: -10,
              style: { fill: '#94a3b8', fontSize: '14px' },
            }}
          />
          <YAxis
            stroke="#94a3b8"
            label={{
              value: 'Frequency (%)',
              angle: -90,
              position: 'insideLeft',
              style: { fill: '#94a3b8', fontSize: '14px' },
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="circle"
          />

          {/* ヒストグラムバー */}
          <Bar
            dataKey="frequency"
            fill="#3b82f6"
            fillOpacity={0.8}
            name="Frequency"
            radius={[4, 4, 0, 0]}
          />

          {/* 統計量の参照線 */}
          {statistics && (
            <>
              <ReferenceLine
                x={statistics.mean}
                stroke="#22c55e"
                strokeWidth={2}
                strokeDasharray="5 5"
                label={{
                  value: 'Mean',
                  position: 'top',
                  fill: '#22c55e',
                  fontSize: 12,
                }}
              />
              <ReferenceLine
                x={statistics.median}
                stroke="#f59e0b"
                strokeWidth={2}
                strokeDasharray="5 5"
                label={{
                  value: 'Median',
                  position: 'top',
                  fill: '#f59e0b',
                  fontSize: 12,
                }}
              />
              <ReferenceLine
                x={statistics.q1}
                stroke="#8b5cf6"
                strokeWidth={1}
                strokeDasharray="3 3"
                label={{
                  value: 'Q1',
                  position: 'top',
                  fill: '#8b5cf6',
                  fontSize: 11,
                }}
              />
              <ReferenceLine
                x={statistics.q3}
                stroke="#8b5cf6"
                strokeWidth={1}
                strokeDasharray="3 3"
                label={{
                  value: 'Q3',
                  position: 'top',
                  fill: '#8b5cf6',
                  fontSize: 11,
                }}
              />
            </>
          )}
        </BarChart>
      </ResponsiveContainer>

      {/* 追加の統計情報 */}
      {statistics && (
        <div
          style={{
            marginTop: '20px',
            padding: '16px',
            background: 'rgba(15, 23, 42, 0.6)',
            borderRadius: '8px',
            border: '1px solid #1e293b',
          }}
        >
          <h4 style={{ margin: '0 0 12px 0', color: '#f1f5f9', fontSize: '14px' }}>
            Distribution Statistics
          </h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '12px', fontSize: '13px', color: '#cbd5e1' }}>
            <div>
              <span style={{ color: '#94a3b8' }}>Min:</span>{' '}
              <span style={{ fontWeight: '600' }}>{statistics.min.toFixed(3)}</span>
            </div>
            <div>
              <span style={{ color: '#94a3b8' }}>Q1:</span>{' '}
              <span style={{ fontWeight: '600', color: '#8b5cf6' }}>{statistics.q1.toFixed(3)}</span>
            </div>
            <div>
              <span style={{ color: '#94a3b8' }}>Median:</span>{' '}
              <span style={{ fontWeight: '600', color: '#f59e0b' }}>{statistics.median.toFixed(3)}</span>
            </div>
            <div>
              <span style={{ color: '#94a3b8' }}>Q3:</span>{' '}
              <span style={{ fontWeight: '600', color: '#8b5cf6' }}>{statistics.q3.toFixed(3)}</span>
            </div>
            <div>
              <span style={{ color: '#94a3b8' }}>Max:</span>{' '}
              <span style={{ fontWeight: '600' }}>{statistics.max.toFixed(3)}</span>
            </div>
            <div>
              <span style={{ color: '#94a3b8' }}>Mean:</span>{' '}
              <span style={{ fontWeight: '600', color: '#22c55e' }}>{statistics.mean.toFixed(3)}</span>
            </div>
          </div>
        </div>
      )}
    </VisualizationCard>
  );
}
