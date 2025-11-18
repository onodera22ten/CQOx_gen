# CQOx - Quick Start Guide

## 🚀 システム起動状況

### ✅ 現在稼働中のサービス

| サービス | URL | ログイン情報 |
|---------|-----|-------------|
| **フロントエンド UI** | http://localhost:3004 | 下記参照 |
| **バックエンド API** | http://localhost:8000 | - |
| **API ドキュメント** | http://localhost:8000/docs | - |
| **PostgreSQL** | localhost:5434 | User: `cqox`, Pass: `cqox_dev_password` |
| **Redis** | localhost:6379 | - |
| **RabbitMQ 管理画面** | http://localhost:15672 | User: `cqox`, Pass: `cqox_dev_password` |

---

## 👤 ログイン情報

### ① デフォルトユーザー（Email/Password）

ログイン画面にアクセス: http://localhost:3004/login

| Role | Email | Password | 権限 |
|------|-------|----------|------|
| **Admin** | `admin@cqox.local` | `admin123` | 全機能 + ユーザー管理 |
| **Analyst** | `analyst@cqox.local` | `analyst123` | モデル・ポリシー作成/分析 |
| **Viewer** | `viewer@cqox.local` | `viewer123` | 閲覧のみ |

### アカウント作成について

**新規ユーザーの作成方法：**

1. **✅ サインアップページから作成**（推奨）:
   - http://localhost:3004/signup にアクセス
   - 名前、Email、パスワードを入力
   - 新規アカウントが自動作成されます（デフォルトロール: viewer）

2. **Option 2**: Adminアカウントでログイン → Admin Panel でユーザー作成

3. **Option 3**: デモユーザーを使う（開発用）:
   - 上記のadmin / analyst / viewer アカウント

---

## 🎨 UIテーマ

**ダークテーマ**（モダンなアナリティクスUI風）を採用：
- 背景色: Dark Blue/Gray
- アクセントカラー: Blue, Cyan, Green, Orange, Purple, Pink
- フォント: Inter (本文), Fira Code (コード)
- レスポンシブデザイン対応

---

## 🛠️ RabbitMQ 管理画面

**URL**: http://localhost:15672

**ログイン情報**:
- Username: `cqox`
- Password: `cqox_dev_password`

**用途**:
- Celery タスクキューの監視
- メッセージ配信状況の確認
- ワーカーの健全性チェック

---

## 📊 実装済み機能

### ✅ V1 機能（基本機能）

| 機能 | フロントエンド | バックエンド API | 説明 |
|------|---------------|-----------------|------|
| **Decision Console** | ✅ | ✅ | デルタ円サマリー・意思決定履歴 |
| **Dataset Management** | ✅ | ✅ | データセットアップロード・プレビュー |
| **Policy Management** | ✅ | ✅ | ポリシー作成・実行 |
| **Analysis & Results** | ✅ | ✅ | 因果推論分析結果表示 |
| **Diagnostics** | ✅ | ✅ | バランス・感度分析 |
| **Portfolio & ROI** | ✅ | ⚠️ | ROI分析（部分実装） |
| **Admin Panel** | ✅ | ✅ | ユーザー管理・RBAC |

### ✅ V2 機能（拡張機能）

| 機能 | フロントエンド | バックエンド API | 説明 |
|------|---------------|-----------------|------|
| **Policy Lab V2** | ✅ | ✅ | オフラインポリシー学習・マルチアーム |
| **Recourse V2** | ✅ | ✅ | 反実仮想分析・介入最適化 |
| **Experiment Design V2** | ✅ | ✅ | A/Bテスト設計・サンプルサイズ計算 |
| **Causal Design** | ✅ | ⚠️ | 因果グラフ設計（部分実装） |

---

## 💡 ③ UIで全機能使えるか？

### 🟢 使用可能な機能（ログイン後）

**ログイン直後にアクセス可能**:
- Decision Console（ダッシュボード）
- Dataset Management（データアップロード）
- Policy Lab（ポリシー作成）
- Analysis & Results（分析結果）
- Diagnostics（診断）

**V2機能（メニューから選択）**:
- Policy Lab V2（高度なポリシー最適化）
- Recourse V2（反実仮想シナリオ）
- Experiment Design V2（実験計画）

**Admin機能（Adminロールのみ）**:
- User Management
- System Settings

### 🟡 制限事項

1. **データが必要**：
   - 初回ログイン時はデータセットが空です
   - まず「Dataset Management」でCSVをアップロードしてください

2. **非同期処理**：
   - 分析実行は Celery タスクキューで非同期処理されます
   - 大きなデータセットの場合、完了まで数分かかる場合があります

3. **デモデータ**：
   - サンプルデータセットは `docs/examples/` に格納予定
   - または API で `/api/v1/datasets/sample` からダウンロード可能

---

## 🔧 トラブルシューティング

### バックエンドが起動しない場合

```bash
# ログ確認
journalctl -u cqox-api -f

# 再起動
cd /home/hirokionodera/CQOx_gen/backend
python -m uvicorn cqox.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### フロントエンドが起動しない場合

```bash
# ログ確認
cd /home/hirokionodera/CQOx_gen/frontend
npm run dev
```

### Dockerサービス再起動

```bash
# 全サービス停止
docker compose down

# 再起動
docker compose up -d postgres redis rabbitmq

# ヘルスチェック
docker ps
```

### ログイン失敗する場合

1. **デモユーザーが作成されているか確認**:
   ```bash
   docker exec -i cqox-postgres psql -U cqox -d cqox_dev -c "SELECT email, roles FROM users;"
   ```

2. **再作成**:
   ```bash
   docker exec -i cqox-postgres psql -U cqox -d cqox_dev < backend/scripts/create_demo_user.sql
   ```

---

## 📚 追加リソース

- **アーキテクチャ**: [docs/architecture.md](docs/architecture.md)
- **UI設計**: [docs/ui-design.md](docs/ui-design.md)
- **V2機能**: [docs/CQOx_v2-delta.md](docs/CQOx_v2-delta.md)
- **API仕様**: http://localhost:8000/docs（Swagger UI）
- **Redoc**: http://localhost:8000/redoc

---

## 🎯 推奨ワークフロー

1. **ログイン**: http://localhost:3004/login
   - Email: `admin@cqox.local`
   - Password: `admin123`

2. **データセットアップロード**: Dataset Management
   - CSVファイルをアップロード
   - スキーマを確認

3. **ポリシー作成**: Policy Lab
   - Treatment列、Outcome列を選択
   - Estimator（S-learner, T-learner等）を選択

4. **分析実行**: Analysis & Results
   - ポリシーを実行
   - 因果効果を確認
   - LCB95（信頼区間下限）を確認

5. **意思決定**: Decision Console
   - 結果を比較
   - Delta-Yen（期待値）をベースに意思決定

---

**🎉 全てのサービスが正常に動作しています！**

ご質問があれば、APIドキュメント（http://localhost:8000/docs）を参照するか、`docs/` ディレクトリの仕様書をご覧ください。

