# CQOx v2 差分仕様書

## 概要

**本文書はCQOx v1からの差分仕様です。** v1の完全仕様については別途参照してください。

### v1との境界

**v1のスコープ（評価レイヤまで）**
- Data Contract + Great Expectations による厳格なデータ品質管理
- 多数の推定器（DML, Causal Forest, Metalearners等）による因果推定
- シナリオDSL + Money-View (Δ¥) による因果評価
- Diagnostics（Refutation, Sensitivity, Heterogeneity）による品質ゲート
- DecisionCard による集計レベルの結果表示

**v2で追加する内容（学習・計画レイヤ）**
- **Policy Lab**: 既存ログからのオフライン policy 学習
- **Recourse**: 個客レベルの反事実的介入提案（Counterfactual Recourse）
- **Experiment Design**: 施策前の実験設計と検出力計算

### 差別化コア

他社（Haus, Incremental, Sellforte等）との差別化は以下：

1. **Offline Policy Learning**: 既存ログから最適 policy を自動学習（uplift + risk のfrontier最適化）
2. **個客レベル Policy & Recourse**: 集計だけでなく、1顧客単位での介入提案
3. **施策前 Planning**: 事後評価ではなく、事前の安全な意思決定支援

---

## v2 新ドメインオブジェクト

### 1. PolicyConfig

**定義**
```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class PolicyConfig(BaseModel):
    """Policy設定（治療割当ルール）"""
    id: str = Field(..., description="Policy ID")
    name: str
    description: Optional[str] = None

    # Policy definition
    policy_type: str = Field(..., description="'threshold', 'multi_arm', 'custom'")
    treatment_variable: str  # e.g., 'marketing_spend'
    outcome_variable: str   # e.g., 'revenue'

    # Threshold policy: treat if score > threshold
    threshold: Optional[float] = Field(None, description="Uplift scoreの閾値")

    # Multi-arm policy: segment → treatment mapping
    segments: Optional[Dict[str, str]] = Field(None, description="Segment名 → Treatment値")

    # Custom policy: Python expression or decision tree
    custom_rule: Optional[str] = None

    # Constraints
    budget_constraint: Optional[float] = None  # 総予算制約（円）
    coverage_constraint: Optional[float] = Field(None, ge=0, le=1)  # 治療を受ける割合

    # Metadata
    created_at: str
    created_by: str  # user_id
    dataset_id: str
    model_id: str  # 使用する uplift model

    class Config:
        json_schema_extra = {
            "example": {
                "id": "policy-abc123",
                "name": "High-Value Customer Marketing",
                "policy_type": "threshold",
                "treatment_variable": "marketing_spend",
                "outcome_variable": "revenue",
                "threshold": 0.3,  # uplift > 0.3 なら treat
                "budget_constraint": 10000000,  # 1000万円
                "coverage_constraint": 0.2,  # 上位20%
                "dataset_id": "dataset-xyz",
                "model_id": "model-456"
            }
        }
```

### 2. OfflinePolicyRun

**定義**
```python
class OfflinePolicyRun(BaseModel):
    """オフライン policy 学習の実行結果"""
    id: str
    policy_config_id: str
    dataset_id: str

    # Learning settings
    objective: str = Field(..., description="'uplift', 'delta_revenue', 'roi'")
    risk_metric: str = Field(..., description="'std', 'var', 'cvar'")
    ope_method: str = Field(..., description="'DR', 'IPW', 'DM'")  # Off-Policy Evaluation

    # Search space
    threshold_grid: List[float] = Field(default=[0.1, 0.2, 0.3, 0.4, 0.5])
    coverage_grid: List[float] = Field(default=[0.1, 0.2, 0.3, 0.5])

    # Results
    status: str  # 'running', 'completed', 'failed'
    frontier: Optional[List[Dict]] = None  # Pareto frontier points
    best_policy: Optional[PolicyConfig] = None
    ope_metrics: Optional[Dict] = None  # OPE推定値

    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "run-789",
                "policy_config_id": "policy-abc123",
                "objective": "delta_revenue",
                "risk_metric": "std",
                "ope_method": "DR",
                "frontier": [
                    {"threshold": 0.1, "expected_revenue": 5000000, "risk": 200000},
                    {"threshold": 0.3, "expected_revenue": 4500000, "risk": 100000},
                    {"threshold": 0.5, "expected_revenue": 3000000, "risk": 50000}
                ],
                "best_policy": {
                    "threshold": 0.3,
                    "expected_revenue": 4500000,
                    "coverage": 0.35
                }
            }
        }
```

### 3. RecoursePlan

**定義**
```python
class RecourseCandidate(BaseModel):
    """1つの介入候補"""
    intervention: Dict[str, float]  # {"marketing_spend": 5000, "discount": 0.1}
    predicted_outcome: float  # 介入後の予測結果
    cost: float  # 介入コスト
    feasibility_score: float  # 実現可能性 [0, 1]
    explanation: str  # なぜこの介入が推奨されるか

class RecoursePlan(BaseModel):
    """個客レベルの反事実的介入計画"""
    id: str
    unit_id: str  # customer_id etc.
    policy_id: str
    model_id: str

    # Current state
    current_features: Dict[str, float]
    current_predicted_outcome: float

    # Target
    target_outcome: float  # 望ましい結果
    target_outcome_type: str  # 'conversion', 'revenue', 'retention'

    # Recourse candidates (Top-K)
    candidates: List[RecourseCandidate] = Field(..., max_length=10)

    # Constraints
    actionable_features: List[str]  # 変更可能な特徴
    max_cost: Optional[float] = None

    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "recourse-001",
                "unit_id": "customer-12345",
                "policy_id": "policy-abc123",
                "current_features": {
                    "age": 35,
                    "income": 50000,
                    "marketing_spend": 0
                },
                "current_predicted_outcome": 0.1,
                "target_outcome": 0.8,
                "target_outcome_type": "conversion",
                "candidates": [
                    {
                        "intervention": {"marketing_spend": 3000, "discount": 0.05},
                        "predicted_outcome": 0.75,
                        "cost": 3150,
                        "feasibility_score": 0.9,
                        "explanation": "適度なマーケ投資と小割引で高確率転換"
                    },
                    {
                        "intervention": {"marketing_spend": 5000},
                        "predicted_outcome": 0.85,
                        "cost": 5000,
                        "feasibility_score": 0.7,
                        "explanation": "高額投資で最大効果、ただしコスト高"
                    }
                ],
                "actionable_features": ["marketing_spend", "discount", "channel"]
            }
        }
```

### 4. ExperimentPlan

**定義**
```python
class ExperimentPlan(BaseModel):
    """施策前の実験設計"""
    id: str
    name: str
    policy_id: str

    # Design parameters
    test_type: str = Field(..., description="'ab', 'multi_arm', 'switchback', 'geo'")
    metric: str  # 'revenue', 'conversion', 'retention'
    baseline_mean: float  # 現状の平均値
    baseline_std: float   # 現状の標準偏差

    # Statistical parameters
    mde: float = Field(..., description="Minimum Detectable Effect (相対変化率)")
    alpha: float = Field(0.05, description="有意水準")
    power: float = Field(0.8, description="検出力")
    sides: int = Field(2, description="1 (片側) or 2 (両側)")

    # Computed results
    required_sample_size: Optional[int] = None  # 必要サンプルサイズ
    required_duration_days: Optional[int] = None  # 必要実験期間
    allocation: Optional[Dict[str, float]] = None  # {"control": 0.5, "treatment": 0.5}

    # Advanced settings (v2.0では未実装、将来拡張)
    stratification: Optional[List[str]] = None  # 層化変数
    clustering: Optional[str] = None  # クラスタリング単位

    created_at: str
    created_by: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "exp-plan-001",
                "name": "Q2 Marketing Campaign Test",
                "test_type": "ab",
                "metric": "revenue",
                "baseline_mean": 100000,
                "baseline_std": 20000,
                "mde": 0.05,  # 5%の改善を検出したい
                "alpha": 0.05,
                "power": 0.8,
                "required_sample_size": 6272,
                "required_duration_days": 14,
                "allocation": {"control": 0.5, "treatment": 0.5}
            }
        }
```

---

## v2 新API仕様

### Policy Lab API

#### 1. Policy一覧取得
```
GET /api/v2/policies
```

**Query Parameters**
- `page` (int, default=1): ページ番号
- `limit` (int, default=50, max=100): 1ページあたりの件数
- `status` (str, optional): フィルタ ('draft', 'learning', 'completed')

**Response**
```json
{
  "items": [
    {
      "id": "policy-abc123",
      "name": "High-Value Customer Marketing",
      "policy_type": "threshold",
      "status": "completed",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 127,
    "pages": 3
  }
}
```

#### 2. Policy作成
```
POST /api/v2/policies
```

**Request Body** (`PolicyConfig`)
```json
{
  "name": "High-Value Customer Marketing",
  "policy_type": "threshold",
  "treatment_variable": "marketing_spend",
  "outcome_variable": "revenue",
  "threshold": 0.3,
  "budget_constraint": 10000000,
  "dataset_id": "dataset-xyz",
  "model_id": "model-456"
}
```

**Response** (201 Created)
```json
{
  "id": "policy-abc123",
  "name": "High-Value Customer Marketing",
  "status": "draft",
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Errors**
- `400`: バリデーションエラー（threshold範囲外、model_id不正等）
- `403`: 権限不足 (`policies:write` 必要)
- `404`: dataset_id または model_id が存在しない

#### 3. Offline Policy Learning実行
```
POST /api/v2/policies/{policy_id}/offline-learn
```

**Request Body**
```json
{
  "objective": "delta_revenue",
  "risk_metric": "std",
  "ope_method": "DR",
  "threshold_grid": [0.1, 0.2, 0.3, 0.4, 0.5],
  "coverage_grid": [0.1, 0.2, 0.3, 0.5]
}
```

**Response** (202 Accepted)
```json
{
  "run_id": "run-789",
  "status": "queued",
  "estimated_duration_seconds": 180,
  "message": "Offline policy learning job queued. Check status at /api/v2/policies/runs/{run_id}"
}
```

**処理フロー**
1. `PolicyConfig` からベースポリシーを取得
2. Celeryタスクをキューに投入
3. バックグラウンドで以下を実行：
   - 指定dataset + model で uplift score 計算
   - Grid search: threshold × coverage の組み合わせごとに OPE 推定
   - Pareto frontier 計算（期待値 vs リスク）
   - 最適 policy を選択

#### 4. Learning Run状態取得
```
GET /api/v2/policies/runs/{run_id}
```

**Response**
```json
{
  "id": "run-789",
  "status": "completed",
  "progress": 100,
  "started_at": "2025-01-15T10:35:00Z",
  "completed_at": "2025-01-15T10:38:00Z",
  "frontier": [
    {"threshold": 0.1, "expected_revenue": 5000000, "risk": 200000, "coverage": 0.45},
    {"threshold": 0.3, "expected_revenue": 4500000, "risk": 100000, "coverage": 0.35},
    {"threshold": 0.5, "expected_revenue": 3000000, "risk": 50000, "coverage": 0.15}
  ],
  "best_policy": {
    "threshold": 0.3,
    "expected_revenue": 4500000,
    "risk": 100000,
    "coverage": 0.35
  },
  "ope_metrics": {
    "method": "DR",
    "bias": 12000,
    "variance": 45000,
    "mse": 57000
  }
}
```

#### 5. Policy更新（学習結果を反映）
```
PUT /api/v2/policies/{policy_id}
```

**Request Body**
```json
{
  "threshold": 0.3,
  "status": "production"
}
```

**Response** (200 OK)
```json
{
  "id": "policy-abc123",
  "name": "High-Value Customer Marketing",
  "threshold": 0.3,
  "status": "production",
  "updated_at": "2025-01-15T10:40:00Z"
}
```

---

### Recourse API

#### 1. 個客レベルRecourse取得
```
GET /api/v2/recourse/{unit_id}
```

**Query Parameters**
- `policy_id` (str, required): 使用する policy
- `target_outcome` (float, required): 目標値
- `max_cost` (float, optional): 最大コスト制約
- `top_k` (int, default=5, max=10): 返す候補数

**Response**
```json
{
  "id": "recourse-001",
  "unit_id": "customer-12345",
  "policy_id": "policy-abc123",
  "current_features": {
    "age": 35,
    "income": 50000,
    "marketing_spend": 0
  },
  "current_predicted_outcome": 0.1,
  "target_outcome": 0.8,
  "candidates": [
    {
      "intervention": {"marketing_spend": 3000, "discount": 0.05},
      "predicted_outcome": 0.75,
      "cost": 3150,
      "feasibility_score": 0.9,
      "explanation": "適度なマーケ投資と小割引で高確率転換"
    }
  ]
}
```

**Errors**
- `400`: target_outcome が不正（範囲外）
- `403`: 権限不足 (`recourse:read` 必要) ※ v2で新設
- `404`: unit_id が dataset に存在しない

**セキュリティ制約**
- **個客レベルデータは保存しない**: レスポンスのみ、DBには集計のみ保存
- **監査ログ**: 誰がどの unit_id の recourse を要求したかを記録（GDPR対応）

#### 2. Recourseバッチ計算（セグメント単位）
```
POST /api/v2/recourse/batch
```

**Request Body**
```json
{
  "segment_filter": {"age_group": "30-40", "income_bracket": "high"},
  "policy_id": "policy-abc123",
  "target_outcome": 0.8,
  "max_cost": 5000,
  "top_k": 3
}
```

**Response** (202 Accepted)
```json
{
  "job_id": "recourse-batch-001",
  "status": "queued",
  "estimated_count": 1523,
  "message": "Batch recourse calculation queued. Results will be aggregated and saved as segment summary."
}
```

**処理後の保存内容（個客レベルは保存しない）**
```sql
INSERT INTO segment_recourse_summary (segment_name, policy_id, summary)
VALUES (
  'high_income_30_40',
  'policy-abc123',
  '{
    "count": 1523,
    "avg_predicted_improvement": 0.65,
    "top_interventions": [
      {"type": "marketing_spend", "frequency": 0.78, "avg_cost": 3200},
      {"type": "discount", "frequency": 0.45, "avg_cost": 1500}
    ]
  }'
);
```

---

### Experiment Design API

#### 1. 実験計画作成
```
POST /api/v2/experiments/design
```

**Request Body**
```json
{
  "name": "Q2 Marketing Campaign Test",
  "policy_id": "policy-abc123",
  "test_type": "ab",
  "metric": "revenue",
  "baseline_mean": 100000,
  "baseline_std": 20000,
  "mde": 0.05,
  "alpha": 0.05,
  "power": 0.8
}
```

**Response** (201 Created)
```json
{
  "id": "exp-plan-001",
  "name": "Q2 Marketing Campaign Test",
  "required_sample_size": 6272,
  "required_duration_days": 14,
  "allocation": {"control": 0.5, "treatment": 0.5},
  "power_curve": [
    {"mde": 0.03, "sample_size": 17422},
    {"mde": 0.05, "sample_size": 6272},
    {"mde": 0.10, "sample_size": 1568}
  ],
  "created_at": "2025-01-15T11:00:00Z"
}
```

**計算ロジック**
```python
from scipy.stats import norm
import math

def calculate_sample_size(baseline_mean, baseline_std, mde, alpha=0.05, power=0.8, sides=2):
    """A/Bテストのサンプルサイズ計算"""
    z_alpha = norm.ppf(1 - alpha / sides)
    z_beta = norm.ppf(power)

    effect_size = (baseline_mean * mde) / baseline_std

    n = 2 * ((z_alpha + z_beta) / effect_size) ** 2

    return math.ceil(n)
```

#### 2. 実験計画一覧取得
```
GET /api/v2/experiments/design
```

**Response**
```json
{
  "items": [
    {
      "id": "exp-plan-001",
      "name": "Q2 Marketing Campaign Test",
      "test_type": "ab",
      "metric": "revenue",
      "required_sample_size": 6272,
      "created_at": "2025-01-15T11:00:00Z"
    }
  ],
  "pagination": {...}
}
```

#### 3. 実験計画詳細取得
```
GET /api/v2/experiments/design/{plan_id}
```

---

## Offline Policy Learning Engine 詳細

### アルゴリズム仕様（v2.0）

**入力**
- Dataset (with treatment, outcome, covariates)
- Uplift model (trained)
- Objective function: `max E[Δ¥(policy)]` or `max E[Δ¥] - λ * Var[Δ¥]`
- Search space: `threshold_grid`, `coverage_grid`

**ステップ**

1. **Uplift Score計算**
```python
# すべてのunitに対してuplift scoreを計算
uplift_scores = model.predict_uplift(dataset)
```

2. **Grid Search**
```python
results = []
for threshold in threshold_grid:
    for coverage in coverage_grid:
        # Policy定義: uplift > threshold and top coverage%
        policy = create_threshold_policy(threshold, coverage)

        # Off-Policy Evaluation (OPE)
        ope_estimate = evaluate_policy_ope(
            policy=policy,
            dataset=dataset,
            method='DR'  # Doubly Robust
        )

        results.append({
            'threshold': threshold,
            'coverage': coverage,
            'expected_revenue': ope_estimate.mean,
            'risk': ope_estimate.std,
            'ope_bias': ope_estimate.bias,
            'ope_variance': ope_estimate.variance
        })
```

3. **Pareto Frontier計算**
```python
from scipy.spatial import ConvexHull

# 期待値 vs リスク の2次元空間でPareto最適解を抽出
frontier = compute_pareto_frontier(
    results,
    x_key='risk',
    y_key='expected_revenue'
)
```

4. **Best Policy選択**
```python
# デフォルト: 最大期待値
best = max(frontier, key=lambda x: x['expected_revenue'])

# または: Sharpe比最大
best = max(frontier, key=lambda x: x['expected_revenue'] / x['risk'])
```

**OPE手法（Doubly Robust Estimator）**
```python
def doubly_robust_estimator(policy, dataset):
    """
    DR = E[ (Y - μ(X,A)) * π(A|X) / e(A|X) + μ(X, π(X)) ]

    where:
    - π(A|X): policy (treatment assignment rule)
    - e(A|X): propensity score (observed treatment probability)
    - μ(X,A): outcome regression model
    """
    n = len(dataset)
    estimates = []

    for i in range(n):
        x = dataset.iloc[i]['features']
        a_obs = dataset.iloc[i]['treatment']
        y_obs = dataset.iloc[i]['outcome']

        # Propensity score (from logged data or model)
        e = dataset.iloc[i]['propensity']

        # Outcome model
        mu_obs = outcome_model.predict(x, a_obs)

        # Policy treatment
        a_policy = policy.assign_treatment(x)
        mu_policy = outcome_model.predict(x, a_policy)

        # Policy probability
        pi = 1.0 if a_policy == a_obs else 0.0

        # DR estimator
        estimate = (y_obs - mu_obs) * (pi / e) + mu_policy
        estimates.append(estimate)

    return {
        'mean': np.mean(estimates),
        'std': np.std(estimates),
        'bias': np.mean([(y - mu) for y, mu in zip(estimates, outcome_model predictions)]),
        'variance': np.var(estimates)
    }
```

**制約・近似**
- v2.0では**threshold policy**のみサポート（簡潔性優先）
- Grid searchは粗いグリッド（計算時間短縮）
- 将来拡張: Decision tree policy, Contextual bandit policy

---

## Recourse 守備範囲（v2.0）

### スコープ定義

**v2.0で実装する範囲**
- **API レスポンスのみ**: 個客レベル recourse は計算してレスポンスで返すが、**DBには保存しない**
- **セグメント集計のみ保存**: バッチ計算の場合、セグメント単位での集計結果のみ保存
- **UI表示**: Main または ROI ページの右側に `RecoursePanel` として1コンポーネント配置

**スコープ外（将来拡張）**
- Policy自動更新: Recourse結果をフィードバックしてpolicyを再学習（Phase 2）
- リアルタイム推奨: ユーザーがログインした瞬間に recourse を表示（Phase 3）
- A/B テスト連携: Recourse候補を実験で検証（Phase 3）

### UI配置

**RecoursePanel コンポーネント（右サイドパネル）**
```
┌─────────────────────────────────────────────────────────────┐
│ Portfolio & ROI Analysis                                     │
├──────────────────────────────┬──────────────────────────────┤
│ ROI Chart (Left 60%)         │ Recourse Panel (Right 40%)  │
│                              │ ────────────────────────────│
│  [ROI推移グラフ]             │ 個客ID: customer-12345      │
│  [ポリシー比較表]             │ 現在予測: 転換率 10%        │
│                              │ 目標: 転換率 80%            │
│                              │                             │
│                              │ 推奨アクション (Top 3):     │
│                              │ ───────────────────────────│
│                              │ 1. マーケ投資 3,000円       │
│                              │    + 5%割引                 │
│                              │    → 予測転換率: 75%        │
│                              │    コスト: 3,150円          │
│                              │    [詳細] [適用]            │
│                              │                             │
│                              │ 2. マーケ投資 5,000円       │
│                              │    → 予測転換率: 85%        │
│                              │    コスト: 5,000円          │
│                              │    [詳細] [適用]            │
│                              │                             │
│                              │ 3. チャネル変更: email→push │
│                              │    → 予測転換率: 70%        │
│                              │    コスト: 500円            │
│                              │    [詳細] [適用]            │
└──────────────────────────────┴──────────────────────────────┘
```

**アクセス方法**
```typescript
// frontend/src/pages/Portfolio.tsx
import { RecoursePanel } from '../components/RecoursePanel'

function Portfolio() {
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(null)

  return (
    <div className="portfolio-layout">
      <div className="left-column">
        {/* ROI Charts & Tables */}
        <PolicyTable onRowClick={(policy) => setSelectedUnitId(policy.unit_id)} />
      </div>

      <div className="right-column">
        {selectedUnitId && (
          <RecoursePanel
            unitId={selectedUnitId}
            policyId={currentPolicyId}
            targetOutcome={0.8}
          />
        )}
      </div>
    </div>
  )
}
```

### セキュリティ・監査

**個客レベルデータの保存禁止**
```python
# ❌ Bad: 個客IDと紐付けて保存（禁止）
await db.execute("""
    INSERT INTO individual_recourse (unit_id, intervention, predicted_outcome)
    VALUES ($1, $2, $3)
""", unit_id, intervention, predicted_outcome)

# ✅ Good: セグメント集計のみ保存
segment_summary = {
    "segment": "high_value_30_40",
    "count": 1523,
    "top_interventions": [
        {"type": "marketing_spend", "frequency": 0.78, "avg_cost": 3200}
    ]
}
await db.execute("""
    INSERT INTO segment_recourse_summary (segment_name, summary)
    VALUES ($1, $2)
""", segment_name, segment_summary)
```

**監査ログ**
```sql
-- Recourse APIアクセスは監査ログに記録
INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details)
VALUES (
    'user-123',
    'READ_RECOURSE',
    'unit',
    'customer-12345',
    '{"policy_id": "policy-abc", "target_outcome": 0.8}'
);
```

---

## Experiment Design スコープ（v2.0）

### 最小スコープ

**v2.0で実装**
- **A/Bテストのサンプルサイズ計算**: 基本統計のみ
- **検出力曲線**: MDE vs サンプルサイズ のグラフ表示
- **設計カード**: 必要サンプル数、期間、割当比を表示

**スコープ外（将来拡張候補）**
- Geo実験設計（Phase 2）
- Switchback実験設計（Phase 2）
- Multi-arm bandit最適化（Phase 3）
- 層化・クラスタリング自動推奨（Phase 3）

### UI配置

**Experiment Design ページ**
```
┌─────────────────────────────────────────────────────────────┐
│ Experiment Design                                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│ 実験パラメータ入力                                           │
│ ──────────────────────────────────────────────────────────── │
│                                                               │
│ Policy: [High-Value Customer Marketing ▼]                    │
│ テストタイプ: [A/B Test ▼]                                   │
│ メトリクス: [Revenue ▼]                                      │
│                                                               │
│ ベースライン平均: [100,000] 円                               │
│ ベースライン標準偏差: [20,000] 円                            │
│                                                               │
│ 検出したい効果 (MDE): [5] %                                  │
│ 有意水準 (α): [0.05]                                         │
│ 検出力 (Power): [0.8]                                        │
│                                                               │
│                                 [計算実行]                    │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ 計算結果                                                      │
│ ──────────────────────────────────────────────────────────── │
│                                                               │
│ ✅ 必要サンプルサイズ: 6,272 人 (各群 3,136 人)              │
│ ✅ 推定実験期間: 14 日間 (想定 DAU: 500人)                   │
│ ✅ 推奨割当: Control 50% / Treatment 50%                     │
│                                                               │
│ ──────────────────────────────────────────────────────────── │
│ 検出力曲線                                                    │
│                                                               │
│  1.0│        ╱────────                                       │
│  0.8│      ╱                                                 │
│  0.6│    ╱                                                   │
│  0.4│  ╱                                                     │
│  0.2│╱                                                       │
│  0.0└─────────────────                                       │
│     0%  3%  5%  7% 10%  MDE                                  │
│                                                               │
│                              [実験設計を保存]                 │
└───────────────────────────────────────────────────────────────┘
```

---

## v2 固有のセキュリティ・監査

### 監査対象

**Policy Lab**
- 誰が（user_id）
- どのdatasetに対して（dataset_id）
- どんな目的関数で（objective, risk_metric）
- どんなfrontierを見て（学習結果）
- どのpolicyを採用したか（best_policy）

**監査ログテーブル拡張**
```sql
ALTER TABLE audit_logs ADD COLUMN v2_metadata JSONB;

-- Example
INSERT INTO audit_logs (user_id, action, resource_type, resource_id, v2_metadata)
VALUES (
    'user-analyst-1',
    'OFFLINE_POLICY_LEARNING',
    'policy',
    'policy-abc123',
    '{
        "dataset_id": "dataset-xyz",
        "objective": "delta_revenue",
        "risk_metric": "std",
        "frontier_count": 15,
        "best_threshold": 0.3,
        "expected_revenue": 4500000,
        "adopted": true
    }'
);
```

### 保持期間

**Policy学習ログ**
- 学習結果（frontier）: 90日間保持
- Adopted policy: 永久保持（削除不可、監査証跡）

**Recourse**
- 個客レベル: レスポンスのみ、保存しない
- セグメント集計: 90日間保持

**Experiment Design**
- 設計カード: 作成から1年間保持
- 実験実行ログ（将来拡張）: 2年間保持

---

## UI への追記部分

### 新規ページ

1. **Policy Lab** (`/policy-lab`)
   - Permission: `policies:write`
   - 機能: Policy作成、Offline Learning実行、Frontier可視化

2. **Experiment Design** (`/experiments/design`)
   - Permission: `experiments:write` (新設)
   - 機能: サンプルサイズ計算、検出力曲線表示

### 既存ページへの追加

1. **Portfolio & ROI** (`/portfolio`)
   - 右側に `RecoursePanel` コンポーネント追加
   - Permission: `recourse:read` (新設)

### ナビゲーション更新

```tsx
// frontend/src/App.tsx
const navItems = [
  { path: '/console', label: 'Decision Console', permission: 'console:read' },
  { path: '/policy-lab', label: 'Policy Lab', permission: 'policies:write' }, // 新規
  { path: '/causal', label: 'Causal Design', permission: 'models:read' },
  { path: '/portfolio', label: 'Portfolio & ROI', permission: 'policies:read' },
  { path: '/diagnostics', label: 'Diagnostics', permission: 'diagnostics:read' },
  { path: '/experiments', label: 'Experiment Design', permission: 'experiments:write' }, // 新規
  { path: '/admin', label: 'Admin Panel', role: 'admin' },
]
```

### URL State Examples

**Policy Lab**
```
/policy-lab?tab=frontier&policy_id=policy-abc123&run_id=run-789&threshold=0.3
```

**Recourse Panel**
```
/portfolio?unit_id=customer-12345&policy_id=policy-abc123&target_outcome=0.8
```

**Experiment Design**
```
/experiments/design?policy_id=policy-abc123&mde=0.05&power=0.8&metric=revenue
```

---

## まとめ

### v2で追加されるもの

**新ドメインオブジェクト (4つ)**
1. PolicyConfig: 治療割当ルール
2. OfflinePolicyRun: オフライン学習実行結果
3. RecoursePlan: 個客レベル介入提案
4. ExperimentPlan: 実験設計

**新API (10エンドポイント)**
1. GET /api/v2/policies
2. POST /api/v2/policies
3. POST /api/v2/policies/{id}/offline-learn
4. GET /api/v2/policies/runs/{run_id}
5. PUT /api/v2/policies/{id}
6. GET /api/v2/recourse/{unit_id}
7. POST /api/v2/recourse/batch
8. POST /api/v2/experiments/design
9. GET /api/v2/experiments/design
10. GET /api/v2/experiments/design/{plan_id}

**新UI (2ページ + 1コンポーネント)**
1. Policy Lab ページ
2. Experiment Design ページ
3. RecoursePanel コンポーネント（Portfolio ページ内）

**新Permission (2つ)**
1. `recourse:read`: Recourse API アクセス
2. `experiments:write`: 実験設計作成

### v1との共存

- **v1 API**: `/api/v1/*` は引き続き動作（後方互換性維持）
- **v2 API**: `/api/v2/*` で新機能を提供
- **データベース**: v1テーブルはそのまま、v2用テーブルを追加
- **UI**: v1ページは維持、v2ページを追加

### 実装優先順位

**Phase 1 (v2.0 MVP)**
1. PolicyConfig + Offline Policy Learning API
2. Policy Lab UI (Frontier可視化まで)
3. Experiment Design API + UI

**Phase 2 (v2.1)**
1. Recourse API + RecoursePanel UI
2. Batch Recourse計算

**Phase 3 (v2.2+)**
1. Geo / Switchback実験設計
2. Policy自動更新
3. リアルタイムRecourse推奨

---

## 次のステップ

1. **v1仕様書の更新**: スコープ境界、UIマッピング表、セキュリティ制約を追記
2. **実装開始**: v2.0 MVP（Policy Lab + Experiment Design）から着手
3. **統合テスト**: v1/v2 API の共存を確認
4. **ドキュメント更新**: API仕様書（OpenAPI）にv2エンドポイント追加
