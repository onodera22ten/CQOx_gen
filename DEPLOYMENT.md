# CQOx デプロイメントガイド

## 📦 本番環境デプロイ

### 前提条件
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM以上
- 20GB ディスク空き容量

### 環境変数設定

```bash
# .env.production
DATABASE_URL=postgresql+asyncpg://cqox:SECURE_PASSWORD@postgres:5432/cqox_prod
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=amqp://cqox:SECURE_PASSWORD@rabbitmq:5672//

# セキュリティ
JWT_SECRET_KEY=GENERATE_SECURE_RANDOM_KEY_HERE
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# OAuth2 (オプション)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# CORS
CORS_ORIGINS=["https://your-domain.com"]

# ログ
LOG_LEVEL=INFO
```

### デプロイ手順

```bash
# 1. リポジトリをクローン
git clone <repository-url>
cd CQOx_gen

# 2. 環境変数を設定
cp .env.example .env.production
# .env.production を編集

# 3. 本番ビルド
docker compose -f docker-compose.prod.yml build

# 4. データベース初期化
docker compose -f docker-compose.prod.yml up -d postgres
docker compose -f docker-compose.prod.yml exec postgres psql -U cqox -d cqox_prod -f /docker-entrypoint-initdb.d/init.sql

# 5. 全サービス起動
docker compose -f docker-compose.prod.yml up -d

# 6. ヘルスチェック
curl http://localhost:8000/health
```

### SSL/TLS設定 (Nginx)

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;
    
    # API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Frontend
    location / {
        proxy_pass http://localhost:3004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔒 セキュリティチェックリスト

- [ ] JWT_SECRET_KEY を強力なランダム値に変更
- [ ] データベースパスワードを変更
- [ ] RabbitMQパスワードを変更
- [ ] HTTPS/TLSを有効化
- [ ] CORS設定を本番ドメインに制限
- [ ] ファイアウォール設定（必要なポートのみ開放）
- [ ] Rate Limitingを有効化
- [ ] ログ監視を設定
- [ ] バックアップ戦略を確立

## 📊 モニタリング

### ヘルスチェック
```bash
# API
curl http://localhost:8000/health

# Celery Worker
docker compose exec celery_worker celery -A cqox.tasks.celery_app inspect active

# PostgreSQL
docker compose exec postgres pg_isready

# Redis
docker compose exec redis redis-cli ping
```

### ログ確認
```bash
# 全ログ
docker compose logs -f

# APIログ
docker compose logs api -f --tail=100

# Celeryログ
docker compose logs celery_worker -f --tail=100
```

### メトリクス
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Jaeger UI: http://localhost:16686

## 🔄 バックアップ・リストア

### データベースバックアップ
```bash
# バックアップ
docker compose exec postgres pg_dump -U cqox cqox_prod > backup_$(date +%Y%m%d).sql

# リストア
docker compose exec -T postgres psql -U cqox cqox_prod < backup_20250116.sql
```

### データファイルバックアップ
```bash
# アップロードファイルをバックアップ
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz data/uploads/

# リストア
tar -xzf uploads_backup_20250116.tar.gz
```

## 📈 スケーリング

### 水平スケーリング

```yaml
# docker-compose.scale.yml
services:
  celery_worker:
    deploy:
      replicas: 4  # ワーカー数を増やす
      
  api:
    deploy:
      replicas: 2  # API インスタンス数を増やす
```

```bash
docker compose -f docker-compose.prod.yml -f docker-compose.scale.yml up -d
```

### Kubernetes デプロイ

```bash
# Helm チャートを使用（準備中）
helm install cqox ./charts/cqox \
  --namespace cqox \
  --create-namespace \
  --values values.production.yaml
```

## 🐛 トラブルシューティング

### 1. API起動失敗
```bash
# ログ確認
docker compose logs api --tail=100

# 一般的な原因
# - データベース接続失敗 → DATABASE_URLを確認
# - ポート競合 → 8000番ポートが使用中か確認
```

### 2. Celeryタスクが処理されない
```bash
# ワーカーステータス確認
docker compose exec celery_worker celery -A cqox.tasks.celery_app inspect stats

# RabbitMQキュー確認
docker compose exec rabbitmq rabbitmqctl list_queues
```

### 3. メモリ不足
```bash
# リソース使用状況
docker stats

# 解決策: docker-compose.yml でメモリ制限を調整
services:
  api:
    mem_limit: 2g
  celery_worker:
    mem_limit: 4g
```

## 📞 サポート

- GitHub Issues: <repository-url>/issues
- Email: support@cqox.example.com
- Slack: #cqox-support
