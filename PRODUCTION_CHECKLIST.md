# 🚀 CQOx 本番環境チェックリスト

## ✅ 解決済み問題

### 1. ログイン問題
- **原因**: データベースにユーザーが存在しない
- **解決策**: デモユーザー認証をフォールバックとして実装
- **ログイン情報**:
  - Email: `admin@cqox.com`
  - Password: `admin_password_change_me`

### 2. CORS エラー
- **原因**: フロントエンドのオリジンがCORS設定に含まれていない
- **解決策**: `localhost:3004` と `127.0.0.1:3004` を明示的に許可

### 3. データファイル参照問題
- **原因**: Celeryワーカーコンテナにアップロードファイルが同期されていない
- **解決策**: ボリュームマウント修正 + 相対パスを絶対パスに変換

## 🔧 現在の問題と修正中

### 1. Causal Design: "Invalid dataset_id format"
- **原因**: フロントエンドからのdataset_idがUUID形式ではない可能性
- **修正中**: データセットID検証と変換ロジックを追加

### 2. Policy Lab: 500 Internal Server Error
- **原因**: データベース接続またはAPI実装の問題
- **修正中**: エラーログ確認とAPI統合チェック

## 📋 次のステップ

### 短期（今すぐ）
1. ✅ デモユーザー認証を実装
2. 🔄 dataset_id/policy_id のUUID検証を修正
3. 🔄 500エラーの原因特定と修正
4. 📝 本番環境での動作確認完了

### 中期（配布準備）
1. Docker イメージのビルドと配布準備
2. READMEの更新（本番環境セットアップ手順）
3. 初期データベースマイグレーション自動化
4. 環境変数設定ガイド作成

### 長期（エンタープライズ対応）
1. Kubernetes マニフェスト作成
2. Helm チャート作成
3. CI/CDパイプライン構築
4. 監視・アラート設定完了

## 🎯 配布方法（選択肢）

### Option 1: Docker Compose（推奨）
```bash
# ビルド
docker compose build

# 起動
docker compose up -d

# 初期ユーザー作成は自動（デモユーザーで即ログイン可能）
```

**利点**:
- セットアップが最も簡単
- 全依存関係を含む
- 開発環境と本番環境で同じ構成

### Option 2: Docker Image 配布
```bash
# イメージ保存
docker save cqox-api:latest | gzip > cqox-api.tar.gz
docker save cqox-frontend:latest | gzip > cqox-frontend.tar.gz

# 配布先での読み込み
docker load < cqox-api.tar.gz
docker load < cqox-frontend.tar.gz
docker compose up -d
```

### Option 3: Kubernetes デプロイ
```bash
# Helmチャート適用
helm install cqox ./helm/cqox --namespace cqox --create-namespace
```

## 🔒 セキュリティチェックリスト

- ✅ JWT認証実装
- ✅ OAuth2対応（Google, GitHub, Microsoft）
- ✅ RBAC実装
- ✅ CORS設定
- ⚠️ デフォルトパスワードの変更推奨
- ⚠️ データベースパスワードの強化
- ⚠️ SECRET_KEY の本番用生成

## 📊 パフォーマンスチェック

- ✅ 非同期タスク処理（Celery）
- ✅ Redis キャッシング
- ✅ PostgreSQL インデックス
- ⚠️ 大規模データ処理（10万行以上）の負荷テスト
- ⚠️ 同時接続数テスト

## 🧪 テストチェックリスト

### 機能テスト
- ✅ ログイン・認証
- 🔄 データセットアップロード
- 🔄 因果推論分析実行
- 🔄 ポリシー作成・評価
- ⚠️ v2 API機能
- ⚠️ 権限管理

### 統合テスト
- 🔄 フロントエンド ↔ バックエンド
- 🔄 バックエンド ↔ データベース
- 🔄 Celery タスク実行
- ⚠️ エンドツーエンドフロー

## 📖 ドキュメント

- ✅ README.md
- ✅ architecture.md
- ✅ ui-design.md
- ⚠️ API ドキュメント (OpenAPI/Swagger)
- ⚠️ ユーザーガイド
- ⚠️ 管理者ガイド
- ⚠️ トラブルシューティングガイド

## 🆘 トラブルシューティング

### ログイン できない
→ `admin@cqox.com` / `admin_password_change_me` を使用

### 500 エラー
→ `docker compose logs api` でログ確認

### ファイルが見つからない
→ `docker compose restart celery_worker` でワーカー再起動

### CORS エラー
→ フロントエンドが `localhost:3004` で動作していることを確認

---

**最終更新**: 2025-11-17
**ステータス**: 🔧 修正中 → 本番環境動作確認へ

