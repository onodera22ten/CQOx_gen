#!/bin/bash
# Celery worker startup script

set -e

echo "🚀 Starting Celery worker for CQOx..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis is not running. Please start Redis first."
    echo "   Run: redis-server"
    exit 1
fi

# Change to backend directory
cd "$(dirname "$0")/.."

# Start Celery worker
echo "👷 Starting Celery worker..."
celery -A cqox.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --max-tasks-per-child=100 \
    --task-events \
    --without-gossip \
    --without-mingle

echo "✅ Celery worker started!"
