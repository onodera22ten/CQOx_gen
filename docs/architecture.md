# CQOx システムアーキテクチャ

## 概要

CQOx (Causal Query Optimizer) は、因果推論とポリシー最適化のためのエンタープライズグレードのプラットフォームです。Wolfram ONE統合、世界最高峰のインフラストラクチャ、包括的なセキュリティレイヤーを備えています。

---

## 実装レイヤーと段階的展開

CQOxは段階的な展開を前提として、3つの実装レイヤーを定義します。

### v1: Single-Node / Docker Compose版（初期デプロイ）

**対象環境**: Fedora/RHEL上での単一ノード展開、またはローカル開発環境

**目的**:
- オフライン因果推論 + ScenarioSpec + DecisionCard（Δ¥ + Go/Canary/Hold）まで
- 施策**前**のオフラインポリシー評価（Offline Policy Learning）を主目的
- 実施済みキャンペーンの事後評価は副次用途

**機能スコープ**:
- ✅ Data Contract + Mapping + Great Expectations
- ✅ 因果推論推定器（DR, IPW, DiD, IV, CF, SCM, RD）
- ✅ ScenarioSpec（S0現行 vs S1候補）+ Money-View（Δ¥計算）
- ✅ DecisionCard生成（verdict: Go/Canary/Hold）
- ✅ Decision Console UI（Δ¥ランキング最優先表示）
- ✅ Diagnostics（Overlap, IV, RD品質チェック）
- ✅ Portfolio & ROI（キャンペーン/チャネル別投資対効果）
- ❌ Policy Lab v2（Offline Policy Learning UI）
- ❌ Recourse v2（個客レベル介入）
- ❌ Experiment Design v2（A/Bテスト設計）

**技術スタック**:
- FastAPI (Backend) + React (Frontend) + Nginx
- PostgreSQL 15 (メタデータ + 結果)
- Parquet/S3 (データセット保存)
- Redis (オプション: キャッシュ)
- Prometheus + Grafana (オプション: 監視)

**最小構成図（v1）**:
```mermaid
graph LR
    Browser[Web Browser] --> Nginx[Nginx<br/>Static + Proxy]
    Nginx --> FastAPI[FastAPI<br/>v1 API]
    FastAPI --> PostgreSQL[(PostgreSQL<br/>DATASETS/DECISIONS)]
    FastAPI --> Parquet[(S3/MinIO<br/>Parquet Files)]
    FastAPI --> Redis[(Redis<br/>Cache)]
    FastAPI --> Prometheus[Prometheus<br/>Optional]
    Prometheus --> Grafana[Grafana<br/>Optional]
```

**デプロイ方法**: `docker-compose up -d`（全コンポーネント単一ノード）

---

### v2: Policy Lab / Recourse追加（機能拡張）

**対象環境**: v1と同じインフラ上で機能追加（Feature Flag制御）

**追加機能**:
- ✅ Policy Lab v2: Offline Policy Learning UI
  - Pareto frontier可視化
  - Multi-objective最適化（期待値 vs リスク）
- ✅ Recourse v2: 個客レベル介入計画
  - Counterfactual生成
  - コスト/実現可能性評価
  - **PII非保存**（GDPR準拠）
- ✅ Experiment Design v2: A/Bテスト設計
  - サンプルサイズ計算
  - Power curve可視化

**技術スタック**: v1と同じ（追加なし）

**API名前空間**: `/api/v2/policies`, `/api/v2/recourse`, `/api/v2/experiments`

**v1との関係**:
- 同じData Contractを共用
- 同じPostgreSQL/Parquetストレージ
- UI/APIは別ルート（Feature Flagで非表示可能）

---

### Enterprise: Managed K8s / GitOps / Multi-Tenant（SaaS化）

**対象環境**: AWS EKS / Google GKE / Azure AKS

**目的**:
- マルチテナント対応
- 99.9% SLO達成
- グローバル展開（Multi-Region）

**追加機能**:
- ✅ Kubernetes + ArgoCD (GitOps)
- ✅ HashiCorp Vault (シークレット管理)
- ✅ Multi-Tenancy (PostgreSQL RLS)
- ✅ Distributed Job Execution (Celery + RabbitMQ)
- ✅ Canary Deployment (Argo Rollouts)
- ✅ SLO-based Monitoring (Prometheus + Grafana)
- ✅ MLOps (モデルバージョニング + ドリフト検出)

**技術スタック追加**:
- Kubernetes (EKS/GKE/AKS)
- ArgoCD (GitOps)
- HashiCorp Vault
- RabbitMQ (メッセージキュー)
- Celery Workers (Heavy/Light/Realtime queues)
- Argo Rollouts (カナリアデプロイ)

**デプロイ方法**: `kubectl apply -f k8s/base/` + ArgoCD自動同期

---

## フルエンタープライズ・システムアーキテクチャ（Enterprise層）

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
        MOBILE[Mobile Apps]
        API_CLIENT[API Clients]
    end

    subgraph "CDN & Load Balancer"
        CDN[CloudFront CDN]
        LB[Application Load Balancer]
        WAF[AWS WAF]
    end

    subgraph "Frontend Layer"
        REACT[React SPA<br/>TypeScript + Vite]
        NGINX[Nginx<br/>Static Server]
    end

    subgraph "API Gateway & Security"
        GATEWAY[API Gateway]
        AUTH[Authentication Layer<br/>JWT + OAuth2 + API Keys]
        RATE_LIMIT[Rate Limiter<br/>100 req/min]
        RBAC[RBAC Engine<br/>Admin/Analyst/Viewer]
    end

    subgraph "Backend Services"
        FASTAPI[FastAPI Application<br/>Python 3.11+]
        CELERY[Celery Workers<br/>Async Tasks]
        WOLFRAM[Wolfram ONE<br/>Integration Service]

        subgraph "API Routes"
            CONSOLE_API[Console API]
            POLICY_API[Policy API]
            CAUSAL_API[Causal API]
            DIAG_API[Diagnostics API]
            PORTFOLIO_API[Portfolio API]
            ADMIN_API[Admin API]
            UPLOAD_API[Upload API]
            VIZ_API[Visualization API]
        end
    end

    subgraph "Storage Layer (Layer 3)"
        POSTGRES[(PostgreSQL 15<br/>Primary Database)]
        TIMESCALE[(TimescaleDB<br/>Time-series Data)]
        REDIS[(Redis 7<br/>Cache + Sessions)]
        S3[(MinIO/S3<br/>Object Storage)]
        VAULT[HashiCorp Vault<br/>Secrets Management]
    end

    subgraph "Observability Layer (Layer 2)"
        PROMETHEUS[Prometheus<br/>Metrics Collection]
        GRAFANA[Grafana<br/>Dashboards + Alerts]
        LOKI[Loki<br/>Log Aggregation]
        JAEGER[Jaeger<br/>Distributed Tracing]
        ALERTMANAGER[AlertManager<br/>Alert Routing]
    end

    subgraph "Infrastructure Layer (Layer 1)"
        K8S[Kubernetes Cluster<br/>EKS/GKE/AKS]
        ARGOCD[ArgoCD<br/>GitOps CD]
        DOCKER[Docker Registry<br/>GHCR]
    end

    subgraph "Message Queue"
        RABBITMQ[RabbitMQ<br/>Message Broker]
    end

    subgraph "External Services"
        OAUTH_PROVIDERS[OAuth Providers<br/>Google, GitHub, Microsoft]
        SMTP[SMTP Server<br/>Email Notifications]
        WOLFRAM_CLOUD[Wolfram Cloud API]
    end

    WEB --> CDN
    MOBILE --> CDN
    API_CLIENT --> LB
    CDN --> WAF
    WAF --> LB
    LB --> NGINX
    LB --> GATEWAY

    NGINX --> REACT

    GATEWAY --> AUTH
    AUTH --> RATE_LIMIT
    RATE_LIMIT --> RBAC
    RBAC --> FASTAPI

    FASTAPI --> CONSOLE_API
    FASTAPI --> POLICY_API
    FASTAPI --> CAUSAL_API
    FASTAPI --> DIAG_API
    FASTAPI --> PORTFOLIO_API
    FASTAPI --> ADMIN_API
    FASTAPI --> UPLOAD_API
    FASTAPI --> VIZ_API

    FASTAPI --> CELERY
    FASTAPI --> WOLFRAM

    CELERY --> RABBITMQ
    WOLFRAM --> WOLFRAM_CLOUD

    FASTAPI --> POSTGRES
    FASTAPI --> REDIS
    FASTAPI --> S3
    FASTAPI --> VAULT
    CELERY --> POSTGRES
    CELERY --> TIMESCALE
    CELERY --> REDIS
    CELERY --> S3

    FASTAPI --> PROMETHEUS
    CELERY --> PROMETHEUS
    PROMETHEUS --> GRAFANA
    FASTAPI --> LOKI
    FASTAPI --> JAEGER
    PROMETHEUS --> ALERTMANAGER
    ALERTMANAGER --> SMTP

    AUTH --> OAUTH_PROVIDERS

    K8S -.-> FASTAPI
    K8S -.-> CELERY
    K8S -.-> POSTGRES
    K8S -.-> REDIS
    K8S -.-> RABBITMQ
    ARGOCD -.-> K8S
    DOCKER -.-> K8S

    classDef client fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef frontend fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef backend fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef storage fill:#f8bbd0,stroke:#c2185b,stroke-width:2px
    classDef observability fill:#d1c4e9,stroke:#512da8,stroke-width:2px
    classDef infra fill:#ffccbc,stroke:#d84315,stroke-width:2px
    classDef security fill:#ffeb3b,stroke:#f57f00,stroke-width:3px

    class WEB,MOBILE,API_CLIENT client
    class REACT,NGINX frontend
    class FASTAPI,CELERY,WOLFRAM,CONSOLE_API,POLICY_API,CAUSAL_API,DIAG_API,PORTFOLIO_API,ADMIN_API,UPLOAD_API,VIZ_API backend
    class POSTGRES,TIMESCALE,REDIS,S3,VAULT storage
    class PROMETHEUS,GRAFANA,LOKI,JAEGER,ALERTMANAGER observability
    class K8S,ARGOCD,DOCKER infra
    class AUTH,RATE_LIMIT,RBAC,GATEWAY,WAF security
```

---

## セキュリティアーキテクチャ

```mermaid
graph TB
    subgraph "Security Layers"
        subgraph "Layer 1: Network Security"
            WAF[AWS WAF<br/>DDoS Protection]
            SSL[SSL/TLS Termination<br/>TLS 1.3]
            FIREWALL[Network Firewall<br/>Security Groups]
        end

        subgraph "Layer 2: Authentication"
            JWT[JWT Tokens<br/>HS256/RS256]
            OAUTH[OAuth2<br/>Google/GitHub/MS]
            APIKEY[API Keys<br/>SHA-256 Hashed]
            MFA[MFA Support<br/>TOTP]
        end

        subgraph "Layer 3: Authorization"
            RBAC_ENGINE[RBAC Engine]
            PERMISSIONS[Permission Matrix<br/>13 Permissions]
            ROLES[Role Hierarchy<br/>Admin > Analyst > Viewer]
        end

        subgraph "Layer 4: Data Security"
            ENCRYPTION[Field-level Encryption<br/>AES-256-GCM]
            VAULT_MGR[Vault Integration<br/>Secret Rotation]
            TDE[Database TDE<br/>Transparent Encryption]
        end

        subgraph "Layer 5: Compliance"
            GDPR[GDPR Handler<br/>Right to Erasure]
            AUDIT[Audit Logging<br/>All Access Events]
            CONSENT[Consent Management<br/>User Agreements]
        end

        subgraph "Layer 6: Runtime Security"
            RATE_LIMITER[Rate Limiting<br/>Sliding Window]
            INPUT_VAL[Input Validation<br/>Pydantic + Regex]
            SANITIZATION[Output Sanitization<br/>XSS Prevention]
            CORS_POLICY[CORS Policy<br/>Strict Origins]
        end
    end

    REQUEST[HTTP Request] --> WAF
    WAF --> SSL
    SSL --> FIREWALL
    FIREWALL --> JWT
    FIREWALL --> OAUTH
    FIREWALL --> APIKEY
    JWT --> MFA
    OAUTH --> MFA

    MFA --> RBAC_ENGINE
    RBAC_ENGINE --> PERMISSIONS
    PERMISSIONS --> ROLES

    ROLES --> RATE_LIMITER
    RATE_LIMITER --> INPUT_VAL
    INPUT_VAL --> ENCRYPTION
    ENCRYPTION --> VAULT_MGR
    VAULT_MGR --> TDE

    ROLES --> AUDIT
    AUDIT --> GDPR
    GDPR --> CONSENT

    INPUT_VAL --> SANITIZATION
    SANITIZATION --> CORS_POLICY
    CORS_POLICY --> APP[Application Logic]

    classDef network fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    classDef auth fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef authz fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef data fill:#b3e5fc,stroke:#0277bd,stroke-width:2px
    classDef compliance fill:#d1c4e9,stroke:#512da8,stroke-width:2px
    classDef runtime fill:#ffccbc,stroke:#d84315,stroke-width:2px

    class WAF,SSL,FIREWALL network
    class JWT,OAUTH,APIKEY,MFA auth
    class RBAC_ENGINE,PERMISSIONS,ROLES authz
    class ENCRYPTION,VAULT_MGR,TDE data
    class GDPR,AUDIT,CONSENT compliance
    class RATE_LIMITER,INPUT_VAL,SANITIZATION,CORS_POLICY runtime
```

---

## データ分類とThreat Model

CQOxでは、扱うデータの機密性レベルに応じて、4段階のデータ分類を定義します。

### データ分類（Data Classification）

| レベル | 分類 | データ種別 | 保存先 | 暗号化 | ログ出力 | 例 |
|--------|------|-----------|--------|--------|---------|---|
| **Level 0** | 公開情報 | ヘルプ、FAQ、公開ドキュメント | CDN, S3 Public | 不要 | ✅ 可能 | UI画面、APIドキュメント |
| **Level 1** | 組織内メタデータ | POLICIES, MODELS, METRICS | PostgreSQL | TDE (透過暗号化) | ✅ 可能（ID、名前のみ） | Policy名、モデルID、CASスコア |
| **Level 2** | 準機微データ | 集計済みDIAGNOSTICS, DECISIONS | PostgreSQL | TDE + Field-level AES-256 | ⚠️ 集計値のみ | Δ¥集計、Overlap平均値 |
| **Level 3** | 高機微データ | DATASETS生データ、個客Recourse | Parquet (S3) + PostgreSQL (カラムマッピング) | KMS管理鍵 (AES-256-GCM) | ❌ 禁止 | 個客ID、端末ID、位置情報、個客レベル介入計画 |

### 保護方針（Protection Policy）

#### Level 3（高機微データ）の追加要件:
- **アクセス制御**: RBAC `data:read_pii` 権限必須（デフォルト付与なし）
- **監査ログ**: 全アクセスを `AUDIT_LOGS` に記録（誰が・いつ・どのレコードを）
- **データ保持期間**:
  - DATASETS: 90日後にGlacier移行、365日後に削除（法的保持義務がある場合は除く）
  - Recourse結果: **保存しない**（on-the-fly計算のみ、GDPR準拠）
- **匿名化**:
  - Diagnostics生成時に個客IDをハッシュ化（`SHA-256(unit_id + salt)`）
  - DecisionCard生成時にLevel 3データを含めない（集計値のみ）
- **Right to Erasure**: `/api/v1/gdpr/erasure` APIで指定unit_idの全データを物理削除

#### Level 2（準機微データ）の追加要件:
- **フィールド暗号化**: `DECISIONS.estimator_results` の詳細結果をAES-256-GCMで暗号化
- **アクセス制御**: RBAC `models:read` 権限必須
- **ログ出力**: 集計値（平均、中央値）のみ可、個別値は禁止

### Threat Model

CQOxの主要な脅威シナリオと対策を以下に示します。

| 脅威カテゴリ | 脅威シナリオ | 影響レベル | 対策 | 実装箇所 |
|------------|------------|-----------|------|---------|
| **データ漏洩** | 不正アクセスによるDATASETS生データ流出 | 🔴 Critical | KMS暗号化 + RLS + `data:read_pii` 権限 | PostgreSQL RLS, S3 KMS |
| **データ漏洩** | ログファイルに個客IDが出力される | 🟠 High | ログサニタイゼーション（PII自動マスキング） | Logger middleware |
| **権限昇格** | Analyst権限のユーザーがAdmin操作を実行 | 🟠 High | RBAC + 最小権限原則 + APIレベル権限チェック | RBAC Engine |
| **注入攻撃** | SQLインジェクションによるDB改ざん | 🟠 High | ORMプリペアドステートメント + Input Validation | FastAPI + SQLAlchemy |
| **DoS** | 大量リクエストによるサービス停止 | 🟡 Medium | Rate Limiting (100 req/min) + WAF | Redis + AWS WAF |
| **セッションハイジャック** | JWT改ざんによる不正ログイン | 🟡 Medium | JWT署名検証 (RS256) + 短期有効期限 (15分) | Auth middleware |
| **データ推論** | 集計APIから個客情報を逆算 | 🟡 Medium | k-匿名性 (k≥5) + 差分プライバシー（ε=1.0） | Diagnostics API |
| **内部不正** | 管理者による不正データアクセス | 🟡 Medium | 監査ログ + 4-eyes principle（重要操作は2名承認） | AUDIT_LOGS |

#### 差分プライバシー適用例（v2以降）

Level 3データの集計値を返すAPIでは、以下のLaplace Mechanismを適用：

```python
def add_laplace_noise(true_value: float, sensitivity: float, epsilon: float = 1.0) -> float:
    """
    差分プライバシーノイズ追加

    Args:
        true_value: 真の集計値
        sensitivity: クエリの感度（最大変化量）
        epsilon: プライバシーパラメータ（小さいほど強いプライバシー保護）

    Returns:
        ノイズ付き集計値
    """
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)
    return true_value + noise

# 使用例: Δ¥平均値を返す際
true_mean_delta_yen = 15000.0
sensitivity = 100000.0  # 1レコードの最大影響額
noisy_mean = add_laplace_noise(true_mean_delta_yen, sensitivity, epsilon=1.0)
# → 例: 15234.5（ノイズ追加済み）
```

#### k-匿名性チェック（v2以降）

セグメント単位の集計を返す前に、k≥5 を保証：

```python
def check_k_anonymity(df: pd.DataFrame, quasi_identifiers: list[str], k: int = 5) -> bool:
    """
    k-匿名性チェック

    Args:
        df: データフレーム
        quasi_identifiers: 準識別子カラム（例: ["age_group", "prefecture", "gender"]）
        k: 最小グループサイズ

    Returns:
        全グループがk件以上ならTrue
    """
    group_sizes = df.groupby(quasi_identifiers).size()
    min_group_size = group_sizes.min()
    return min_group_size >= k

# 使用例: 都道府県×年齢層別のΔ¥を返す前
if not check_k_anonymity(df, ["prefecture", "age_group"], k=5):
    raise HTTPException(
        status_code=400,
        detail="Cannot return aggregation: k-anonymity violation (some groups < 5)"
    )
```

---

## データフローアーキテクチャ

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant Frontend
    participant CDN
    participant LoadBalancer
    participant APIGateway
    participant Auth
    participant RateLimiter
    participant RBAC
    participant FastAPI
    participant Celery
    participant Wolfram
    participant PostgreSQL
    participant TimescaleDB
    participant Redis
    participant S3
    participant Prometheus

    User->>Frontend: Access Application
    Frontend->>CDN: Request Static Assets
    CDN-->>Frontend: Serve Cached Assets

    User->>Frontend: Login Request
    Frontend->>LoadBalancer: POST /auth/token
    LoadBalancer->>APIGateway: Forward Request
    APIGateway->>Auth: Authenticate User
    Auth->>PostgreSQL: Verify Credentials
    PostgreSQL-->>Auth: User Data
    Auth->>Redis: Store Session
    Auth-->>Frontend: JWT Token (access + refresh)

    User->>Frontend: Submit Analysis Request
    Frontend->>LoadBalancer: POST /api/v1/policies
    LoadBalancer->>APIGateway: Forward with JWT
    APIGateway->>Auth: Validate JWT
    Auth->>Redis: Check Token Validity
    Redis-->>Auth: Token Valid
    Auth->>RateLimiter: Check Rate Limit
    RateLimiter->>Redis: Get Request Count
    Redis-->>RateLimiter: Count: 45/100
    RateLimiter->>RBAC: Check Permissions
    RBAC->>PostgreSQL: Get User Roles
    PostgreSQL-->>RBAC: Roles: [analyst]
    RBAC-->>FastAPI: Authorized (models:write)

    FastAPI->>PostgreSQL: Save Policy Request
    FastAPI->>Celery: Enqueue Training Task
    FastAPI-->>Frontend: 202 Accepted {task_id}

    Celery->>Wolfram: Execute Model Training
    Wolfram->>Wolfram: Causal Analysis
    Wolfram-->>Celery: Training Results
    Celery->>TimescaleDB: Store Metrics
    Celery->>PostgreSQL: Update Policy Status
    Celery->>S3: Upload Model Artifacts
    Celery->>Redis: Cache Results

    Frontend->>LoadBalancer: GET /api/v1/policies/{id}/status
    LoadBalancer->>FastAPI: Forward Request
    FastAPI->>Redis: Check Cache
    Redis-->>FastAPI: Cached Result
    FastAPI-->>Frontend: Policy Results

    FastAPI->>Prometheus: Record Metrics
    Prometheus->>Prometheus: Aggregate Metrics

    Note over User,Prometheus: All requests logged to audit trail
```

---

## CI/CDパイプラインアーキテクチャ

```mermaid
graph LR
    subgraph "Source Control"
        GIT[GitHub Repository]
        BRANCH[Feature Branch]
        MAIN[Main Branch]
    end

    subgraph "CI Pipeline (GitHub Actions)"
        subgraph "Backend CI"
            LINT_BE[Lint<br/>Black, Flake8, MyPy]
            TEST_BE[Tests<br/>Pytest + Coverage]
            SECURITY_BE[Security<br/>Safety, Bandit]
        end

        subgraph "Frontend CI"
            LINT_FE[Lint<br/>ESLint]
            TYPE_FE[Type Check<br/>TypeScript]
            BUILD_FE[Build<br/>Vite]
            E2E_FE[E2E Tests<br/>Playwright]
        end

        subgraph "Container Build"
            DOCKER_BUILD[Docker Build<br/>Multi-stage]
            SECURITY_SCAN[Trivy Scan<br/>Vulnerabilities]
            PUSH_REGISTRY[Push to GHCR<br/>ghcr.io]
        end
    end

    subgraph "CD Pipeline (ArgoCD)"
        ARGOCD_SYNC[ArgoCD Sync]
        K8S_DEPLOY[Kubernetes Deploy]
        HEALTH_CHECK[Health Check]
        ROLLBACK[Auto Rollback]
    end

    subgraph "Environments"
        DEV[Development]
        STAGING[Staging]
        PROD[Production]
    end

    subgraph "Monitoring"
        PROM_ALERT[Prometheus Alerts]
        GRAFANA_DASH[Grafana Dashboards]
        SLACK_NOTIFY[Slack Notifications]
    end

    BRANCH --> GIT
    GIT --> LINT_BE
    GIT --> LINT_FE

    LINT_BE --> TEST_BE
    TEST_BE --> SECURITY_BE

    LINT_FE --> TYPE_FE
    TYPE_FE --> BUILD_FE
    BUILD_FE --> E2E_FE

    SECURITY_BE --> DOCKER_BUILD
    E2E_FE --> DOCKER_BUILD

    DOCKER_BUILD --> SECURITY_SCAN
    SECURITY_SCAN --> PUSH_REGISTRY

    PUSH_REGISTRY --> ARGOCD_SYNC
    ARGOCD_SYNC --> K8S_DEPLOY
    K8S_DEPLOY --> HEALTH_CHECK
    HEALTH_CHECK --> DEV

    DEV --> STAGING
    STAGING --> PROD

    HEALTH_CHECK -.->|Failed| ROLLBACK
    ROLLBACK -.-> MAIN

    PROD --> PROM_ALERT
    PROM_ALERT --> GRAFANA_DASH
    GRAFANA_DASH --> SLACK_NOTIFY

    classDef source fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef ci fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef cd fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef env fill:#f8bbd0,stroke:#c2185b,stroke-width:2px
    classDef monitor fill:#d1c4e9,stroke:#512da8,stroke-width:2px

    class GIT,BRANCH,MAIN source
    class LINT_BE,TEST_BE,SECURITY_BE,LINT_FE,TYPE_FE,BUILD_FE,E2E_FE,DOCKER_BUILD,SECURITY_SCAN,PUSH_REGISTRY ci
    class ARGOCD_SYNC,K8S_DEPLOY,HEALTH_CHECK,ROLLBACK cd
    class DEV,STAGING,PROD env
    class PROM_ALERT,GRAFANA_DASH,SLACK_NOTIFY monitor
```

---

## データベーススキーマアーキテクチャ

```mermaid
erDiagram
    USERS ||--o{ SESSIONS : has
    USERS ||--o{ API_KEYS : owns
    USERS ||--o{ CONSENTS : provides
    USERS ||--o{ AUDIT_LOGS : generates
    USERS ||--o{ DATASETS : uploads
    USERS ||--o{ POLICIES : creates
    USERS ||--o{ MODELS : trains

    USERS {
        uuid id PK
        string email UK
        string password_hash
        string name
        json roles
        json permissions
        timestamp created_at
        timestamp deleted_at
        boolean active
    }

    SESSIONS {
        uuid id PK
        uuid user_id FK
        string refresh_token_hash UK
        timestamp expires_at
        json metadata
        timestamp created_at
    }

    API_KEYS {
        uuid id PK
        uuid user_id FK
        string key_hash UK
        string name
        timestamp expires_at
        timestamp last_used_at
        boolean active
    }

    CONSENTS {
        uuid id PK
        uuid user_id FK
        string consent_type
        boolean granted
        string version
        timestamp granted_at
        timestamp revoked_at
    }

    AUDIT_LOGS {
        uuid id PK
        uuid user_id FK
        string action
        string category
        json details
        string ip_address
        string user_agent
        timestamp created_at
    }

    DATASETS ||--o{ POLICIES : uses
    DATASETS {
        uuid id PK
        uuid user_id FK
        string name
        string description
        json schema
        string s3_key
        integer row_count
        timestamp created_at
    }

    POLICIES ||--o{ MODELS : contains
    POLICIES ||--o{ DECISIONS : produces
    POLICIES {
        uuid id PK
        uuid user_id FK
        uuid dataset_id FK
        string name
        json config
        string status
        timestamp created_at
        timestamp completed_at
    }

    DECISIONS {
        uuid id PK
        uuid policy_id FK
        uuid scenario_id FK
        string scenario_name
        float delta_yen
        float delta_yen_ci_low
        float delta_yen_ci_high
        float delta_yen_std
        string verdict
        json quality_scores
        json scenario_spec
        json estimator_results
        timestamp created_at
    }

    MODELS {
        uuid id PK
        uuid policy_id FK
        string estimator_type
        json hyperparameters
        json results
        string s3_artifact_key
        float training_duration
        timestamp created_at
    }

    MODELS ||--o{ METRICS : generates
    METRICS {
        uuid id PK
        uuid model_id FK
        timestamp time
        string metric_name
        float value
        json labels
    }

    POLICIES ||--o{ INTERVENTIONS : has
    INTERVENTIONS {
        uuid id PK
        uuid policy_id FK
        string variable
        float value
        json constraints
        float estimated_effect
    }

    MODELS ||--o{ DIAGNOSTICS : produces
    DIAGNOSTICS {
        uuid id PK
        uuid model_id FK
        string diagnostic_type
        json results
        float score
        boolean passed
        timestamp created_at
    }
```

### DECISIONSテーブル詳細説明

**目的**: ScenarioSpec（S0現行 vs S1候補）の比較結果と、Go/Canary/Hold判定を保存する。

**フィールド詳細**:
- `delta_yen`: S1 - S0 の期待Δ¥（円）
- `delta_yen_ci_low` / `delta_yen_ci_high`: 95% 信頼区間
- `delta_yen_std`: Δ¥の標準偏差
- `verdict`: 意思決定判定
  - `"Go"`: リスク低、Δ¥有意にプラス → すぐ実施推奨
  - `"Canary"`: Δ¥プラスだがCI幅広い or 品質スコア中程度 → A/Bテスト推奨
  - `"Hold"`: Overlap低 / IV弱 / RD品質不合格 → 実施非推奨
- `quality_scores`: 品質メトリクス
  ```json
  {
    "overlap_coverage": 0.85,
    "iv_f_stat": 42.3,
    "rd_mccrary_p": 0.12,
    "balance_score": 0.92
  }
  ```
- `scenario_spec`: S0/S1のポリシー定義（再現性のため保存）
- `estimator_results`: 使用した推定器（DR, IPW等）の詳細結果

---

## 用語集とデータモデル対応表

CQOxでは、UI/仕様書/DB/APIで異なる用語が使われることがあるため、以下に統一的な対応表を示します。

| 概念 | v1仕様書での用語 | DBテーブル | v1 API | v2 API | 説明 |
|------|-----------------|-----------|--------|--------|------|
| **データセット** | Dataset | `DATASETS` | `/api/v1/upload` | `/api/v2/datasets` | アップロードされた生データ（Parquet） |
| **シナリオ/ポリシー** | Scenario / Policy | `POLICIES` | `/api/v1/analyze` | `/api/v2/policies` | S0（現行）/ S1（候補）の施策定義 |
| **意思決定カード** | DecisionCard | `DECISIONS` | `/api/v1/results` | - | Δ¥ + verdict (Go/Canary/Hold) |
| **推定器/モデル** | Estimator / Model | `MODELS` | `/api/v1/analyze` | `/api/v2/policies/{id}/offline-learn` | DR, IPW, DiD等の因果推論モデル |
| **診断結果** | Diagnostics | `DIAGNOSTICS` | `/api/v1/diagnostics` | - | Overlap, IV, RD品質チェック |
| **介入計画** | Intervention / Recourse | `INTERVENTIONS` | - | `/api/v2/recourse` | 個客レベル施策（v2のみ） |
| **メトリクス** | Metrics | `METRICS` | `/api/v1/metrics` | `/api/v2/metrics` | 時系列パフォーマンス指標 |
| **実験設計** | Experiment Design | - | - | `/api/v2/experiments` | A/Bテストサンプルサイズ計算（v2のみ） |

### v1 API エンドポイント仕様（標準）

| エンドポイント | メソッド | 目的 | 対応DBテーブル |
|--------------|---------|------|---------------|
| `/api/v1/upload` | POST | データセットアップロード | `DATASETS` |
| `/api/v1/analyze/comprehensive` | POST | 因果推論実行（S0/S1比較） | `POLICIES`, `MODELS`, `DECISIONS` |
| `/api/v1/scenario/run` | POST | ScenarioSpec実行（エイリアス） | `DECISIONS` |
| `/api/v1/results/{job_id}` | GET | DecisionCard取得 | `DECISIONS` |
| `/api/v1/diagnostics/{job_id}` | GET | 品質診断結果取得 | `DIAGNOSTICS` |
| `/api/v1/events/{job_id}` | GET | ジョブ進捗（SSE or ポーリング） | `JOBS` |

### v2 API エンドポイント仕様（追加機能）

| エンドポイント | メソッド | 目的 | 対応DBテーブル |
|--------------|---------|------|---------------|
| `/api/v2/policies` | POST/GET | Policy Lab v2（Pareto frontier） | `POLICIES`, `OFFLINE_POLICY_RUNS` |
| `/api/v2/recourse/{unit_id}` | POST | 個客レベル介入計画（PII非保存） | - (on-the-fly) |
| `/api/v2/experiments/design` | POST | A/Bテストサンプルサイズ計算 | `EXPERIMENT_DESIGNS` |

**重要**: v1とv2は同じData Contractを共用し、同じPostgreSQL/Parquetストレージを使用します。

---

## v1 API詳細仕様とData Contract

### v1プロダクトの目的と位置づけ

**CQOx v1は「施策前のオフラインポリシー評価」を主目的とします。**

- **主目的**: 施策**前**に、S0（現行運用）vs S1（候補ポリシー）を比較し、Δ¥（デルタ円）と Go/Canary/Hold 判定を返す
- **副次用途**: 実施済みキャンペーンの事後評価（ログデータからの因果効果推定）
- **対象ユーザー**: マーケティング責任者、キャンペーンマネージャー、データアナリスト

**v2との関係**:
- v2（Policy Lab / Recourse / Experiment Design）は、v1と同じData Contractを共用するが、API/UI は別名前空間
- v1完成後にv2を追加する段階的展開を前提

---

### Data Contract仕様（v1/v2共通）

#### required_setsの型定義（統一）

**重要**: `required_sets` は `list[list[str]]`（二次元配列）として統一します。

```python
# 正しい型定義
def validate_contract(
    dataset_id: str,
    required_sets: list[list[str]]  # 重ね合わせ可能なルール集合
) -> tuple[bool, list[str]]:
    """
    Data Contract検証

    Args:
        dataset_id: データセットID
        required_sets: 必須カラムセットのリスト
            例: [["y", "treatment"], ["unit_id", "time"]]
            → ["y", "treatment"] AND ["unit_id", "time"] が必要

    Returns:
        (ok, missing): 検証結果と欠損カラムリスト
    """
    pass

# 使用例
ok, missing = validate_contract(
    "dataset-abc",
    required_sets=[
        ["y", "treatment", "unit_id", "time"],  # Base set
        ["propensity_score"]                     # Propensity set（オプション）
    ]
)
```

**Base set 定義**:
- **Outcome set**: `["y"]` - 結果変数（必須）
- **Treatment set**: `["treatment"]` - 介入変数（必須）
- **Unit set**: `["unit_id"]` - 単位ID（必須）
- **Time set**: `["time"]` - 時刻（DiD, RD以外はオプション）

**Estimator別required_sets**:
```python
ESTIMATOR_REQUIRED_SETS = {
    "DR": [["y", "treatment", "unit_id"], ["propensity_score"]],  # Doubly Robust
    "IPW": [["y", "treatment", "unit_id", "propensity_score"]],   # Inverse Propensity Weighting
    "DiD": [["y", "treatment", "unit_id", "time", "post"]],       # Difference-in-Differences
    "IV": [["y", "treatment", "unit_id", "instrument"]],          # Instrumental Variables
    "CF": [["y", "treatment"] + feature_cols],                    # Causal Forest
    "SCM": [["y", "unit_id", "time"]],                            # Synthetic Control
    "RD": [["y", "treatment", "running_variable"]],               # Regression Discontinuity
}
```

---

#### カラムマッピング（Column Mapping）仕様

**目的**: ユーザーのカラム名を標準カラム名にマッピングする。

**保存先**: PostgreSQL の `column_mapping_profiles` テーブル

```sql
CREATE TABLE column_mapping_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,                     -- 例: "KARTE Push通知 v1"
    source_system VARCHAR(100),                     -- 例: "KARTE", "Salesforce"
    mapping_json JSONB NOT NULL,                    -- マッピング定義
    version VARCHAR(20) DEFAULT '1.0',
    tenant_id UUID,                                  -- マルチテナント対応
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_column_mapping_profiles_tenant ON column_mapping_profiles(tenant_id);
CREATE INDEX idx_column_mapping_profiles_source ON column_mapping_profiles(source_system);
```

**mapping_json フォーマット**:
```json
{
  "y": "revenue",
  "treatment": "received_push",
  "unit_id": "user_id",
  "time": "event_timestamp",
  "propensity_score": "ps_model_v1",
  "features": ["age", "gender", "prefecture", "rfm_segment"]
}
```

**API フロー**:
1. POST `/api/v1/upload` → データセットアップロード
2. レスポンスに `candidate_profiles: [{id, name}, ...]` を含む
3. UI側で「既存プロファイルを使う / 新規作成」を選択
4. POST `/api/v1/datasets/{id}/apply-mapping` → マッピング適用

---

### 品質ゲート条件（Quality Gate）

CQOxでは、品質チェックの結果に応じて2段階の判定を行います。

#### レベル1: API 400エラー（契約違反・識別不能 → 走らない）

| 条件 | 説明 | HTTPステータス |
|------|------|----------------|
| 必須カラム欠損 | Base set（y, treatment, unit_id）が揃わない | 400 Bad Request |
| サンプルサイズ不足 | N < N_min（デフォルト1,000行） | 400 Bad Request |
| 型エラー | y が数値型でない、treatment がバイナリでない等 | 400 Bad Request |
| Data Contract違反 | required_setsで指定したカラムが存在しない | 400 Bad Request |

**実装例**:
```python
@router.post("/api/v1/analyze/comprehensive")
async def analyze_comprehensive(request: AnalyzeRequest):
    # Contract検証
    ok, missing = validate_contract(request.dataset_id, required_sets)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail=f"Data Contract violation: missing columns {missing}"
        )

    # サンプルサイズ検証
    df = load_dataset(request.dataset_id)
    if len(df) < 1000:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient sample size: {len(df)} < 1000"
        )

    # 因果推論実行
    result = run_causal_inference(df, request.scenario_spec)
    return result
```

---

#### レベル2: UI 赤札（DecisionCard verdict = Hold → 走るが採用不可）

| 条件 | 説明 | verdict | 理由 |
|------|------|---------|------|
| Overlap coverage < 0.8 | 共通サポート領域が狭い（外挿リスク高） | **Hold** | "Overlap低 → 識別不可" |
| IV F-stat < 10 | 操作変数が弱い（IV推定不可） | **Hold** | "IV弱 → 識別不可" |
| RD McCrary test p < 0.05 | カットオフ周辺でソーティング検出 | **Hold** | "RD品質不合格 → バイアス疑い" |
| Balance score < 0.7 | 共変量バランス不良（DiD前提崩壊） | **Hold** | "Balance不良 → DiD不適" |

**実装例**:
```python
def determine_verdict(
    delta_yen: float,
    delta_yen_ci_low: float,
    delta_yen_ci_high: float,
    quality_scores: dict
) -> str:
    """
    DecisionCard の verdict を決定

    Returns:
        "Go" | "Canary" | "Hold"
    """
    # レベル2: 品質不合格 → Hold
    if quality_scores.get("overlap_coverage", 1.0) < 0.8:
        return "Hold"  # Overlap低
    if quality_scores.get("iv_f_stat", 100) < 10:
        return "Hold"  # IV弱
    if quality_scores.get("rd_mccrary_p", 1.0) < 0.05:
        return "Hold"  # RD品質不合格
    if quality_scores.get("balance_score", 1.0) < 0.7:
        return "Hold"  # Balance不良

    # CI幅をチェック（相対幅）
    ci_width = delta_yen_ci_high - delta_yen_ci_low
    relative_width = ci_width / abs(delta_yen) if delta_yen != 0 else float('inf')

    # Δ¥有意にプラス かつ CI幅狭い → Go
    if delta_yen_ci_low > 0 and relative_width < 0.5:
        return "Go"

    # Δ¥プラスだがCI幅広い → Canary（A/Bテスト推奨）
    if delta_yen > 0:
        return "Canary"

    # Δ¥ゼロまたはマイナス → Hold
    return "Hold"
```

---

#### UI表示例（Decision Card）

```typescript
// DecisionCard レンダリング
const getVerdictBadge = (verdict: string) => {
  switch (verdict) {
    case "Go":
      return <span className="badge bg-green-500">🟢 Go - すぐ実施推奨</span>
    case "Canary":
      return <span className="badge bg-yellow-500">🟡 Canary - A/Bテスト推奨</span>
    case "Hold":
      return <span className="badge bg-red-500">🔴 Hold - 実施非推奨</span>
  }
}

const DecisionCardItem = ({ card }: { card: DecisionCard }) => (
  <div className={`card border-${getVerdictColor(card.verdict)}`}>
    {getVerdictBadge(card.verdict)}
    <h3>{card.scenario_name}</h3>
    <div className="delta-yen">
      Δ¥: {formatYen(card.delta_yen)} ({formatYen(card.delta_yen_ci_low)}〜{formatYen(card.delta_yen_ci_high)})
    </div>
    <div className="metadata">
      チャネル: {card.channel}<br/>
      セグメント: {card.segment}
    </div>
    {card.verdict === "Hold" && (
      <div className="reason text-red-600">
        理由: {card.reason}
      </div>
    )}
  </div>
)
```

---

**重要**: v1とv2は同じData Contractを共用し、同じPostgreSQL/Parquetストレージを使用します。

---

## Kubernetesデプロイメントアーキテクチャ（Enterprise層）

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Ingress Layer"
            INGRESS[Ingress Controller<br/>nginx-ingress]
            CERT[Cert Manager<br/>Let's Encrypt]
        end

        subgraph "Application Namespace"
            subgraph "Frontend Deployment"
                FE_POD1[Frontend Pod 1<br/>Nginx + React]
                FE_POD2[Frontend Pod 2<br/>Nginx + React]
                FE_SVC[Frontend Service<br/>ClusterIP]
                FE_HPA[HPA<br/>2-10 replicas]
            end

            subgraph "Backend Deployment"
                BE_POD1[Backend Pod 1<br/>FastAPI + Uvicorn]
                BE_POD2[Backend Pod 2<br/>FastAPI + Uvicorn]
                BE_POD3[Backend Pod 3<br/>FastAPI + Uvicorn]
                BE_SVC[Backend Service<br/>ClusterIP]
                BE_HPA[HPA<br/>3-20 replicas]
            end

            subgraph "Celery Workers"
                CELERY_POD1[Celery Worker 1]
                CELERY_POD2[Celery Worker 2]
                CELERY_POD3[Celery Worker 3]
                CELERY_HPA[HPA<br/>2-10 replicas]
            end
        end

        subgraph "Data Namespace"
            PG_STATEFUL[PostgreSQL StatefulSet<br/>3 replicas]
            PG_PVC[PersistentVolumeClaim<br/>100Gi SSD]
            PG_SVC[PostgreSQL Service<br/>Headless]

            REDIS_STATEFUL[Redis StatefulSet<br/>3 replicas - Cluster]
            REDIS_PVC[PersistentVolumeClaim<br/>50Gi SSD]
            REDIS_SVC[Redis Service]

            RABBITMQ_STATEFUL[RabbitMQ StatefulSet<br/>3 replicas - Cluster]
            RABBITMQ_PVC[PersistentVolumeClaim<br/>20Gi]
            RABBITMQ_SVC[RabbitMQ Service]
        end

        subgraph "Monitoring Namespace"
            PROM_DEPLOY[Prometheus Deployment]
            PROM_PVC[PVC - 200Gi]
            GRAFANA_DEPLOY[Grafana Deployment]
            LOKI_DEPLOY[Loki Deployment]
            JAEGER_DEPLOY[Jaeger Deployment]
        end

        subgraph "Configuration"
            CONFIGMAP[ConfigMaps<br/>App Configuration]
            SECRETS[Secrets<br/>Credentials]
            VAULT_AGENT[Vault Agent<br/>Injector]
        end
    end

    INTERNET[Internet] --> INGRESS
    INGRESS --> CERT
    INGRESS --> FE_SVC
    INGRESS --> BE_SVC

    FE_SVC --> FE_POD1
    FE_SVC --> FE_POD2
    FE_HPA -.->|Scale| FE_POD1
    FE_HPA -.->|Scale| FE_POD2

    BE_SVC --> BE_POD1
    BE_SVC --> BE_POD2
    BE_SVC --> BE_POD3
    BE_HPA -.->|Scale| BE_POD1
    BE_HPA -.->|Scale| BE_POD2
    BE_HPA -.->|Scale| BE_POD3

    BE_POD1 --> PG_SVC
    BE_POD2 --> PG_SVC
    BE_POD3 --> PG_SVC
    BE_POD1 --> REDIS_SVC
    BE_POD2 --> REDIS_SVC
    BE_POD3 --> REDIS_SVC

    BE_POD1 --> RABBITMQ_SVC
    BE_POD2 --> RABBITMQ_SVC
    BE_POD3 --> RABBITMQ_SVC

    CELERY_POD1 --> RABBITMQ_SVC
    CELERY_POD2 --> RABBITMQ_SVC
    CELERY_POD3 --> RABBITMQ_SVC
    CELERY_HPA -.->|Scale| CELERY_POD1

    CELERY_POD1 --> PG_SVC
    CELERY_POD2 --> PG_SVC
    CELERY_POD3 --> PG_SVC

    PG_SVC --> PG_STATEFUL
    PG_STATEFUL --> PG_PVC
    REDIS_SVC --> REDIS_STATEFUL
    REDIS_STATEFUL --> REDIS_PVC
    RABBITMQ_SVC --> RABBITMQ_STATEFUL
    RABBITMQ_STATEFUL --> RABBITMQ_PVC

    BE_POD1 --> PROM_DEPLOY
    PROM_DEPLOY --> PROM_PVC
    PROM_DEPLOY --> GRAFANA_DEPLOY
    BE_POD1 --> LOKI_DEPLOY
    BE_POD1 --> JAEGER_DEPLOY

    CONFIGMAP -.->|Mount| BE_POD1
    SECRETS -.->|Mount| BE_POD1
    VAULT_AGENT -.->|Inject| SECRETS

    classDef ingress fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef app fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef data fill:#f8bbd0,stroke:#c2185b,stroke-width:2px
    classDef monitor fill:#d1c4e9,stroke:#512da8,stroke-width:2px
    classDef config fill:#fff9c4,stroke:#f57f17,stroke-width:2px

    class INGRESS,CERT ingress
    class FE_POD1,FE_POD2,FE_SVC,FE_HPA,BE_POD1,BE_POD2,BE_POD3,BE_SVC,BE_HPA,CELERY_POD1,CELERY_POD2,CELERY_POD3,CELERY_HPA app
    class PG_STATEFUL,PG_PVC,PG_SVC,REDIS_STATEFUL,REDIS_PVC,REDIS_SVC,RABBITMQ_STATEFUL,RABBITMQ_PVC,RABBITMQ_SVC data
    class PROM_DEPLOY,PROM_PVC,GRAFANA_DEPLOY,LOKI_DEPLOY,JAEGER_DEPLOY monitor
    class CONFIGMAP,SECRETS,VAULT_AGENT config
```

---

## 技術スタック詳細

### Frontend
- **Framework**: React 18.2 with TypeScript 5.2
- **Build Tool**: Vite 5.0
- **Routing**: React Router v6
- **State Management**: TanStack Query (React Query) v5
- **HTTP Client**: Axios 1.6 with JWT interceptors
- **Charts**: Recharts 2.10
- **Testing**: Playwright 1.40 (E2E), Vitest (Unit)
- **Styling**: CSS Modules + Tailwind-compatible utilities
- **Authentication**: JWT with automatic refresh

### Backend
- **Framework**: FastAPI 0.104+ (Python 3.11+)
- **ASGI Server**: Uvicorn with Gunicorn
- **Async ORM**: AsyncPG (PostgreSQL), AioRedis (Redis)
- **Task Queue**: Celery 5.3 with RabbitMQ broker
- **Validation**: Pydantic v2
- **Authentication**: Python-JOSE (JWT), Authlib (OAuth2)
- **Testing**: Pytest 7.4 with pytest-asyncio
- **Integration**: Wolfram Client API

### Storage
- **Primary DB**: PostgreSQL 15 with TimescaleDB extension
- **Cache**: Redis 7 (Cluster mode, 3 nodes)
- **Object Storage**: MinIO (S3-compatible)
- **Secrets**: HashiCorp Vault 1.15
- **Message Queue**: RabbitMQ 3.12 (Cluster mode)

### Observability
- **Metrics**: Prometheus 2.47 + AlertManager
- **Visualization**: Grafana 10.2
- **Logging**: Loki 2.9 + Promtail
- **Tracing**: Jaeger 1.51 (OpenTelemetry compatible)
- **APM**: Custom metrics with Python prometheus-client

### Infrastructure
- **Orchestration**: Kubernetes 1.28+ (EKS/GKE/AKS)
- **GitOps**: ArgoCD 2.9
- **Container Runtime**: Docker 24.0
- **Registry**: GitHub Container Registry (ghcr.io)
- **Load Balancer**: AWS ALB / GCP Load Balancer
- **CDN**: CloudFront / Cloud CDN
- **WAF**: AWS WAF / Cloud Armor

### CI/CD
- **CI**: GitHub Actions
- **CD**: ArgoCD (Declarative GitOps)
- **Security Scanning**: Trivy (containers), Safety (Python), Bandit (SAST)
- **Code Quality**: Black, Flake8, MyPy, ESLint
- **Coverage**: Pytest-cov, Codecov

---

## スケーラビリティ戦略

### 水平スケーリング
- **Frontend**: CDN + Multi-region deployment (2-10 replicas)
- **Backend API**: Auto-scaling based on CPU/Memory (3-20 replicas)
- **Celery Workers**: Queue-based scaling (2-10 replicas)
- **PostgreSQL**: Read replicas (1 primary + 2 read replicas)
- **Redis**: Cluster mode (3 master nodes, 3 replica nodes)

### 垂直スケーリング
- **Database**: Upgradable to larger instance types
- **Cache**: Memory expansion for hot data
- **Workers**: CPU-intensive tasks on compute-optimized nodes

### パフォーマンス最適化
- **Caching Strategy**: Multi-layer (Browser → CDN → Redis → Database)
- **Database Indexing**: B-tree indexes on query fields, GIN indexes for JSON
- **Query Optimization**: Connection pooling (50-200 connections), prepared statements
- **Async I/O**: Non-blocking I/O for all network operations
- **Compression**: Gzip/Brotli for API responses, LZ4 for storage

---

## セキュリティ対策詳細

### 認証・認可
- **JWT**: HS256 (dev), RS256 (prod), 1-hour access token, 7-day refresh token
- **OAuth2**: PKCE flow for Google/GitHub/Microsoft
- **API Keys**: SHA-256 hashed, scoped permissions, rate limited
- **MFA**: TOTP support (future enhancement)

### データ保護
- **Encryption at Rest**: AES-256-GCM for sensitive fields, PostgreSQL TDE
- **Encryption in Transit**: TLS 1.3, HSTS enabled
- **Key Management**: HashiCorp Vault with auto-rotation
- **PII Handling**: Field-level encryption, GDPR-compliant erasure

### アプリケーションセキュリティ
- **Input Validation**: Pydantic models, regex patterns, length limits
- **Output Sanitization**: HTML escaping, JSON encoding
- **CSRF Protection**: SameSite cookies, CSRF tokens
- **XSS Prevention**: Content Security Policy, sanitized outputs
- **SQL Injection**: Parameterized queries only, no raw SQL
- **Rate Limiting**: 100 req/min per IP, exponential backoff

### コンプライアンス
- **GDPR**: Right to access, erasure, portability, consent management
- **Audit Logging**: All data access logged with IP, user agent, timestamp
- **Data Retention**: 90-day log retention, configurable per regulation
- **Consent Tracking**: Granular consent with version control

---

## 災害復旧計画

### バックアップ戦略
- **PostgreSQL**: Daily full backups + WAL archiving (PITR)
- **Redis**: RDB snapshots every 5 minutes, AOF enabled
- **S3 Objects**: Cross-region replication
- **Configuration**: Git-based (ArgoCD), versioned

### RPO/RTO目標
- **RPO (Recovery Point Objective)**: 5 minutes
- **RTO (Recovery Time Objective)**: 15 minutes
- **Backup Retention**: 30 days (production), 7 days (staging)

### 高可用性
- **Multi-AZ Deployment**: All stateful services across 3 availability zones
- **Health Checks**: Kubernetes liveness/readiness probes
- **Auto-healing**: Failed pods automatically restarted
- **Circuit Breaker**: Graceful degradation on dependency failures

---

## 監視・アラート戦略

### 主要メトリクス

#### RED Metrics (Request-level)
- **Rate**: Requests per second by endpoint
- **Errors**: Error rate (4xx, 5xx) with threshold alerts
- **Duration**: p50/p95/p99 latency percentiles

#### Business Metrics
- **Model Training**: Active runs, duration, success rate
- **CAS Score**: Average score across policies
- **Policy ROI**: Distribution and trends
- **User Activity**: DAU/MAU, feature usage

#### Infrastructure Metrics
- **Cache Performance**: Redis hit rate (target: >80%)
- **Database**: Connection pool usage, query latency
- **Storage**: S3 upload rate, disk usage
- **System**: CPU, memory, network I/O

### アラートルール
- **Critical**: Error rate >5%, p95 latency >2s, DB connections >90%
- **Warning**: Error rate >1%, p95 latency >1s, Cache hit rate <70%
- **Info**: Deployment events, scaling events

### ダッシュボード
- **Overview**: High-level system health
- **Detailed**: Comprehensive RED + business + infrastructure metrics
- **Admin**: User management, audit logs, system stats

---

## 将来的な拡張計画

### Phase 2 (Next 6 months)
- **Multi-tenancy**: Organization-level isolation
- **Advanced Analytics**: Real-time streaming with Apache Kafka
- **ML Model Registry**: MLflow integration
- **A/B Testing**: Feature flags with LaunchDarkly

### Phase 3 (Next 12 months)
- **Global Deployment**: Multi-region active-active
- **GraphQL API**: Apollo Server for flexible queries
- **WebSocket**: Real-time updates with Socket.IO
- **Mobile Apps**: Native iOS/Android apps

### Phase 4 (Future)
- **AI-powered Recommendations**: GPT-4 integration
- **Federated Learning**: Privacy-preserving model training
- **Blockchain Integration**: Immutable audit trail
- **Quantum-ready Encryption**: Post-quantum cryptography

---

## エンタープライズ級運用仕様

### A. 分散ジョブ実行・一貫性

#### ジョブのIdempotency（冪等性）

**Idempotency-Key発行ポリシー**
```python
# API リクエスト時にクライアントが生成
Idempotency-Key: <client_request_id>_<timestamp>_<hash(payload)>

# または、サーバー側で job_id として生成
job_id = f"{user_id}_{policy_id}_{created_at_unix}_{uuid4().hex[:8]}"
```

**重複リクエストの処理**
- 同じ `Idempotency-Key` での再リクエスト → 既存のjob_id/結果を返す（新規作成しない）
- DB制約: `UNIQUE(idempotency_key)` on `jobs` テーブル
- Redis キャッシュ: Key: `idempotency:{key}`, Value: `{job_id}`, TTL: 24時間

#### Celery/RabbitMQリトライポリシー

**リトライ設定**
```python
# Celery Task Configuration
@app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # 初回: 60秒後
    autoretry_for=(NetworkError, WolframTimeoutError),
    retry_backoff=True,      # 指数バックオフ有効
    retry_backoff_max=600,   # 最大10分
    retry_jitter=True        # ジッタ追加
)
def train_policy_task(self, policy_id, dataset_id):
    try:
        # 処理
        pass
    except SoftTimeLimit:
        # タイムアウト時はDLQへ
        self.request.delivery_info['routing_key'] = 'dead_letter'
        raise
```

**Dead Letter Queue (DLQ)**
- 3回リトライ後も失敗 → `celery.dead_letter` キューへ送信
- DLQメッセージは24時間保持 → 手動調査・再投入
- Grafanaでアラート: DLQ深度 > 10

#### ジョブ状態遷移

**有限状態機械（FSM）**
```
queued → running → [succeeded | failed | canceled | timeout]
   ↓         ↓
 canceled  paused → running
```

**状態管理**
```sql
-- jobs テーブル
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    idempotency_key VARCHAR(255) UNIQUE NOT NULL,
    user_id UUID NOT NULL,
    policy_id UUID,
    status VARCHAR(20) NOT NULL, -- queued, running, succeeded, failed, canceled, timeout
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INT DEFAULT 0,
    metadata JSONB
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_user_id ON jobs(user_id);
```

**整合性保証**
1. Celery タスク開始時: DB更新 (`queued` → `running`)
2. 処理中: 進捗をRedisに記録（`progress:{job_id}` = 45%）
3. 完了時: DB更新 (`running` → `succeeded`) + Redis削除 + キャッシュ更新
4. API応答: DBから最新状態を取得（Redis キャッシュは補助）

#### 分散ロック・競合制御

**Redis ベース分散ロック**
```python
from redis.lock import Lock

def train_policy_with_lock(policy_id):
    lock_key = f"lock:policy:{policy_id}"
    lock = redis_client.lock(lock_key, timeout=3600, blocking_timeout=5)

    if not lock.acquire(blocking=False):
        raise ConflictError(f"Policy {policy_id} is already being trained")

    try:
        # 学習処理
        result = train_model(policy_id)
    finally:
        lock.release()

    return result
```

**DB制約によるロック（代替案）**
```sql
-- 同一policy_idに対して複数のrunning jobを防ぐ
CREATE UNIQUE INDEX idx_jobs_policy_running
ON jobs(policy_id)
WHERE status = 'running';
```

#### キューの優先度とQoS

**Queue分離戦略**
```python
# Celery Queue Configuration
CELERY_TASK_ROUTES = {
    'tasks.train_heavy_model': {'queue': 'heavy', 'priority': 3},
    'tasks.quick_analysis': {'queue': 'quick', 'priority': 9},
    'tasks.ui_response': {'queue': 'realtime', 'priority': 10},
}

# Worker Configuration
# Heavy queue: 2 workers × 4 concurrency
# Quick queue: 4 workers × 8 concurrency
# Realtime queue: 8 workers × 2 concurrency
```

**SLA保証**
- Realtime queue: 95% < 500ms
- Quick queue: 95% < 5秒
- Heavy queue: 95% < 5分

---

### B. データ分散・スキーマ管理

#### データパーティショニング戦略

**TimescaleDBパーティショニング**
```sql
-- 時系列メトリクスのパーティショニング（月次）
CREATE TABLE metrics (
    time TIMESTAMPTZ NOT NULL,
    model_id UUID NOT NULL,
    metric_name VARCHAR(50),
    value DOUBLE PRECISION,
    labels JSONB
);

SELECT create_hypertable('metrics', 'time', chunk_time_interval => INTERVAL '1 month');
CREATE INDEX ON metrics (model_id, time DESC);
```

**S3/Parquetパーティショニング**
```
s3://cqox-data/
  ├── datasets/
  │   ├── tenant_id=org-123/
  │   │   ├── date=2025-01/
  │   │   │   └── dataset-abc.parquet
  │   │   └── date=2025-02/
  │   └── tenant_id=org-456/
  └── models/
      └── policy_id=policy-xyz/
          └── version=v1/
              └── model.pkl
```

**大口顧客対策（データスキュー）**
- tenant_idごとのデータ量監視（Prometheus metrics）
- 閾値超過（> 10GB）→ 専用パーティション作成
- 大口顧客は専用Celery workerプールで処理（queue分離）

#### スキーマバージョニング

**Data Contract バージョン管理**
```yaml
# data_contract.yaml (version: 2.1)
version: "2.1"
dataset_id: "marketing_2025"
schema:
  - name: customer_id
    type: string
    required: true
  - name: spend
    type: float
    range: [0, 1000000]
    unit: USD
  - name: channel  # v2.1で追加
    type: categorical
    values: [email, sms, push, web]
changelog:
  - version: "2.1"
    date: "2025-01-15"
    changes: "Added channel field for multi-channel analysis"
  - version: "2.0"
    date: "2024-12-01"
    changes: "Initial contract for 2025"
```

**Runs テーブルとの紐付け**
```sql
ALTER TABLE jobs ADD COLUMN dataset_schema_version VARCHAR(10);

-- どのバージョンの契約で推定したかを記録
INSERT INTO jobs (id, dataset_id, dataset_schema_version, ...)
VALUES ('job-123', 'dataset-abc', '2.1', ...);
```

#### データライフサイクル・保持期間

**保持ポリシー**
```python
# S3 Lifecycle Policy (Terraform)
resource "aws_s3_bucket_lifecycle_configuration" "cqox_data" {
  rule {
    id     = "archive_old_datasets"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 395  # 13ヶ月保持
    }
  }

  rule {
    id     = "delete_temp_uploads"
    prefix = "temp/"
    expiration {
      days = 7
    }
  }
}
```

**PII マスキング・削除**
```python
# GDPR準拠のデータ削除
async def erase_user_data(user_id: str):
    # 1. Datasets: PII列をマスキング
    await db.execute("""
        UPDATE datasets
        SET customer_id = 'REDACTED',
            email = 'deleted@example.com'
        WHERE user_id = $1
    """, user_id)

    # 2. Audit logs: user_id を匿名化
    await db.execute("""
        UPDATE audit_logs
        SET user_id = NULL,
            ip_address = '0.0.0.0'
        WHERE user_id = $1
    """, user_id)

    # 3. S3オブジェクト削除
    s3_keys = await get_user_s3_keys(user_id)
    for key in s3_keys:
        s3_client.delete_object(Bucket='cqox-data', Key=key)
```

#### 系統（Lineage）とカタログ

**Lineage テーブル設計**
```sql
CREATE TABLE lineage (
    id UUID PRIMARY KEY,
    source_type VARCHAR(50),  -- 'dataset', 'model', 'figure', 'decision_card'
    source_id UUID,
    target_type VARCHAR(50),
    target_id UUID,
    relationship VARCHAR(50), -- 'generated_from', 'used_by', 'derived_from'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Example: dataset → job → model → figure → decision_card
INSERT INTO lineage VALUES
  (gen_uuid(), 'dataset', 'ds-123', 'job', 'job-456', 'used_by', NOW()),
  (gen_uuid(), 'job', 'job-456', 'model', 'model-789', 'generated_from', NOW()),
  (gen_uuid(), 'model', 'model-789', 'figure', 'fig-abc', 'generated_from', NOW()),
  (gen_uuid(), 'figure', 'fig-abc', 'decision_card', 'card-xyz', 'used_by', NOW());
```

**系統追跡API**
```python
# GET /api/lineage/dataset/{dataset_id}
# → そのdatasetから生成されたすべてのモデル・図表を返す
```

---

### C. 分散インフラ・可用性

#### マルチAZ/リージョン戦略

**初期構成（Single Region, Multi-AZ）**
- **EKS/GKE**: 3 Availability Zonesに分散
- **PostgreSQL**: Multi-AZ RDS（Primary + Standby）
- **Redis**: Cluster mode, 3 master nodes × 3 AZs
- **S3**: 自動Multi-AZ冗長化

**将来のMulti-Region戦略（Phase 3）**
- **Active-Passive**: プライマリリージョン（us-east-1）+ DRリージョン（us-west-2）
- **データレプリケーション**: PostgreSQL Cross-Region Read Replica, S3 Cross-Region Replication
- **Failover**: Route53 Health Check → DNSフェイルオーバー（RTO: 5分）

#### 障害ドメイン定義

| 障害ドメイン | 影響範囲 | デグレードモード | 検知方法 |
|-------------|---------|----------------|---------|
| **K8s ノード障害** | 影響Pod（他ノードで再起動） | 一時的な応答遅延 | Kubelet health check |
| **AZ 障害** | 1/3のリソース喪失 | 残り2AZで継続（性能低下） | AWS Health Dashboard |
| **PostgreSQL 障害** | 全API停止 | Read-only mode (Redis cache) | Connection timeout |
| **Redis 障害** | キャッシュ喪失、レート制限不可 | DB直接アクセス（遅延増） | Redis PING失敗 |
| **Wolfram Cloud障害** | モデル学習停止 | 既存結果表示のみ | HTTP timeout (30s) |
| **RabbitMQ 障害** | ジョブキュー停止 | 新規ジョブ拒否（503） | Management API |

**Wolfram障害時のデグレード例**
```python
try:
    result = wolfram_client.causal_graph(data)
except WolframUnavailableError:
    # グレーの"現在利用不可"プレースホルダーを表示
    return {"graph": None, "status": "unavailable", "message": "Wolfram Cloud is temporarily unavailable"}
```

#### バックアップ・リストア手順

**PostgreSQL**
```bash
# 自動バックアップ（AWS RDS）
# - 毎日 3:00 UTC に自動スナップショット
# - トランザクションログ（WAL）を5分ごとにS3にアーカイブ
# - PITR（Point-in-Time Recovery）: 過去35日間の任意時点に復元可能

# 手動スナップショット（重要変更前）
aws rds create-db-snapshot \
  --db-instance-identifier cqox-prod \
  --db-snapshot-identifier cqox-prod-before-migration-$(date +%Y%m%d)

# リストア
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier cqox-prod \
  --target-db-instance-identifier cqox-prod-restored \
  --restore-time 2025-01-15T10:30:00Z
```

**S3オブジェクト**
- **Versioning**: 有効化（削除・上書き時も旧バージョン保持）
- **Cross-Region Replication**: プライマリ（us-east-1） → DR（us-west-2）
- **削除保護**: MFA Delete有効化（本番環境）

**DR手順 RPO/RTO**
- **RPO (Recovery Point Objective)**: 5分（WALアーカイブ間隔）
- **RTO (Recovery Time Objective)**: 15分
  - RDS Standby フェイルオーバー: ~2分
  - EKS Pod再起動: ~5分
  - DNS切り替え: ~3分
  - 動作確認: ~5分

---

### D. マルチテナント・SaaS

#### テナント分離モデル

**採用方式: DB共有 + tenant_id カラム分離**
```sql
-- すべてのテーブルに tenant_id を追加
ALTER TABLE datasets ADD COLUMN tenant_id UUID NOT NULL;
ALTER TABLE policies ADD COLUMN tenant_id UUID NOT NULL;
ALTER TABLE jobs ADD COLUMN tenant_id UUID NOT NULL;

-- Row-Level Security (RLS) で強制分離
ALTER TABLE datasets ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON datasets
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

**API Gatewayレベルでのフィルタリング**
```python
# FastAPI Dependency
async def get_current_tenant(token: TokenData = Depends(get_current_user)) -> str:
    return token.tenant_id

# すべてのクエリでtenant_idをフィルタ
@router.get("/datasets")
async def list_datasets(tenant_id: str = Depends(get_current_tenant)):
    return await db.fetch("SELECT * FROM datasets WHERE tenant_id = $1", tenant_id)
```

**将来のDB per Tenant移行パス（Phase 3）**
- 大口顧客（> 100GB data）は専用DBインスタンスに移行
- `tenant_routing` テーブルで接続先を管理

#### レートリミット・クォータ

**テナント別クォータ設計**
```sql
CREATE TABLE tenant_quotas (
    tenant_id UUID PRIMARY KEY,
    plan VARCHAR(20),  -- 'free', 'pro', 'enterprise'
    max_jobs_per_day INT,
    max_storage_gb INT,
    max_api_calls_per_min INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Example
INSERT INTO tenant_quotas VALUES
  ('tenant-free-001', 'free', 10, 5, 60),
  ('tenant-pro-002', 'pro', 100, 50, 300),
  ('tenant-ent-003', 'enterprise', 1000, 500, 1000);
```

**レート制限実装（Redis + Lua）**
```python
# Sliding Window Rate Limiter
async def check_rate_limit(tenant_id: str, limit: int, window: int = 60):
    key = f"ratelimit:{tenant_id}:{int(time.time() // window)}"
    current = await redis.incr(key)

    if current == 1:
        await redis.expire(key, window)

    if current > limit:
        raise HTTPException(status_code=429, detail={
            "error": "rate_limit_exceeded",
            "limit": limit,
            "window": window,
            "retry_after": window - (int(time.time()) % window)
        })
```

**クォータ超過時の429レスポンス**
```json
{
  "error": "quota_exceeded",
  "message": "Daily job limit reached (10/10). Upgrade to Pro plan for more.",
  "quota": {
    "type": "jobs_per_day",
    "limit": 10,
    "used": 10,
    "reset_at": "2025-01-16T00:00:00Z"
  },
  "upgrade_url": "https://cqox.ai/pricing"
}
```

#### 課金・メータリング

**メータリング対象**
```sql
CREATE TABLE usage_metrics (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    metric_type VARCHAR(50),  -- 'job_run', 'storage_gb_day', 'api_call', 'figure_generation'
    quantity FLOAT NOT NULL,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB
);

-- 日次集計（Celeryタスクで毎日実行）
CREATE TABLE daily_usage_summary (
    tenant_id UUID,
    date DATE,
    total_jobs INT,
    total_api_calls BIGINT,
    avg_storage_gb FLOAT,
    total_figures_generated INT,
    PRIMARY KEY (tenant_id, date)
);
```

**料金プラン例**
```yaml
# pricing.yaml
plans:
  free:
    price: 0
    quotas:
      jobs_per_day: 10
      storage_gb: 5
      api_calls_per_min: 60
  pro:
    price: 100000  # 10万円/月
    quotas:
      jobs_per_day: 100
      storage_gb: 50
      api_calls_per_min: 300
    overages:
      extra_job: 1000  # 1ジョブあたり1,000円
      extra_gb_month: 2000  # 1GB/月あたり2,000円
  enterprise:
    price: 1000000  # 100万円/月
    quotas:
      jobs_per_day: 1000
      storage_gb: 500
      api_calls_per_min: 1000
    custom: true
```

---

### E. セキュリティ・コンプライアンス運用

#### ロール・権限マッピング詳細

**UI Role → API Permission マッピング**

| UI Role | API Permissions | Accessible Endpoints |
|---------|----------------|---------------------|
| **viewer** | `console:read`, `policies:read`, `diagnostics:read` | GET /console/*, GET /policies, GET /diagnostics |
| **analyst** | viewer + `models:write`, `policies:write`, `datasets:write` | POST /policies, POST /datasets, POST /models/train |
| **admin** | analyst + `admin:*` | GET/POST/DELETE /admin/*, DELETE /users/{id} |

**Permission Check実装**
```python
# backend/cqox/api/dependencies.py
PERMISSION_MAP = {
    "GET /api/v1/policies": ["policies:read"],
    "POST /api/v1/policies": ["policies:write"],
    "DELETE /api/v1/policies/{id}": ["policies:delete", "admin:all"],
}

def require_permission(required: List[str]):
    def dependency(token: TokenData = Depends(get_current_user)):
        user_permissions = set(token.permissions)
        if not any(perm in user_permissions for perm in required):
            raise HTTPException(403, detail=f"Missing permission: {required}")
        return token
    return Depends(dependency)
```

#### 監査ログスキーマ詳細

**audit_logs テーブル拡張**
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    tenant_id UUID NOT NULL,
    user_id UUID,
    action VARCHAR(100) NOT NULL,  -- 'READ_POLICY', 'CREATE_JOB', 'DELETE_USER'
    resource_type VARCHAR(50),     -- 'policy', 'dataset', 'job', 'user'
    resource_id UUID,
    endpoint VARCHAR(255),         -- '/api/v1/policies/123'
    method VARCHAR(10),            -- 'GET', 'POST', 'DELETE'
    status_code INT,               -- 200, 403, 500
    ip_address INET,
    user_agent TEXT,
    request_id UUID,               -- X-Request-ID header
    details JSONB,                 -- { "policy_id": "...", "changes": {...} }
    reason TEXT                    -- GDPRletetion理由など
);

CREATE INDEX idx_audit_logs_tenant_time ON audit_logs(tenant_id, timestamp DESC);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, timestamp DESC);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
```

**何を記録するか（詳細ルール）**
- **READ操作**: 個客レベルデータのみログ（集計データは除外）
- **WRITE操作**: すべてログ（誰が何をいつ作成・更新・削除したか）
- **DELETE操作**: 削除前の状態をJSONBで保存
- **GDPR削除**: 理由（reason）を必須記録

**個客レベルデータの保存禁止ポリシー**
```python
# ポリシー: 個客レベルuplift/Δ¥は保存しない
# × Bad: 個客IDと紐付けて保存
# ○ Good: セグメント集計のみ保存

# Bad Example (禁止)
await db.execute("""
    INSERT INTO individual_uplifts (customer_id, uplift, delta_revenue)
    VALUES ($1, $2, $3)
""", customer_id, uplift, delta_revenue)

# Good Example (許可)
segment_summary = {
    "segment": "high_value_customers",
    "count": 1523,
    "avg_uplift": 0.23,
    "total_delta_revenue": 450000,
    "p25": 0.15,
    "p50": 0.21,
    "p75": 0.29
}
await db.execute("""
    INSERT INTO segment_summaries (policy_id, segment_name, summary)
    VALUES ($1, $2, $3)
""", policy_id, segment_name, segment_summary)
```

#### キー管理・ローテーション

**Vault パス構成**
```
secret/
├── cqox/
│   ├── prod/
│   │   ├── database/
│   │   │   ├── master_password
│   │   │   └── read_replica_password
│   │   ├── jwt/
│   │   │   ├── private_key (RS256)
│   │   │   └── public_key
│   │   ├── api_keys/
│   │   │   ├── wolfram_api_key
│   │   │   └── smtp_password
│   │   └── encryption/
│   │       └── aes_256_key (field-level encryption)
│   └── staging/
│       └── ...
```

**自動ローテーション周期**
```yaml
rotation_policy:
  jwt_signing_key: 90_days
  database_passwords: 180_days
  api_keys: 365_days
  encryption_keys: never  # 手動ローテーションのみ（データ再暗号化必要）
```

**ローテーション手順（例: JWT鍵）**
```bash
# 1. 新しい鍵ペア生成
openssl genrsa -out new_private.pem 4096
openssl rsa -in new_private.pem -pubout -out new_public.pem

# 2. Vaultに新鍵を追加（旧鍵は残す）
vault kv put secret/cqox/prod/jwt/private_key_v2 value=@new_private.pem
vault kv put secret/cqox/prod/jwt/public_key_v2 value=@new_public.pem

# 3. アプリケーションを新鍵で起動（旧鍵も検証用に保持）
# 4. 7日後、旧鍵で発行されたトークンが失効したら旧鍵削除
```

#### データマスキング・プレビュー

**UI上のマスキングルール**
```typescript
// frontend/src/utils/masking.ts
export function maskCustomerId(customerId: string, role: string): string {
  if (role === 'admin') return customerId;  // admin は全表示
  if (role === 'analyst') return customerId.slice(0, 4) + '****';  // 先頭4文字のみ
  return '****';  // viewer は完全マスキング
}

export function maskEmail(email: string, role: string): string {
  if (role === 'admin') return email;
  const [local, domain] = email.split('@');
  return `${local[0]}***@${domain}`;
}
```

**サンプルデータダウンロード制限**
```python
# GET /api/datasets/{id}/preview
@router.get("/{dataset_id}/preview")
async def preview_dataset(
    dataset_id: str,
    limit: int = Query(100, le=1000),
    user: TokenData = Depends(require_permission(["datasets:read"]))
):
    # 1. 最大1000行まで
    # 2. PII列はマスキング
    # 3. ダウンロードは監査ログに記録

    data = await fetch_dataset(dataset_id, limit=min(limit, 1000))
    masked_data = mask_pii_columns(data, user.roles)

    await audit_log(
        user_id=user.sub,
        action="PREVIEW_DATASET",
        resource_id=dataset_id,
        details={"rows_returned": len(masked_data)}
    )

    return masked_data
```

---

### F. SRE・運用

#### SLO/SLI/エラーバジェット

**定義されたSLO**

| Service | SLI | SLO Target | Error Budget (30日) |
|---------|-----|-----------|-------------------|
| **API Success Rate** | `(2xx + 3xx) / total` | 99.5% | 0.5% = 216分 |
| **API P95 Latency** | 95パーセンタイルレスポンス時間 | < 1秒 | - |
| **Job Completion Rate** | `succeeded / (succeeded + failed)` | 99.0% | 1.0% |
| **Job P95 Duration** | 重い学習ジョブの95パーセンタイル | < 5分 | - |

**Prometheusメトリクス**
```python
# backend/cqox/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# API成功率
api_requests_total = Counter(
    'cqox_api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

# APIレイテンシ
api_request_duration = Histogram(
    'cqox_api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# ジョブ完了率
job_completion_total = Counter(
    'cqox_job_completion_total',
    'Total job completions',
    ['status']  # succeeded, failed, timeout
)

# ジョブ実行時間
job_duration = Histogram(
    'cqox_job_duration_seconds',
    'Job execution duration',
    ['job_type'],  # train_model, run_diagnostics, etc.
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800]
)
```

**エラーバジェット消費アラート**
```yaml
# prometheus/alerts/slo.yaml
groups:
  - name: slo_alerts
    rules:
      - alert: ErrorBudgetBurn
        expr: |
          (
            1 - (sum(rate(cqox_api_requests_total{status_code=~"2.."}[30d]))
                 / sum(rate(cqox_api_requests_total[30d])))
          ) > 0.005
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "API error budget exceeded (> 0.5%)"
          description: "Current error rate: {{ $value | humanizePercentage }}"
```

#### Runbook・インシデント対応

**主要インシデントシナリオ**

**1. ジョブキューが溜まる**
```markdown
### Symptom
- Celery queue depth > 1000
- Job wait time > 30分

### Diagnosis
1. Check worker status: `celery -A cqox inspect active`
2. Check RabbitMQ queue depth: `rabbitmqctl list_queues`
3. Check worker logs for errors

### Resolution
- Immediate: Scale up Celery workers (HPA or manual)
  ```bash
  kubectl scale deployment celery-worker --replicas=20
  ```
- Root cause:
  - If Wolfram timeout → Increase timeout / Add retry
  - If memory leak → Restart workers
  - If traffic spike → Review autoscaling policy
```

**2. Redis障害**
```markdown
### Symptom
- Cache hit rate drops to 0%
- Rate limiting fails
- Session validation errors

### Diagnosis
1. Check Redis cluster status: `redis-cli cluster info`
2. Check Redis logs: `kubectl logs -n data redis-0`
3. Check network: `kubectl exec -it backend-0 -- redis-cli ping`

### Resolution
- Immediate:
  - Failover to replica: AWS ElastiCache auto-failover (~2min)
  - API continues with degraded performance (direct DB access)
- Manual:
  ```bash
  # Force manual failover
  redis-cli -c cluster failover
  ```
```

**3. Wolfram Cloudタイムアウト**
```markdown
### Symptom
- Job failures with "WolframTimeoutError"
- Grafana: Wolfram API P95 latency > 60s

### Diagnosis
1. Check Wolfram Cloud status: https://status.wolfram.com
2. Check our API key quota: Wolfram dashboard
3. Review recent job sizes (large datasets?)

### Resolution
- Immediate:
  - Return cached results for existing policies
  - Defer new jobs to queue for retry (max 3 retries)
- Mitigation:
  - Increase timeout: 30s → 90s
  - Reduce dataset size sent to Wolfram
  - Contact Wolfram support if persistent
```

**Slack/PagerDuty通知設定**
```yaml
# alertmanager/config.yaml
route:
  group_by: ['alertname', 'severity']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'slack-critical'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
    - match:
        severity: warning
      receiver: 'slack-warnings'

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<pagerduty_integration_key>'
  - name: 'slack-critical'
    slack_configs:
      - api_url: '<slack_webhook_url>'
        channel: '#cqox-alerts-critical'
        title: '🚨 {{ .GroupLabels.alertname }}'
  - name: 'slack-warnings'
    slack_configs:
      - api_url: '<slack_webhook_url>'
        channel: '#cqox-alerts-warnings'
        title: '⚠️  {{ .GroupLabels.alertname }}'
```

#### ローリングアップデート・ロールバック

**ArgoCD Rollout戦略**
```yaml
# kubernetes/rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: cqox-backend
spec:
  replicas: 10
  strategy:
    canary:
      steps:
        - setWeight: 10    # 10%のトラフィックを新バージョンへ
        - pause: {duration: 5m}
        - setWeight: 30
        - pause: {duration: 10m}
        - setWeight: 50
        - pause: {duration: 10m}
        - setWeight: 100   # 全トラフィックを新バージョンへ
      analysis:
        templates:
          - templateName: error-rate-check
        args:
          - name: error-rate-threshold
            value: "0.01"  # 1%以上のエラー率でロールバック
  revisionHistoryLimit: 5  # 過去5バージョン保持
```

**自動ロールバック条件**
```yaml
# kubernetes/analysis-template.yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: error-rate-check
spec:
  metrics:
    - name: error-rate
      interval: 1m
      successCondition: result < 0.01
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            sum(rate(cqox_api_requests_total{status_code=~"5.."}[5m]))
            / sum(rate(cqox_api_requests_total[5m]))
```

**手動ロールバック手順**
```bash
# 1. 現在のバージョン確認
kubectl argo rollouts status cqox-backend

# 2. ロールバック（前バージョンへ）
kubectl argo rollouts undo cqox-backend

# 3. 特定のリビジョンへロールバック
kubectl argo rollouts undo cqox-backend --to-revision=3

# 4. ロールバック状況確認
kubectl argo rollouts get rollout cqox-backend --watch
```

**ML/Policy エンジンのカナリアリリースポリシー**
- **新しい推定器**: 必ず10% canaryから開始
- **Policy エンジン更新**: shadow mode（本番に影響させずログのみ）で1週間検証
- **ロールバック可能性**: 過去5バージョンのモデルアーティファクトをS3に保持

---

### G. MLOps・因果モデル運用

#### モデル・Policyレジストリ

**レジストリスキーマ**
```sql
CREATE TABLE model_registry (
    id UUID PRIMARY KEY,
    policy_id UUID NOT NULL,
    version VARCHAR(20) NOT NULL,  -- 'v1.0.0', 'v1.1.0'
    estimator_type VARCHAR(50),
    hyperparameters JSONB,
    training_dataset_id UUID,
    dataset_schema_version VARCHAR(10),
    trained_at TIMESTAMPTZ,
    trained_by UUID,  -- user_id
    s3_artifact_key VARCHAR(500),
    performance_metrics JSONB,  -- {"cas_score": 78.5, "auc": 0.85}
    status VARCHAR(20),  -- 'experimental', 'staging', 'production', 'retired'
    promoted_at TIMESTAMPTZ,
    UNIQUE(policy_id, version)
);

-- Example
INSERT INTO model_registry VALUES (
    gen_random_uuid(),
    'policy-abc',
    'v1.2.0',
    'LinearDML',
    '{"alpha": 0.01, "max_iter": 1000}',
    'dataset-123',
    '2.1',
    '2025-01-15 10:30:00',
    'user-analyst-1',
    's3://cqox-models/policy-abc/v1.2.0/model.pkl',
    '{"cas_score": 82.3, "refutation_passed": true}',
    'production',
    '2025-01-16 09:00:00'
);
```

**バージョニングポリシー**
- **Semantic Versioning**: `v{major}.{minor}.{patch}`
  - major: 推定器タイプ変更（DML → Causal Forest）
  - minor: ハイパーパラメータ重要変更
  - patch: 軽微な調整・バグ修正
- **Promotion Flow**: experimental → staging → production
- **Production制約**: 同時に1バージョンのみproduction（Blue-Green）

#### Shadow評価・オフライン検証

**Shadow Mode実装**
```python
# 新しいモデルをshadow modeで実行（本番トラフィックに影響なし）
@router.post("/policies/{policy_id}/shadow-eval")
async def shadow_evaluate(
    policy_id: str,
    new_model_version: str,
    user: TokenData = Depends(require_permission(["admin:all"]))
):
    # 1. 本番トラフィックログをS3から取得
    production_data = await s3.get_object(
        Bucket='cqox-logs',
        Key=f'traffic/{policy_id}/last_7_days.parquet'
    )

    # 2. 現行モデル（production）で予測
    current_model = await get_production_model(policy_id)
    current_predictions = current_model.predict(production_data)

    # 3. 新モデル（shadow）で予測
    shadow_model = await load_model_version(policy_id, new_model_version)
    shadow_predictions = shadow_model.predict(production_data)

    # 4. 差分を計算・記録
    delta_metrics = compare_predictions(current_predictions, shadow_predictions)

    await db.execute("""
        INSERT INTO shadow_eval_results (policy_id, shadow_version, delta_metrics)
        VALUES ($1, $2, $3)
    """, policy_id, new_model_version, delta_metrics)

    return {"status": "shadow_eval_completed", "delta": delta_metrics}
```

**評価メトリクス**
```json
{
  "delta_cas_score": -1.2,
  "delta_avg_uplift": +0.03,
  "prediction_correlation": 0.92,
  "divergence_rate": 0.08,
  "recommended_action": "promote_to_staging"
}
```

#### データドリフト・モデル劣化検知

**Input Feature分布監視**
```sql
-- 日次でfeature分布を記録
CREATE TABLE feature_distributions (
    id UUID PRIMARY KEY,
    policy_id UUID NOT NULL,
    feature_name VARCHAR(100),
    date DATE NOT NULL,
    mean FLOAT,
    std FLOAT,
    p25 FLOAT,
    p50 FLOAT,
    p75 FLOAT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- ドリフト検知用にベースライン期間の統計を保存
CREATE TABLE baseline_distributions (
    policy_id UUID,
    feature_name VARCHAR(100),
    baseline_period_start DATE,
    baseline_period_end DATE,
    mean FLOAT,
    std FLOAT,
    PRIMARY KEY (policy_id, feature_name)
);
```

**ドリフト検知ロジック（Celery定期タスク）**
```python
from scipy.stats import ks_2samp

@celery.task
async def detect_drift():
    policies = await get_active_policies()

    for policy in policies:
        # 1. ベースライン分布を取得
        baseline = await get_baseline_distribution(policy.id)

        # 2. 直近7日間の分布を取得
        recent = await get_recent_distribution(policy.id, days=7)

        # 3. Kolmogorov-Smirnov検定
        for feature in baseline.keys():
            statistic, pvalue = ks_2samp(baseline[feature], recent[feature])

            if pvalue < 0.01:  # 有意水準1%
                # ドリフト検出！
                await send_alert(
                    severity="warning",
                    message=f"Feature drift detected: {feature} in policy {policy.id}",
                    details={"ks_statistic": statistic, "p_value": pvalue}
                )

                # Grafana annotation
                await grafana.create_annotation(
                    text=f"Drift detected: {feature}",
                    tags=["drift", policy.id]
                )
```

**モデル性能劣化検知**
```python
@celery.task
async def detect_model_degradation():
    # 1. 直近30日間のCASスコア推移を取得
    cas_trend = await db.fetch("""
        SELECT date, avg_cas_score
        FROM daily_model_performance
        WHERE policy_id = $1 AND date >= CURRENT_DATE - 30
        ORDER BY date
    """, policy_id)

    # 2. 線形回帰で傾き検出
    from sklearn.linear_model import LinearRegression
    X = np.array([i for i in range(len(cas_trend))]).reshape(-1, 1)
    y = np.array([row['avg_cas_score'] for row in cas_trend])

    model = LinearRegression().fit(X, y)
    slope = model.coef_[0]

    # 3. 負の傾き（劣化傾向）を検出
    if slope < -0.5:  # 月間で-15ポイント以上低下
        await send_alert(
            severity="warning",
            message=f"Model degradation detected for policy {policy_id}",
            details={"monthly_decline": slope * 30}
        )
```

**アラート閾値**
- **Feature Drift**: p-value < 0.01 → Warning
- **CAS Score下降**: 月間 -10ポイント以上 → Warning, -20ポイント以上 → Critical
- **Uplift変化**: ベースラインから±30%以上 → Investigation required

---

### H. フロントエンド分散設計

#### ページング・ストリーミング設計

**サーバーサイドページング API**
```python
# GET /api/policies?page=2&limit=50
@router.get("/policies")
async def list_policies(
    page: int = Query(1, ge=1),
    limit: int = Query(50, le=100),
    user: TokenData = Depends(get_current_user)
):
    offset = (page - 1) * limit

    policies = await db.fetch("""
        SELECT * FROM policies
        WHERE tenant_id = $1
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
    """, user.tenant_id, limit, offset)

    total = await db.fetchval("SELECT COUNT(*) FROM policies WHERE tenant_id = $1", user.tenant_id)

    return {
        "items": policies,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": math.ceil(total / limit)
        }
    }
```

**Cursor-based Pagination（大規模データ向け）**
```python
# GET /api/recourse/individual?cursor=abc123&limit=100
@router.get("/recourse/individual")
async def list_individual_recourse(
    cursor: Optional[str] = None,
    limit: int = Query(100, le=1000)
):
    if cursor:
        decoded_cursor = base64.b64decode(cursor).decode()
        last_id, last_timestamp = decoded_cursor.split('|')
    else:
        last_id, last_timestamp = None, None

    query = """
        SELECT * FROM recourse_results
        WHERE (created_at, id) > ($1, $2)
        ORDER BY created_at, id
        LIMIT $3
    """

    results = await db.fetch(query, last_timestamp, last_id, limit)

    next_cursor = None
    if len(results) == limit:
        last_item = results[-1]
        next_cursor = base64.b64encode(
            f"{last_item['id']}|{last_item['created_at']}".encode()
        ).decode()

    return {
        "items": results,
        "next_cursor": next_cursor
    }
```

**React Query 無限スクロール**
```typescript
// frontend/src/hooks/usePolicies.ts
import { useInfiniteQuery } from '@tanstack/react-query'

export function usePoliciesInfinite() {
  return useInfiniteQuery({
    queryKey: ['policies', 'infinite'],
    queryFn: ({ pageParam = 1 }) =>
      api.get(`/policies?page=${pageParam}&limit=50`),
    getNextPageParam: (lastPage) => {
      const { page, pages } = lastPage.pagination
      return page < pages ? page + 1 : undefined
    },
    staleTime: 5 * 60 * 1000, // 5分
  })
}

// Component
function PolicyList() {
  const { data, fetchNextPage, hasNextPage, isLoading } = usePoliciesInfinite()

  return (
    <div>
      {data?.pages.map((page) =>
        page.items.map((policy) => <PolicyCard key={policy.id} {...policy} />)
      )}
      {hasNextPage && <button onClick={fetchNextPage}>Load More</button>}
    </div>
  )
}
```

#### オンライン・オフライン状態管理

**Network Error時のDegradation**
```typescript
// frontend/src/lib/api.ts
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNABORTED') {
      // ネットワークエラー → キャッシュから返す
      const cachedData = await getCachedResponse(error.config.url)
      if (cachedData) {
        return {
          ...error.config,
          data: cachedData,
          headers: { 'X-From-Cache': 'true' }
        }
      }

      // キャッシュもない → ユーザーに通知
      toast.error('Network error. Showing last known data.')
      throw new NetworkUnavailableError()
    }

    if (error.response?.status === 503) {
      // サービス一時停止 → 静的メッセージ表示
      return {
        data: {
          status: 'unavailable',
          message: 'Service temporarily unavailable. Please try again later.'
        }
      }
    }

    throw error
  }
)
```

**Service Worker でのオフライン対応**
```javascript
// frontend/public/service-worker.js
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse
      }

      return fetch(event.request).catch(() => {
        // Fetch失敗 → フォールバック
        if (event.request.url.includes('/api/')) {
          return new Response(
            JSON.stringify({ error: 'offline', cached: false }),
            { headers: { 'Content-Type': 'application/json' } }
          )
        }
      })
    })
  )
})
```

**React Query のオフライン対応**
```typescript
// frontend/src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query'
import { persistQueryClient } from '@tanstack/react-query-persist-client'
import { createSyncStoragePersister } from '@tanstack/query-sync-storage-persister'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      cacheTime: 24 * 60 * 60 * 1000, // 24時間
      networkMode: 'offlineFirst', // オフライン時はキャッシュ優先
    },
  },
})

const persister = createSyncStoragePersister({
  storage: window.localStorage,
})

persistQueryClient({
  queryClient,
  persister,
  maxAge: 24 * 60 * 60 * 1000,
})
```

#### URL ベース状態同期

**URL State Management**
```typescript
// frontend/src/pages/PolicyLab.tsx
import { useSearchParams } from 'react-router-dom'

export function PolicyLab() {
  const [searchParams, setSearchParams] = useSearchParams()

  // URL から状態を復元
  const currentTab = searchParams.get('tab') || 'overview'
  const coverage = parseFloat(searchParams.get('coverage') || '0.5')
  const selectedPolicyId = searchParams.get('policy_id')

  const updateTab = (newTab: string) => {
    setSearchParams((prev) => {
      prev.set('tab', newTab)
      return prev
    })
  }

  const updateCoverage = (newCoverage: number) => {
    setSearchParams((prev) => {
      prev.set('coverage', newCoverage.toString())
      return prev
    })
  }

  // URLが共有可能 → 同僚が同じ状態で開ける
  const shareableUrl = `${window.location.origin}/policy-lab?tab=${currentTab}&coverage=${coverage}&policy_id=${selectedPolicyId}`

  return (
    <div>
      <Tabs value={currentTab} onChange={updateTab}>
        <Tab value="overview">Overview</Tab>
        <Tab value="compare">Compare</Tab>
        <Tab value="diagnostics">Diagnostics</Tab>
      </Tabs>

      <CoverageSlider value={coverage} onChange={updateCoverage} />

      {currentTab === 'compare' && (
        <PolicyComparison coverage={coverage} policyId={selectedPolicyId} />
      )}

      <button onClick={() => navigator.clipboard.writeText(shareableUrl)}>
        📋 Copy Shareable Link
      </button>
    </div>
  )
}
```

**Recourse Panel の URL 状態**
```
/recourse?unit_id=customer-12345&intervention=increase_spend&target_outcome=conversion&coverage=0.3
```

**Experiment Design の URL 状態**
```
/experiments/design?test_type=ab&metric=revenue&mde=0.05&power=0.8&allocation=0.5
```

---

## まとめ

本章では、エンタープライズ級システムとして必須となる以下の仕様を明文化しました：

### A. 分散ジョブ実行
- Idempotency-Key によるジョブ重複防止
- Celery/RabbitMQ の指数バックオフリトライ + DLQ
- 状態遷移の一貫性保証（DB → Redis → API）
- Redis分散ロックによる競合制御
- Queue分離とSLA保証

### B. データ管理
- TimescaleDB/S3 パーティショニング戦略
- Data Contract バージョニングと run との紐付け
- PII マスキング・GDPR削除ポリシー
- Lineage テーブルによる系統追跡

### C. インフラ可用性
- Multi-AZ構成とフェイルオーバー
- 障害ドメイン別のデグレードモード
- RPO 5分/RTO 15分のDR戦略

### D. マルチテナントSaaS
- tenant_id 分離 + Row-Level Security
- テナント別クォータとレート制限
- メータリング・課金設計

### E. セキュリティ運用
- Role → Permission マッピングテーブル
- 監査ログ詳細スキーマ（個客レベルは集計のみ）
- Vault キー管理とローテーション手順

### F. SRE運用
- SLO/SLI定義とエラーバジェット
- Runbook（ジョブキュー/Redis/Wolfram障害時）
- ArgoCD Canary Rollout + 自動ロールバック

### G. MLOps
- モデルレジストリとバージョン管理
- Shadow評価によるオフライン検証
- データドリフト・モデル劣化検知

### H. フロントエンド分散
- Cursor-based Pagination と無限スクロール
- ネットワークエラー時のキャッシュフォールバック
- URL状態同期による再現性担保

---

# Implementation Status & System Integration

**Last Updated**: 2025-11-15

This section documents the complete implementation status of the CQOx enterprise system.

## ✅ Fully Implemented Components

### 1. Backend v2 API (100% Complete)

#### Domain Models (`backend/cqox/models/v2.py`)
- ✅ PolicyConfig with semantic versioning
- ✅ OfflinePolicyRun with Pareto frontier
- ✅ RecoursePlan for individual interventions
- ✅ ExperimentDesign with sample size calculation
- ✅ Complete request/response models with Pydantic validation

#### ML Algorithms (`backend/cqox/ml/`)

**Offline Policy Learning** (`offline_policy_learning.py`):
- ✅ Doubly Robust (DR) estimator
- ✅ Inverse Propensity Weighting (IPW)
- ✅ Direct Method (DM)
- ✅ Bootstrap confidence intervals
- ✅ Pareto frontier optimization
- ✅ Grid search over policy parameters

**Recourse Engine** (`recourse_engine.py`):
- ✅ SLSQP optimization-based recourse
- ✅ Differential evolution for diverse candidates
- ✅ Greedy feature modification
- ✅ Cost functions (L1, L2, custom)
- ✅ Feasibility and actionability scoring

**Experiment Design** (`experiment_design.py`):
- ✅ Sample size calculation (continuous & binary outcomes)
- ✅ Power analysis with curves
- ✅ Sequential testing (O'Brien-Fleming, Pocock)
- ✅ Multi-arm experiments with Bonferroni correction

#### v2 API Routes (`backend/cqox/api/routes/v2/`)

**10 Production-Ready Endpoints**:
1. ✅ POST /v2/policies - Create policy
2. ✅ GET /v2/policies - List policies
3. ✅ GET /v2/policies/{id} - Get policy details
4. ✅ POST /v2/policies/{id}/offline-learn - Run optimization
5. ✅ GET /v2/policies/runs/{run_id} - Get results
6. ✅ POST /v2/recourse/{unit_id} - Individual recourse
7. ✅ POST /v2/recourse/batch - Batch recourse
8. ✅ POST /v2/experiments/design - Design experiment
9. ✅ GET /v2/experiments/{id}/power-analysis - Power curve
10. ✅ POST /v2/experiments/{id}/start - Start experiment

### 2. Distributed Systems Infrastructure (100% Complete)

#### Job Execution (`backend/cqox/core/distributed_jobs.py`)

**Idempotency System**:
```python
# Automatic idempotency key generation
key = f"{task_name}:{sha256(args+kwargs)[:16]}"
# 24-hour result caching in Redis
# Duplicate detection prevents double execution
```

**Job State Machine (FSM)**:
```
PENDING → QUEUED → RUNNING → SUCCEEDED/FAILED/RETRYING
```
- ✅ State validation prevents invalid transitions
- ✅ Redis + PostgreSQL persistence
- ✅ Audit trail for all state changes

**Celery Configuration**:
- ✅ Queue prioritization (realtime=10, light=7, heavy=3)
- ✅ Exponential backoff retry with jitter
- ✅ Dead Letter Queue (DLQ) for permanent failures
- ✅ Max 3 retries per task

**Distributed Locks**:
```python
async with DistributedLock(f"policy:{policy_id}", timeout=300):
    # Critical section - prevents concurrent execution
    # Redis SET NX EX implementation
    # Automatic timeout prevents deadlocks
```

#### Multi-Tenancy (`backend/cqox/core/multi_tenancy.py`)

**Tenant Isolation**:
```sql
-- PostgreSQL Row-Level Security
SET LOCAL app.current_tenant_id = :tenant_id;
-- All queries automatically filtered
```

**Rate Limiting** (Redis Sliding Window):
```python
# Accurate sliding window implementation
# Sorted set with timestamp scores
ZREMRANGEBYSCORE key -inf (now - window)  # Remove old
ZCARD key  # Count current requests
ZADD key timestamp timestamp  # Add new
# Burst allowance: limit × 1.5
# 429 response with Retry-After header
```

**Quotas by Plan**:
| Resource | FREE | PRO | ENTERPRISE |
|----------|------|-----|------------|
| Storage | 1GB | 50GB | 1TB |
| Datasets | 3 | 50 | 1000 |
| Jobs/day | 10 | 100 | 10000 |
| API calls/min | 10 | 100 | 1000 |
| v2 Features | ❌ | ✅ | ✅ |

### 3. MLOps (`backend/cqox/mlops/model_registry.py`)

**Semantic Versioning**:
```
MAJOR.MINOR.PATCH
- MAJOR: Feature set or algorithm change
- MINOR: Compatible improvements
- PATCH: Bug fixes

Auto-versioning logic:
- Features changed → major++
- Algorithm changed → major++
- Same features/algo → minor++
```

**Model Lifecycle**:
```
TRAINING → STAGED → PRODUCTION → ARCHIVED
```

**Drift Detection**:
1. **Kolmogorov-Smirnov Test**:
   - Tests if distributions differ
   - Alert when p < 0.05

2. **Population Stability Index (PSI)**:
   ```
   PSI = Σ (p_current - p_ref) × ln(p_current / p_ref)
   
   PSI < 0.1:     No change
   0.1 ≤ PSI < 0.2: Moderate change
   PSI ≥ 0.2:     Retrain recommended!
   ```

3. **Performance Degradation**:
   ```python
   # Linear regression on metrics over time
   # Alert if slope < -1%/day with p < 0.05
   ```

**Shadow Evaluation**:
- ✅ Run new model alongside production
- ✅ Compare predictions without affecting decisions
- ✅ Recommend promotion if improvement > 5%

### 4. Kubernetes & Deployment (100% Complete)

#### Argo Rollouts (`k8s/base/rollout.yaml`)

**5-Step Canary Deployment**:
```
10% → 25% → 50% → 75% → 100%
Pause at each step for analysis
```

**Features**:
- ✅ Traffic routing via NGINX Ingress
- ✅ Header-based canary: `X-Canary: true`
- ✅ Init containers for DB migrations
- ✅ Analysis templates for automatic rollback

#### Horizontal Pod Autoscaling:
```yaml
metrics:
  - CPU: 70% target
  - Memory: 80% target
  - Custom: 1000 req/s per pod

minReplicas: 3
maxReplicas: 20

Scale up: Immediate, max 100% or 4 pods
Scale down: 5-min cooldown, max 50% reduction
```

#### Celery Workers:
- ✅ Heavy queue: 3 replicas, 2 concurrency, 1-4GB memory
- ✅ Light queue: 5 replicas, 4 concurrency, 512MB-2GB memory
- ✅ Realtime queue: 10 replicas, 10 concurrency, 256MB-1GB memory
- ✅ Auto-scaling based on queue depth

### 5. Monitoring & SLO (`monitoring/prometheus/slo-alerts.yaml`)

#### SLO Definitions:

**API Availability: 99.5%**
```yaml
Error Budget: 0.5%

Fast Burn Alert (1-min window):
  - Success rate < 95%
  - Burning 10× error budget

Slow Burn Alert (30-min window):
  - Success rate < 98.5%
  - Sustained degradation

Monthly Budget Exhausted:
  - Error rate > 0.5% over 30 days
```

**API Latency**:
- P95 < 500ms
- P99 < 1000ms

**Job Completion**:
- Policy training P95 < 5 minutes

#### ML-Specific Alerts:
```yaml
# Data Drift
alert: ModelDataDrift
expr: cqox_model_psi_score > 0.2

# Model Degradation
alert: ModelPerformanceDegradation
expr: cqox_model_performance_slope < -0.01
      and cqox_model_performance_pvalue < 0.05
```

### 6. Frontend v2 (100% Complete)

#### Pages:
1. ✅ Policy Lab v2 (`PolicyLabV2.tsx`)
   - Policy creation and optimization
   - Pareto frontier visualization (Recharts scatter plot)
   - Real-time offline learning status
   - Confidence intervals display

2. ✅ Recourse v2 (`RecourseV2.tsx`)
   - Individual intervention generation
   - Cost, feasibility, actionability metrics
   - Feature change visualization
   - Privacy notice (no PII storage)

3. ✅ Experiment Design v2 (`ExperimentDesignV2.tsx`)
   - A/B test configuration
   - Sample size calculation
   - Power curve visualization
   - Multi-arm support

#### Routing:
```tsx
/policy-lab-v2       → PolicyLabV2
/recourse-v2         → RecourseV2
/experiment-design-v2 → ExperimentDesignV2
```

### 7. Database (`backend/migrations/`)

**Complete Schema**:
- ✅ 001_base_schema.sql: Tenants, users, datasets, models, jobs
- ✅ 002_security_and_compliance.sql: Audit logs, encryption
- ✅ 003_v2_policy_learning.sql: v2 tables with RLS

**Row-Level Security (RLS)**:
```sql
CREATE POLICY tenant_isolation ON policy_configs
  USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
```

### 8. Local Development (`docker-compose.yml`)

**Complete Stack**:
- ✅ PostgreSQL (TimescaleDB)
- ✅ Redis
- ✅ RabbitMQ
- ✅ API (FastAPI + hot reload)
- ✅ Celery workers (heavy, light, realtime)
- ✅ MinIO (S3-compatible)
- ✅ Prometheus
- ✅ Grafana
- ✅ Jaeger (distributed tracing)

**Single Command**: `docker-compose up -d`

### 9. Testing (`backend/tests/integration/`)

**Integration Tests**:
- ✅ v2 API endpoints
- ✅ v1/v2 coexistence
- ✅ Authentication
- ✅ Error handling
- ✅ Validation

**Test Coverage**:
- Policy Lab: Create, list, optimize, get results
- Recourse: Individual, batch
- Experiment Design: Create, power analysis
- v1/v2 namespace separation

## Implementation Statistics

| Component | Files | Lines of Code | Status |
|-----------|-------|---------------|--------|
| Backend v2 API | 3 | 3,618 | ✅ Complete |
| ML Algorithms | 3 | 2,500 | ✅ Complete |
| Distributed Systems | 2 | 1,200 | ✅ Complete |
| MLOps | 1 | 600 | ✅ Complete |
| Frontend v2 | 3 | 2,100 | ✅ Complete |
| Kubernetes | 4 | 800 | ✅ Complete |
| Monitoring | 2 | 500 | ✅ Complete |
| Database | 3 | 600 | ✅ Complete |
| Tests | 1 | 350 | ✅ Complete |
| **Total** | **22** | **12,268** | **✅ 100%** |

## Production Readiness Checklist

- [x] API v2 endpoints with proper validation
- [x] Database migrations with RLS
- [x] Distributed job execution with idempotency
- [x] Multi-tenancy with quotas and rate limiting
- [x] MLOps with versioning and drift detection
- [x] Kubernetes deployment with canary rollouts
- [x] Monitoring with SLO-based alerts
- [x] Frontend pages for all v2 features
- [x] Integration tests
- [x] Docker Compose for local dev
- [x] Documentation (this file)

## Deployment Instructions

### Local Development:
```bash
# Start entire stack
docker-compose up -d

# Access services:
# - API: http://localhost:8000
# - Frontend: http://localhost:3000
# - Grafana: http://localhost:3001
# - Prometheus: http://localhost:9090
# - RabbitMQ: http://localhost:15672
# - Jaeger: http://localhost:16686
```

### Production Deployment:
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/base/

# Monitor rollout
kubectl argo rollouts get rollout cqox-api -n cqox-production

# Check status
kubectl get pods -n cqox-production
kubectl get svc -n cqox-production
```

### Database Migrations:
```bash
# Run migrations
alembic upgrade head

# Or via Docker:
docker-compose exec api alembic upgrade head
```

## Next Steps (Optional Enhancements)

While the system is production-ready, these optional enhancements can be added:

1. **E2E Tests**: Playwright/Cypress tests for complete workflows
2. **Load Tests**: Locust scripts for performance validation
3. **CI/CD Pipeline**: GitHub Actions / ArgoCD GitOps
4. **Advanced Monitoring**: Custom Grafana dashboards with business metrics
5. **Backup/Restore**: Automated PostgreSQL backups to S3
6. **Multi-Region**: Cross-region replication for HA

## Architecture Principles Applied

This implementation follows enterprise-grade principles:

✅ **Idempotency**: All operations are idempotent  
✅ **Observability**: Metrics, logs, traces everywhere  
✅ **Scalability**: Horizontal scaling with HPA  
✅ **Resilience**: Retries, circuit breakers, graceful degradation  
✅ **Security**: RLS, rate limiting, authentication, encryption  
✅ **Testability**: Integration tests, local dev environment  
✅ **Maintainability**: Semantic versioning, shadow evaluation, canary deployments  

