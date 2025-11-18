# CQOx クイックスタートガイド

## 🚀 5分で始める

### 1. システム起動
```bash
cd /home/hirokionodera/CQOx_gen
docker compose up -d
```

### 2. ログイン
- URL: http://localhost:3004/login
- Email: `admin@cqox.local`
- Password: `admin123`

### 3. データアップロード
1. **データ管理** タブをクリック
2. **新規アップロード** ボタン
3. CSVファイルを選択（サンプル: `backend/tests/fixtures/sample_data.csv`）
4. データセット名: 例）`marketing_campaign_test`
5. **アップロード**

### 4. 因果推論分析
1. **Causal Design** タブ
2. アップロードしたデータセットを選択
3. 列を指定:
   - Treatment Column: `treatment`
   - Outcome Column: `outcome`
   - Feature Columns: `x1,x2,x3`
4. Estimators: **DR**, **IPW** を選択
5. **TRAIN MODELS** をクリック
6. 数秒〜数分で結果が表示されます

### 5. 結果確認
- **Causal Design**: 分析ステータスと結果
- **Decision Console**: Δ¥サマリー
- **Policy Lab**: ポリシー一覧
- **Portfolio & ROI**: 集計データ

## 📊 システム構成

### サービス一覧
```bash
docker compose ps
```

- **API** (port 8000): FastAPI バックエンド
- **Celery Worker**: 非同期タスク処理
- **PostgreSQL** (port 5434): データベース
- **Redis** (port 6379): キャッシュ
- **RabbitMQ** (port 15672): メッセージブローカー
- **Frontend** (port 3004): React UI

### ログ確認
```bash
# API
docker compose logs api -f

# Celery Worker
docker compose logs celery_worker -f

# 全サービス
docker compose logs -f
```

## 🔧 トラブルシューティング

### 分析が pending のまま
```bash
# Celery ワーカーを再起動
docker compose restart celery_worker
```

### データベースをリセット
```bash
docker compose exec postgres psql -U cqox -d cqox_dev -c "
DELETE FROM analysis_runs;
DELETE FROM datasets;
"
```

### 全サービス再起動
```bash
docker compose down
docker compose up -d
```

## 📝 デモユーザー

| Email | Password | Role |
|-------|----------|------|
| admin@cqox.local | admin123 | admin |
| analyst@cqox.local | analyst123 | analyst |
| viewer@cqox.local | viewer123 | viewer |

## 🎯 主要機能

### ✅ 実装済み
- データセットアップロード（CSV, 最大100MB）
- 因果推論分析（S-Learner, DR-Learner, T-Learner, X-Learner, Causal Forest）
- 大規模データ処理（100万行対応、バッチ処理）
- Δ¥計算とGo/Canary/Hold判定
- 非同期タスク処理（Celery）
- マルチテナンシー対応
- JWT認証 + OAuth2（Google, GitHub, Microsoft）
- RBAC（Role-Based Access Control）

### 🔄 開発中
- v2 API（Policy Lab, Recourse, Experiment Design）
- 追加MLアルゴリズム（DiD, IV, RD, SCM）
- MLOps（モデルレジストリ, Drift検出）
- 監視（Prometheus, Grafana）
- CI/CD パイプライン

## 📚 技術スタック

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Celery
- **Frontend**: React 18, TypeScript, Tailwind CSS, React Query
- **Database**: PostgreSQL 15 (TimescaleDB), Redis
- **Message Queue**: RabbitMQ
- **Container**: Docker, Docker Compose
- **ML/Causal**: scikit-learn, EconML, CausalML, PyTorch

## 🐛 既知の問題

1. **初回アップロード後、分析失敗**
   - 解決済み：Volume マウント設定を修正

2. **Celery タスクが処理されない**
   - 解決済み：キューのルーティング設定を修正

3. **UUID型エラー**
   - 解決済み：DB/SQLAlchemy/API全層でUUID型を統一

## 💡 ベストプラクティス

1. **データ形式**:
   - CSV (UTF-8推奨)
   - 列名: 英数字とアンダースコア推奨
   - Treatment: 0/1 のバイナリ
   - Outcome: 数値
   - Features: 数値またはカテゴリカル

2. **パフォーマンス**:
   - 小規模（〜10k行）: 10-30秒
   - 中規模（〜100k行）: 1-3分
   - 大規模（1M+行）: 5-15分（自動バッチ処理）

3. **セキュリティ**:
   - 本番環境では環境変数を適切に設定
   - JWT_SECRET_KEY を変更
   - HTTPS を使用
   - データベースパスワードを変更

## 📞 サポート

- 問題報告: GitHub Issues
- ドキュメント: `docs/` ディレクトリ
- アーキテクチャ: `docs/architecture.md`
- UI設計: `docs/ui-design.md`

