/**
 * Decision Console v1
 *
 * Δ¥ランキング最優先のマーケティング意思決定ダッシュボード
 */
import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { decisionsApi } from '../api/v1/decisions';
import DecisionCard from '../components/v1/DecisionCard';
import DeltaYenMetricCard from '../components/v1/DeltaYenMetricCard';

const DecisionConsoleV1: React.FC = () => {
  const periodDays = 7;
  const [selectedVerdict, setSelectedVerdict] = useState<'Go' | 'Canary' | 'Hold' | undefined>(undefined);

  // Δ¥サマリー取得
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['delta-yen-summary', periodDays],
    queryFn: () => decisionsApi.getSummary(periodDays),
    refetchInterval: 30000 // 30秒ごとに更新
  });

  // DecisionCard一覧取得（Δ¥ランキング順）
  const { data: decisionsList, isLoading: decisionsLoading } = useQuery({
    queryKey: ['decisions-list', selectedVerdict],
    queryFn: () => decisionsApi.list({
      sort_by: 'delta_yen',
      order: 'desc',
      verdict: selectedVerdict,
      page: 1,
      page_size: 10
    }),
    refetchInterval: 30000
  });

  // Δ¥履歴取得
  const { data: history } = useQuery({
    queryKey: ['delta-yen-history'],
    queryFn: () => decisionsApi.getHistory({ period: 'week', weeks: 6 }),
    refetchInterval: 60000 // 1分ごと
  });

  // 判定内訳取得
  const { data: verdictDist } = useQuery({
    queryKey: ['verdict-distribution', periodDays],
    queryFn: () => decisionsApi.getVerdictDistribution(periodDays),
    refetchInterval: 30000
  });

  const formatYen = (amount: number) => {
    if (Math.abs(amount) >= 1_000_000) {
      return `¥${(amount / 1_000_000).toFixed(1)}M`;
    } else if (Math.abs(amount) >= 1_000) {
      return `¥${(amount / 1_000).toFixed(0)}K`;
    } else {
      return `¥${amount.toFixed(0)}`;
    }
  };

  // 円グラフ用データ
  const pieData = verdictDist ? [
    { name: 'Go', value: verdictDist.go, color: '#10b981' },
    { name: 'Canary', value: verdictDist.canary, color: '#f59e0b' },
    { name: 'Hold', value: verdictDist.hold, color: '#ef4444' }
  ] : [];

  if (summaryLoading || decisionsLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-gray-600">読み込み中...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Decision Console - マーケ施策意思決定</h1>
        <p className="text-gray-600 mt-2">Δ¥（デルタ円）と Go/Canary/Hold 判定を確認</p>
      </div>

      {/* メトリクスカード（4列） */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <DeltaYenMetricCard
          title="今週のベストシナリオ Δ¥"
          value={summary ? formatYen(summary.best_delta_yen) : '-'}
          subtitle={summary?.best_scenario ? summary.best_scenario.scenario_name : ''}
          icon="📈"
          color="green"
          onClick={() => setSelectedVerdict(undefined)}
        />
        <DeltaYenMetricCard
          title="リスク高シナリオ数"
          value={summary?.hold_count || 0}
          subtitle="Hold判定"
          icon="🔴"
          color="red"
          onClick={() => setSelectedVerdict('Hold')}
        />
        <DeltaYenMetricCard
          title="実行推奨キャンペーン"
          value={summary?.go_count || 0}
          subtitle={summary ? `期待収益 ${formatYen(summary.best_delta_yen * summary.go_count)}` : ''}
          icon="🟢"
          color="green"
          onClick={() => setSelectedVerdict('Go')}
        />
        <DeltaYenMetricCard
          title="A/Bテスト候補"
          value={summary?.canary_count || 0}
          subtitle="Canary判定"
          icon="🟡"
          color="yellow"
          onClick={() => setSelectedVerdict('Canary')}
        />
      </div>

      {/* メインコンテンツ（2列） */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左カラム（65%） - Decision Cards一覧 */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900">
                📊 Decision Cards（Δ¥ランキング順）
              </h2>
              {selectedVerdict && (
                <button
                  onClick={() => setSelectedVerdict(undefined)}
                  className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 text-sm"
                >
                  フィルタ解除
                </button>
              )}
            </div>

            {decisionsList && decisionsList.items.length > 0 ? (
              <div className="space-y-4">
                {decisionsList.items.map((card) => (
                  <DecisionCard
                    key={card.id}
                    card={card}
                    onClick={() => console.log('Click:', card.id)}
                  />
                ))}
                <div className="text-center pt-4">
                  <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                    全て表示（{decisionsList.total}件）
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-2">📭</div>
                <p>Decision Cardがありません</p>
              </div>
            )}
          </div>

          {/* クイックアクション */}
          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="font-semibold text-gray-900 mb-3">クイックアクション</h3>
            <div className="flex flex-wrap gap-2">
              <button className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
                + 新シナリオ作成
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                📊 週次レポート
              </button>
              <button className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700">
                📁 データアップロード
              </button>
            </div>
          </div>
        </div>

        {/* 右カラム（35%） - グラフ */}
        <div className="space-y-6">
          {/* Δ¥推移（週次） */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">📈 Δ¥推移（週次）</h3>
            {history && history.length > 0 ? (
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={history}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="week" />
                  <YAxis />
                  <Tooltip formatter={(value: number) => formatYen(value)} />
                  <Bar dataKey="delta_yen" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-gray-500 py-8">データなし</div>
            )}
          </div>

          {/* 判定内訳（円グラフ） */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">判定内訳（今週）</h3>
            {verdictDist && verdictDist.total > 0 ? (
              <>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">🟢 Go:</span>
                    <span className="font-semibold">{verdictDist.go}件</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">🟡 Canary:</span>
                    <span className="font-semibold">{verdictDist.canary}件</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">🔴 Hold:</span>
                    <span className="font-semibold">{verdictDist.hold}件</span>
                  </div>
                </div>
              </>
            ) : (
              <div className="text-center text-gray-500 py-8">データなし</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DecisionConsoleV1;
