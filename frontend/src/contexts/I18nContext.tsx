/**
 * 【日本語サマリ】このモジュールは多言語対応（i18n）を実現し、EN/JA切替を提供する。
 * - なぜ必要か: Google/Meta/NASA/WPP/BCG級のグローバルUX要件に対応
 * - 何をするか: Context APIでアプリ全体の言語状態を管理、翻訳辞書を提供
 * - どう検証するか: 言語切替ボタンで即座にUI文言が変わることを確認
 */

import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react'

type Language = 'en' | 'ja'

interface I18nContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: string) => string
}

const I18nContext = createContext<I18nContextType | undefined>(undefined)

// Translation dictionary
const translations: Record<Language, Record<string, string>> = {
  en: {
    // Navigation
    'nav.console': 'Decision Console',
    'nav.policy': 'Policy Lab',
    'nav.causal': 'Causal Design',
    'nav.portfolio': 'Portfolio',
    'nav.diagnostics': 'Diagnostics',
    'nav.datasets': 'Datasets',
    'nav.digital_twin': 'Digital Twin',
    'nav.experiment': 'Experiment Design',
    'nav.experiment_studio': 'Experiment Studio',
    'nav.growth_studio': 'Growth Studio',
    'nav.governance': 'Governance Center',
    'nav.recourse': 'Recourse',
    'nav.export': 'Export Gate',
    'nav.admin': 'Admin',
    
    // Decision Console
    'console.title': 'Decision Console - Marketing Decisions',
    'console.subtitle': 'Check Δ¥ (Delta Yen) and Go/Canary/Hold verdicts',
    'console.total_profit': 'TOTAL INCREMENTAL PROFIT',
    'console.avg_delta': 'AVERAGE Δ¥',
    'console.total_decisions': 'TOTAL DECISIONS',
    'console.no_data': 'No data available yet',
    'console.upload_prompt': 'Upload a dataset and run causal inference in Causal Design.',
    'console.delta_trend': 'Δ¥ Trend (Weekly)',
    'console.verdict_breakdown': 'Verdict Breakdown (This Week)',
    'console.recent_analyses': 'Recent Analyses',
    
    // Portfolio
    'portfolio.title': 'Marketing Portfolio & ROI',
    'portfolio.overview': 'Overview',
    'portfolio.frontier': 'Pareto Frontier',
    'portfolio.total_policies': 'Total Policies',
    'portfolio.total_profit': 'Total Incremental Profit',
    'portfolio.avg_roi': 'Average ROI',
    'portfolio.by_channel': 'Performance by Channel',
    'portfolio.no_data': 'No Policy Data Available',
    'portfolio.no_data_desc': 'Run completed analyses in Causal Design to see your portfolio recommendations here.',
    'portfolio.recommended_strategy': 'Recommended Portfolio Strategy',
    'policyLab.title': 'Policy Lab',
    'policyLab.subtitle': 'Design, evaluate, and simulate marketing policies',
    'policyLab.create': 'Create Policy',
    'policyLab.custom.description': 'Build SQL-based scenarios, configure channels, budgets, and evaluation metrics.',
    'digitalTwin.title': 'Digital Twin Reference',
    'digitalTwin.description': 'View the latest Digital Twin specification (twin.pdf) for implementation details.',
    
    // Causal Design
    'causal.title': 'Causal Design',
    'causal.subtitle': 'Run causal inference analysis',
    'causal.select_dataset': 'Select Dataset',
    'causal.treatment_col': 'Treatment Column',
    'causal.outcome_col': 'Outcome Column',
    'causal.feature_cols': 'Feature Columns',
    'causal.estimators': 'Estimators',
    'causal.run_analysis': 'Run Analysis',
    'causal.view_diagnostics': 'View Diagnostics',
    
    // Common
    'common.loading': 'Loading...',
    'common.error': 'Error',
    'common.save': 'Save',
    'common.cancel': 'Cancel',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.view': 'View',
    'common.close': 'Close',
    'common.submit': 'Submit',
    'common.search': 'Search',
    'common.filter': 'Filter',
    'common.export': 'Export',
    'common.import': 'Import',
    'common.back': 'Back',
    'common.next': 'Next',
    'common.previous': 'Previous',
    'common.confirm': 'Confirm',
    'common.language': 'Language',
    'common.download': 'Download',
    'common.pdf_missing': 'twin.pdf is not accessible. Confirm the file exists in the repository root.',
    
    // Verdicts
    'verdict.go': 'Go',
    'verdict.canary': 'Canary',
    'verdict.hold': 'Hold',
  },
  ja: {
    // Navigation
    'nav.console': '意思決定コンソール',
    'nav.policy': 'ポリシーラボ',
    'nav.causal': '因果推論デザイン',
    'nav.portfolio': 'ポートフォリオ',
    'nav.diagnostics': '診断',
    'nav.datasets': 'データセット',
    'nav.digital_twin': 'デジタルツイン',
    'nav.experiment': '実験デザイン',
    'nav.experiment_studio': 'エクスペリメントスタジオ',
    'nav.growth_studio': 'Growth Studio',
    'nav.governance': 'ガバナンスセンター',
    'nav.recourse': 'リコース',
    'nav.export': 'エクスポートゲート',
    'nav.admin': '管理',
    
    // Decision Console
    'console.title': 'Decision Console - マーケ施策意思決定',
    'console.subtitle': 'Δ¥（デルタ円）と Go/Canary/Hold 判定を確認',
    'console.total_profit': '総増分利益',
    'console.avg_delta': '平均Δ¥',
    'console.total_decisions': '総決定数',
    'console.no_data': 'データがまだありません',
    'console.upload_prompt': 'Causal Design ページでデータセットをアップロードし、因果推論を実行してください。',
    'console.delta_trend': 'Δ¥推移（週次）',
    'console.verdict_breakdown': '判定内訳（今週）',
    'console.recent_analyses': '最近の分析',
    
    // Portfolio
    'portfolio.title': 'マーケティングポートフォリオ & ROI',
    'portfolio.overview': '概要',
    'portfolio.frontier': 'パレートフロンティア',
    'portfolio.total_policies': '総ポリシー数',
    'portfolio.total_profit': '総増分利益',
    'portfolio.avg_roi': '平均ROI',
    'portfolio.by_channel': 'チャネル別パフォーマンス',
    'portfolio.no_data': 'ポリシーデータがありません',
    'portfolio.no_data_desc': 'Causal Designで完了した分析を実行すると、ここにポートフォリオ推奨が表示されます。',
    'portfolio.recommended_strategy': '推奨ポートフォリオ戦略',
    'policyLab.title': 'ポリシーラボ',
    'policyLab.subtitle': 'マーケ施策を設計・評価・シミュレーション',
    'policyLab.create': 'ポリシー作成',
    'policyLab.custom.description': 'SQLベースのターゲット条件、チャネル、予算、評価指標を一括で設定できます。',
    'digitalTwin.title': 'Digital Twin ドキュメント',
    'digitalTwin.description': 'twin.pdf に基づく最新の仕様書を参照できます。',
    
    // Causal Design
    'causal.title': '因果推論デザイン',
    'causal.subtitle': '因果推論分析を実行',
    'causal.select_dataset': 'データセット選択',
    'causal.treatment_col': '処置列',
    'causal.outcome_col': '結果列',
    'causal.feature_cols': '特徴列',
    'causal.estimators': '推定量',
    'causal.run_analysis': '分析実行',
    'causal.view_diagnostics': '診断を表示',
    
    // Common
    'common.loading': '読み込み中...',
    'common.error': 'エラー',
    'common.save': '保存',
    'common.cancel': 'キャンセル',
    'common.delete': '削除',
    'common.edit': '編集',
    'common.view': '表示',
    'common.close': '閉じる',
    'common.submit': '送信',
    'common.search': '検索',
    'common.filter': 'フィルタ',
    'common.export': 'エクスポート',
    'common.import': 'インポート',
    'common.back': '戻る',
    'common.next': '次へ',
    'common.previous': '前へ',
    'common.confirm': '確認',
    'common.language': '言語',
    'common.download': 'ダウンロード',
    'common.pdf_missing': 'twin.pdf にアクセスできません。リポジトリ直下にファイルが存在するか確認してください。',
    
    // Verdicts
    'verdict.go': '実行',
    'verdict.canary': 'カナリア',
    'verdict.hold': '保留',
  },
}

export const I18nProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Load language from localStorage, default to 'ja' (Japanese)
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('cqox_language')
    return (saved === 'en' || saved === 'ja') ? saved : 'ja'
  })

  // Save language to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('cqox_language', language)
  }, [language])

  const setLanguage = (lang: Language) => {
    setLanguageState(lang)
  }

  const t = (key: string): string => {
    return translations[language][key] || key
  }

  const value: I18nContextType = {
    language,
    setLanguage,
    t,
  }

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>
}

export const useI18n = () => {
  const context = useContext(I18nContext)
  if (context === undefined) {
    throw new Error('useI18n must be used within an I18nProvider')
  }
  return context
}
