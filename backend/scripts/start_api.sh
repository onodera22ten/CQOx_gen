#!/bin/bash
# FastAPI server startup script

set -e

echo "🚀 Starting CQOx API server..."

# Change to backend directory
cd "$(dirname "$0")/.."

# Check if database is accessible
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "⚠️  Warning: PostgreSQL is not running. Some features may not work."
fi

# Start FastAPI with uvicorn
echo "🌐 Starting FastAPI server on http://localhost:8000"
uvicorn cqox.api.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info

echo "✅ API server started!"
