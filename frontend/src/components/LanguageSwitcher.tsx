/**
 * Language Switcher Component
 * EN/JA切替ボタン - 全ページ共通ヘッダーに配置
 */

import React from 'react'
import { useI18n } from '../contexts/I18nContext'

export const LanguageSwitcher: React.FC = () => {
  const { language, setLanguage } = useI18n()

  return (
    <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
      <button
        onClick={() => setLanguage('en')}
        style={{
          padding: '6px 12px',
          background: language === 'en' 
            ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' 
            : 'rgba(51, 65, 85, 0.5)',
          border: 'none',
          borderRadius: '6px',
          color: '#fff',
          fontSize: '13px',
          fontWeight: language === 'en' ? '600' : '400',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          opacity: language === 'en' ? 1 : 0.7,
        }}
        title="Switch to English"
      >
        EN
      </button>
      <button
        onClick={() => setLanguage('ja')}
        style={{
          padding: '6px 12px',
          background: language === 'ja' 
            ? 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' 
            : 'rgba(51, 65, 85, 0.5)',
          border: 'none',
          borderRadius: '6px',
          color: '#fff',
          fontSize: '13px',
          fontWeight: language === 'ja' ? '600' : '400',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
          opacity: language === 'ja' ? 1 : 0.7,
        }}
        title="日本語に切り替え"
      >
        日本語
      </button>
    </div>
  )
}

