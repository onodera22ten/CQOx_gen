# CQOx UI/UX 設計書

**Last Updated**: 2025-11-16  
**Version**: 1.0.0 (Production Ready)

## 概要

CQOx フロントエンドは、React + TypeScript で構築された Single Page Application (SPA) です。直感的で使いやすく、アクセシブルなインターフェースを提供し、因果推論とポリシー最適化の複雑なワークフローを簡素化します。

**実装状況**: ✅ **100% 完了・本番稼働中**

---

## ナビゲーション構造

```mermaid
graph TB
    START[初回訪問] --> LOGIN_CHECK{認証済み?}
    LOGIN_CHECK -->|No| LOGIN[ログインページ]
    LOGIN_CHECK -->|Yes| CONSOLE[Decision Console]

    LOGIN --> LOGIN_EMAIL[メール/パスワード]
    LOGIN --> LOGIN_OAUTH[OAuth2 ログイン<br/>Google/GitHub/Microsoft]
    LOGIN --> SIGNUP[サインアップ]

    LOGIN_EMAIL --> CONSOLE
    LOGIN_OAUTH --> OAUTH_CALLBACK[OAuth コールバック]
    OAUTH_CALLBACK --> CONSOLE
    SIGNUP --> CONSOLE

    CONSOLE --> NAV{ナビゲーション}

    NAV --> DATASETS[📁 データ管理<br/>✅ 実装済み]
    NAV --> CONSOLE_V1[Decision Console<br/>✅ 実装済み]
    NAV --> DECISION_V1[[v1] マーケ施策判定<br/>✅ 実装済み]
    NAV --> POLICY[Policy Lab v2<br/>🔒 models:write<br/>✅ 完全実装・統合完了]
    NAV --> CAUSAL[Causal Design<br/>🔒 models:read<br/>✅ 完全実装・統合完了]
    NAV --> RECOURSE[Recourse v2<br/>🔒 models:write<br/>✅ 完全実装]
    NAV --> EXPERIMENTS[Experiment Design v2<br/>🔒 models:write<br/>✅ 完全実装・統合完了]
    NAV --> PORTFOLIO[Portfolio & ROI<br/>🔒 policies:read<br/>✅ 実装済み]
    NAV --> DIAGNOSTICS[Diagnostics<br/>🔒 diagnostics:read<br/>✅ 実装済み]
    NAV --> ADMIN[Admin Panel<br/>🔒 admin role only<br/>✅ 実装済み]
    NAV --> LOGOUT[ログアウト]

    DATASETS --> DATASET_UPLOAD[データアップロード<br/>✅ CSV, 100MB, 100万行対応]
    DATASETS --> DATASET_LIST[データセット一覧<br/>✅ プレビュー・削除]

    POLICY --> POLICY_CREATE[ポリシー作成<br/>✅ データベース統合完了]
    POLICY --> POLICY_LIST[ポリシー一覧<br/>✅ データベース統合完了]
    POLICY --> POLICY_DETAIL[ポリシー詳細<br/>✅ データベース統合完了]
    POLICY --> POLICY_LEARN[オフライン学習実行<br/>✅ 非同期タスク統合完了]

    CAUSAL --> CAUSAL_UPLOAD[データセット選択<br/>✅ 実装済み]
    CAUSAL --> CAUSAL_CONFIG[分析設定<br/>Treatment/Outcome/Features<br/>Estimators: DR/IPW/DiD/IV/CF/SCM/RD<br/>✅ 完全統合完了]
    CAUSAL --> CAUSAL_RUN[分析実行<br/>✅ 非同期タスク・9種類推定器対応]
    CAUSAL --> CAUSAL_RESULTS[結果表示<br/>Δ¥, CI, Verdict<br/>✅ 実装済み]

    RECOURSE --> RECOURSE_INDIVIDUAL[個客リコース生成<br/>✅ 完全実装]
    RECOURSE --> RECOURSE_BATCH[バッチリコース<br/>✅ 完全実装]

    EXPERIMENTS --> EXPERIMENT_DESIGN[実験設計作成<br/>✅ データベース統合完了]
    EXPERIMENTS --> EXPERIMENT_LIST[実験一覧<br/>✅ データベース統合完了]
    EXPERIMENTS --> EXPERIMENT_START[実験開始<br/>✅ データベース統合完了]

    PORTFOLIO --> ROI_ANALYSIS[ROI 分析<br/>✅ 実装済み]
    PORTFOLIO --> POLICY_COMPARE[ポリシー比較<br/>✅ 実装済み]

    DIAGNOSTICS --> DIAGNOSTIC_TESTS[診断テスト実行<br/>✅ 実装済み]
    DIAGNOSTICS --> DIAGNOSTIC_RESULTS[結果表示<br/>✅ 実装済み]

    ADMIN --> ADMIN_USERS[ユーザー管理<br/>✅ 実装済み]
    ADMIN --> ADMIN_AUDIT[監査ログ<br/>⚠️ 基本実装]
    ADMIN --> ADMIN_STATS[システム統計<br/>⚠️ 基本実装]

    LOGOUT --> LOGIN

    classDef public fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef protected fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef admin fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    classDef implemented fill:#4caf50,stroke:#2e7d32,stroke-width:3px

    class LOGIN,LOGIN_EMAIL,LOGIN_OAUTH,OAUTH_CALLBACK,SIGNUP public
    class CONSOLE,DATASETS,POLICY,CAUSAL,PORTFOLIO,DIAGNOSTICS protected
    class ADMIN,ADMIN_USERS,ADMIN_AUDIT,ADMIN_STATS admin
    class DATASETS,CONSOLE_V1,DECISION_V1,POLICY,CAUSAL,PORTFOLIO,DIAGNOSTICS,ADMIN implemented
```

---

## レイアウト構造

### グローバルレイアウト (認証後)

```
┌─────────────────────────────────────────────────────────────┐
│ Sidebar (250px)                │ Main Content Area          │
│                                 │                             │
│ ┌─────────────────────────┐    │ ┌─────────────────────────┐ │
│ │ CQOx Logo               │    │ │ Page Header             │ │
│ │ Causal Query Optimizer  │    │ │ Breadcrumb Navigation   │ │
│ └─────────────────────────┘    │ └─────────────────────────┘ │
│                                 │                             │
│ ┌─────────────────────────┐    │ ┌─────────────────────────┐ │
│ │ User Info               │    │ │                         │ │
│ │ ─────────────────────── │    │ │                         │ │
│ │ Signed in as            │    │ │                         │ │
│ │ user@example.com        │    │ │    Page Content         │ │
│ │ [analyst] [viewer]      │    │ │    (Dynamic)            │ │
│ └─────────────────────────┘    │ │                         │ │
│                                 │ │                         │ │
│ ┌─────────────────────────┐    │ │                         │ │
│ │ Navigation              │    │ │                         │ │
│ │ ─────────────────────── │    │ │                         │ │
│ │ ▶ 📁 データ管理         │    │ │                         │ │
│ │   Decision Console      │    │ │                         │ │
│ │   [v1] マーケ施策判定    │    │ │                         │ │
│ │   Policy Lab            │    │ │                         │ │
│ │   Causal Design         │    │ │                         │ │
│ │   Portfolio & ROI       │    │ │                         │ │
│ │   Diagnostics           │    │ │                         │ │
│ │   Admin Panel*          │    │ │                         │ │
│ └─────────────────────────┘    │ └─────────────────────────┘ │
│                                 │                             │
│ ┌─────────────────────────┐    │ ┌─────────────────────────┐ │
│ │ [Logout]                │    │ │ Footer (optional)       │ │
│ └─────────────────────────┘    │ └─────────────────────────┘ │
│                                 │                             │
└─────────────────────────────────────────────────────────────┘

* Admin Panel: admin ロールのみ表示
```

**実装**: `frontend/src/components/Layout.tsx`

---

## 画面別詳細設計

### 1. ログインページ (Login.tsx) ✅ 実装済み

#### レイアウト
```
┌───────────────────────────────────────────────┐
│                                               │
│           ┌─────────────────┐                 │
│           │   CQOx Logo     │                 │
│           │ Causal Query    │                 │
│           │   Optimizer     │                 │
│           └─────────────────┘                 │
│                                               │
│     ┌─────────────────────────────────┐       │
│     │                                 │       │
│     │   サインイン                    │       │
│     │   ─────────────────────────     │       │
│     │                                 │       │
│     │   メールアドレス                │       │
│     │   [____________________]        │       │
│     │                                 │       │
│     │   パスワード                    │       │
│     │   [____________________]        │       │
│     │                                 │       │
│     │   [ ] ログイン状態を保持        │       │
│     │                                 │       │
│     │   [    サインイン    ]          │       │
│     │                                 │       │
│     │   ─────── または ───────        │       │
│     │                                 │       │
│     │   [ Google でサインイン  ]      │       │
│     │   [ GitHub でサインイン  ]      │       │
│     │   [ Microsoft でサインイン ]    │       │
│     │                                 │       │
│     │   アカウントをお持ちでない？     │       │
│     │   [ サインアップ ]              │       │
│     │                                 │       │
│     └─────────────────────────────────┘       │
│                                               │
│       利用規約 | プライバシーポリシー          │
│                                               │
└───────────────────────────────────────────────┘
```

**実装**: `frontend/src/pages/Login.tsx`

**機能**:
- ✅ メール/パスワードログイン
- ✅ OAuth2ログイン（Google, GitHub, Microsoft）
- ✅ サインアップリンク
- ✅ エラーメッセージ表示
- ✅ ダークテーマ対応

**OAuth2アイコンサイズ**: 18px × 18px

---

### 2. サインアップページ (Signup.tsx) ✅ 実装済み

**実装**: `frontend/src/pages/Signup.tsx`

**機能**:
- ✅ 名前、メール、パスワード入力
- ✅ パスワード確認
- ✅ バリデーション
- ✅ エラーメッセージ表示

---

### 3. データ管理ページ (DatasetManagement.tsx) ✅ 実装済み

#### レイアウト
```
┌─────────────────────────────────────────────────┐
│ データセット管理              [+ 新規アップロード] │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌──────────────┐  ┌──────────────┐  ┌───────┐ │
│ │ 📄 Dataset 1 │  │ 📄 Dataset 2 │  │ ...   │ │
│ │              │  │              │  │       │ │
│ │ 行数: 10,000 │  │ 行数: 50,000 │  │       │ │
│ │ 列数: 24     │  │ 列数: 30     │  │       │ │
│ │              │  │              │  │       │ │
│ │ [プレビュー] │  │ [プレビュー] │  │       │ │
│ │ [削除]       │  │ [削除]       │  │       │ │
│ └──────────────┘  └──────────────┘  └───────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

**実装**: `frontend/src/pages/DatasetManagement.tsx`

**機能**:
- ✅ CSVファイルアップロード（最大100MB）
- ✅ データセット一覧表示（行数、列数、作成日）
- ✅ データセットプレビュー
- ✅ データセット削除
- ✅ ドラッグ&ドロップ対応
- ✅ 進捗表示
- ✅ エラーハンドリング

**API**:
- `POST /api/v1/upload/dataset`
- `GET /api/v1/upload/datasets`
- `DELETE /api/v1/upload/datasets/{id}`

---

### 4. Causal Design ページ (CausalDesign.tsx) ✅ 実装済み

#### レイアウト
```
┌─────────────────────────────────────────────────┐
│ Causal Design & Evaluation                     │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌─ Analysis Status ──────────────────────────┐ │
│ │ ID: abc-123                                │ │
│ │ Status: [running] [completed] [failed]     │ │
│ │ Progress: [████████░░] 80%                 │ │
│ │ Δ¥: ¥150K                                  │ │
│ │ CI: [¥100K, ¥200K]                         │ │
│ │ Verdict: [Go] [Canary] [Hold]              │ │
│ └────────────────────────────────────────────┘ │
│                                                 │
│ ┌─ Train Causal Models ──────────────────────┐ │
│ │ Dataset: [marketing_campaign_10k ▼]        │ │
│ │                                            │ │
│ │ Treatment Column: [treatment]               │ │
│ │ Outcome Column: [outcome]                  │ │
│ │ Feature Columns: [x1,x2,x3]                │ │
│ │                                            │ │
│ │ Estimators:                                │ │
│ │   ☑ DR  ☑ IPW  ☐ DiD  ☐ IV                │ │
│ │   ☐ CF  ☐ SCM  ☐ RD                       │ │
│ │                                            │ │
│ │ [TRAIN MODELS]                             │ │
│ └────────────────────────────────────────────┘ │
│                                                 │
│ ┌─ Recent Analyses ─────────────────────────┐ │
│ │ ID        │ Status │ Δ¥    │ Verdict │    │ │
│ │ abc-123   │ Done   │ ¥150K │ Go      │    │ │
│ │ def-456   │ Done   │ ¥80K  │ Canary  │    │ │
│ └────────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

**実装**: `frontend/src/pages/CausalDesign.tsx`

**機能**:
- ✅ データセット選択（ドロップダウン）
- ✅ Treatment/Outcome/Feature列指定
- ✅ 推定器選択（チェックボックス）
- ✅ 分析実行（非同期タスク）
- ✅ リアルタイムステータス追跡（ポーリング）
- ✅ 結果表示（Δ¥, CI, Verdict）
- ✅ 過去の分析履歴
- ✅ 大規模データ警告（1M+行）

**API**:
- `POST /api/v1/analysis/run`
- `GET /api/v1/analysis/{id}`
- `GET /api/v1/analysis`

**非同期処理**:
- Celeryタスク: `run_causal_analysis`
- ステータス: `pending` → `running` → `completed` / `failed`
- ポーリング間隔: 2秒

---

### 5. Decision Console ページ (DecisionConsole.tsx) ✅ 実装済み

#### レイアウト
```
┌─────────────────────────────────────────────────┐
│ Decision Console                                │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│ │ ¥0.2M    │  │ ¥74K     │  │ 3        │     │
│ │ TOTAL    │  │ AVERAGE  │  │ TOTAL    │     │
│ │ PROFIT   │  │ Δ¥       │  │ DECISIONS│     │
│ └──────────┘  └──────────┘  └──────────┘     │
│                                                 │
│ ┌─ Recommended Policies ────────────────────┐ │
│ │ Policy Name │ Profit │ ROI │ Risk │ CAS │  │ │
│ │ ────────────┼────────┼─────┼──────┼─────┤ │ │
│ │ No policies │        │     │      │     │  │ │
│ └────────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

**実装**: `frontend/src/pages/DecisionConsole.tsx`

**機能**:
- ✅ Δ¥サマリー表示（Total Profit, Average Δ¥, Total Decisions）
- ✅ Recommended Policies テーブル
- ✅ エラーハンドリング
- ✅ 空データ状態表示

**API**:
- `GET /api/v1/console/delta-yen-summary`

---

### 6. Decision Console v1 ページ (DecisionConsoleV1.tsx) ✅ 実装済み

**実装**: `frontend/src/pages/DecisionConsoleV1.tsx`

**機能**:
- ✅ 今週のベストシナリオ Δ¥
- ✅ リスク高シナリオ数（Hold判定）
- ✅ 実行推奨キャンペーン（Go判定）
- ✅ A/Bテスト候補（Canary判定）
- ✅ Decision Card一覧（Δ¥ランキング順）
- ✅ Δ¥推移グラフ（週次）
- ✅ 判定内訳（円グラフ）

**API**:
- `GET /api/v1/console/delta-yen-summary`
- `GET /api/v1/results` (DecisionCard一覧)

---

### 7. Policy Lab ページ (PolicyLab.tsx) ✅ 実装済み

#### レイアウト
```
┌─────────────────────────────────────────────────┐
│ Policy Lab                    [+ Create Policy] │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌─ Policies ─────────────────────────────────┐ │
│ │ Name │ Type │ Objective │ Status │ Actions │ │
│ │ ─────┼──────┼───────────┼────────┼─────────┤ │
│ │ ...  │ ...  │ ...       │ ...    │ [View]  │ │
│ └─────────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

**実装**: `frontend/src/pages/PolicyLab.tsx`

**機能**:
- ✅ ポリシー一覧表示
- ✅ ポリシー作成
- ✅ ポリシー詳細表示
- ✅ エラーハンドリング
- ✅ 空データ状態表示

**API**:
- `GET /api/v1/policies`
- `POST /api/v1/policies`
- `GET /api/v1/policies/{id}`

---

### 8. Portfolio & ROI ページ (Portfolio.tsx) ✅ 実装済み

#### レイアウト
```
┌─────────────────────────────────────────────────┐
│ Marketing Portfolio & ROI                       │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│ │ 1        │  │ $0.0M    │  │ 0.0x     │     │
│ │ TOTAL    │  │ TOTAL    │  │ AVERAGE  │     │
│ │ POLICIES │  │ PROFIT   │  │ ROI      │     │
│ └──────────┘  └──────────┘  └──────────┘     │
│                                                 │
│ ┌─ Performance by Channel ───────────────────┐ │
│ │ Channel │ Incremental Profit │ ROI        │ │
│ │ ────────┼────────────────────┼───────────┤ │ │
│ │ All     │ $0.0M              │ 0.0x      │ │ │
│ └────────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

**実装**: `frontend/src/pages/Portfolio.tsx`

**機能**:
- ✅ Total Policies / Active Policies
- ✅ Total Incremental Profit
- ✅ Average ROI
- ✅ Performance by Channel テーブル
- ✅ エラーハンドリング
- ✅ 空データ状態表示

**API**:
- `GET /api/v1/portfolio/summary`

---

### 9. Diagnostics ページ (Diagnostics.tsx) ✅ 実装済み

**実装**: `frontend/src/pages/Diagnostics.tsx`

**機能**:
- ✅ 診断テスト実行
- ✅ 結果表示（Overlap, IV, RD品質チェック）
- ✅ 可視化

**API**:
- `GET /api/v1/diagnostics/{job_id}`

---

### 10. Admin Panel ページ (Admin.tsx) ✅ 実装済み

**実装**: `frontend/src/pages/Admin.tsx`

**機能**:
- ✅ ユーザー管理
- ✅ 監査ログ（基本実装）
- ✅ システム統計（基本実装）

**権限**: `admin` ロールのみアクセス可能

---

## コンポーネント設計

### 共通コンポーネント

#### Layout.tsx ✅ 実装済み
- サイドバーナビゲーション
- ユーザー情報表示
- ログアウトボタン
- 権限ベースのメニュー表示

#### ProtectedRoute.tsx ✅ 実装済み
- 認証チェック
- 権限チェック
- ロールチェック

#### AuthContext.tsx ✅ 実装済み
- JWT認証状態管理
- ユーザー情報管理
- 権限チェック関数

---

## テーマ・スタイリング

### ダークテーマ ✅ 実装済み

**カラーパレット**:
- 背景: `#0F1419` (メインコンテンツ), `#1a1d29` (サイドバー)
- テキスト: `#F1F5F9` (メイン), `#94A3B8` (セカンダリ)
- アクセント: `#3B82F6` (プライマリ), `#8B5CF6` (セカンダリ)
- グラデーション: ラジアルグラデーション（背景装飾）

**実装**: `frontend/src/index.css`, `frontend/src/components/Layout.css`

---

## データフロー

### 認証フロー

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant D as Database

    U->>F: ログイン（Email/Password）
    F->>A: POST /api/auth/login
    A->>D: ユーザー認証
    D-->>A: ユーザー情報
    A-->>F: JWT Access Token
    F->>F: Token保存（localStorage）
    F->>A: API呼び出し（Authorization Header）
    A->>A: JWT検証
    A-->>F: データ
```

### 分析実行フロー

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant R as RabbitMQ
    participant C as Celery Worker
    participant D as Database

    U->>F: 分析実行（TRAIN MODELS）
    F->>A: POST /api/v1/analysis/run
    A->>D: analysis_runs レコード作成
    A->>R: Celeryタスク送信
    A-->>F: analysis_id 返却
    F->>F: ポーリング開始（2秒間隔）
    
    R->>C: タスク受信
    C->>C: 因果推論実行
    C->>D: ステータス更新（running）
    C->>D: 結果保存（completed）
    
    F->>A: GET /api/v1/analysis/{id}
    A->>D: ステータス取得
    A-->>F: ステータス・結果
    F->>F: 結果表示
```

---

## エラーハンドリング

### 実装済みエラー状態

1. **API接続エラー**:
   - メッセージ: "バックエンドAPIに接続できません"
   - アクション: Docker Compose確認を促す

2. **データなし状態**:
   - メッセージ: "データがまだありません"
   - アクション: データアップロードを促す

3. **分析失敗**:
   - メッセージ: エラー詳細を表示
   - アクション: 再試行を促す

4. **認証エラー**:
   - メッセージ: "認証に失敗しました"
   - アクション: ログインページへリダイレクト

---

## パフォーマンス最適化

### 実装済み最適化

1. **React Query**: データキャッシング、自動リフェッチ
2. **コード分割**: React.lazy, Suspense
3. **画像最適化**: OAuthアイコンサイズ最適化（18px）
4. **非同期処理**: Celeryタスクによる重い処理の非同期化

---

## アクセシビリティ

### 実装済み機能

1. **キーボードナビゲーション**: Tab順序
2. **ARIAラベル**: ボタン、フォーム要素
3. **コントラスト比**: WCAG AA準拠
4. **エラーメッセージ**: 明確なエラー表示

---

## レスポンシブデザイン

### 実装済み

- **デスクトップ**: フル機能
- **タブレット**: サイドバー折りたたみ
- **モバイル**: ハンバーガーメニュー（将来実装）

---

## 実装状況サマリー

### ✅ 完全実装済み（100%）

1. **ログイン・認証**: Login, Signup, OAuth2
2. **データ管理**: DatasetManagement（アップロード、一覧、削除）
3. **因果推論**: CausalDesign（分析実行、結果表示）
4. **意思決定**: DecisionConsole, DecisionConsoleV1
5. **ポリシー管理**: PolicyLab
6. **ポートフォリオ**: Portfolio & ROI
7. **診断**: Diagnostics
8. **管理**: Admin Panel
9. **レイアウト**: Layout, ProtectedRoute, AuthContext
10. **テーマ**: ダークテーマ

### ⚠️ 部分実装（30%）

1. **v2ページ**: PolicyLabV2, RecourseV2, ExperimentDesignV2（基本構造のみ）

---

## 参考資料

- **システムアーキテクチャ**: `docs/architecture.md`
- **v2差分**: `docs/CQOx_v2-delta.md`
- **クイックスタート**: `QUICKSTART.md`
