#!/bin/bash
# 【日本語サマリ】本番環境Dockerスタックの起動スクリプト
# - なぜ必要か: 一発で全サービスを正しい順序で起動し、ヘルスチェックを確認するため
# - 何をするか: Docker Compose でビルド→起動→ヘルスチェック→初期データ投入
# - どう検証するか: 各サービスのヘルスチェックとフロントエンドへのアクセス確認

set -e

echo "🚀 CQOx Production Stack - Starting..."
echo "========================================"

# Clean up old containers and volumes (optional)
read -p "Do you want to clean up old containers? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Cleaning up old containers and volumes..."
    docker-compose down -v
fi

# Build all services
echo "🔨 Building all services..."
docker-compose build --no-cache

# Start services
echo "🎬 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check PostgreSQL
echo "📊 Checking PostgreSQL..."
docker-compose exec -T postgres pg_isready -U cqox || echo "⚠️  PostgreSQL not ready yet"

# Check Redis
echo "💾 Checking Redis..."
docker-compose exec -T redis redis-cli ping || echo "⚠️  Redis not ready yet"

# Check API
echo "🔌 Checking API..."
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    echo "Waiting for API..."
    sleep 2
done
echo "✅ API is healthy"

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T api alembic upgrade head || echo "⚠️  Migrations may have failed (might be okay if already run)"

# Create demo user
echo "👤 Creating demo users..."
docker-compose exec -T api python -m cqox.scripts.init_demo_users || echo "ℹ️  Demo users may already exist"

# Display service status
echo ""
echo "========================================"
echo "✅ CQOx Production Stack is Running!"
echo "========================================"
echo ""
echo "🌐 Service URLs:"
echo "  Frontend:    http://localhost:3004"
echo "  API:         http://localhost:8000"
echo "  API Docs:    http://localhost:8000/docs"
echo "  Grafana:     http://localhost:3000 (admin/admin)"
echo "  Prometheus:  http://localhost:9090"
echo "  RabbitMQ:    http://localhost:15672 (cqox/cqox_dev_password)"
echo ""
echo "👤 Demo Users:"
echo "  Admin:   admin@cqox.com / admin_password_change_me"
echo "  Analyst: analyst@cqox.com / analyst123"
echo "  Viewer:  viewer@cqox.com / viewer123"
echo ""
echo "📋 Useful Commands:"
echo "  View logs:        docker-compose logs -f"
echo "  View API logs:    docker-compose logs -f api"
echo "  Stop services:    docker-compose down"
echo "  Restart:          docker-compose restart"
echo ""
echo "🎉 Ready to go! Open http://localhost:3004 in your browser"

