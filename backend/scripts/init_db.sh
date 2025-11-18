#!/bin/bash
# Database initialization script

set -e

echo "🔧 Initializing CQOx database..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    exit 1
fi

# Create database if not exists
echo "📦 Creating database..."
psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'cqox'" | grep -q 1 || \
    psql -U postgres -c "CREATE DATABASE cqox;"

# Create user if not exists
echo "👤 Creating database user..."
psql -U postgres -tc "SELECT 1 FROM pg_roles WHERE rolname = 'cqox'" | grep -q 1 || \
    psql -U postgres -c "CREATE USER cqox WITH PASSWORD 'cqox';"

# Grant privileges
echo "🔑 Granting privileges..."
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE cqox TO cqox;"

# Run Alembic migrations
echo "🔄 Running database migrations..."
cd "$(dirname "$0")/.."
alembic upgrade head

echo "✅ Database initialization complete!"
echo ""
echo "Database: cqox"
echo "User: cqox"
echo "Password: cqox"
echo "Connection string: postgresql://cqox:cqox@localhost:5432/cqox"
