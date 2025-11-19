#!/bin/bash

# CQOx Demo Version - Quick Start Script
# Usage: ./start.sh

echo "🚀 CQOx Demo Version - Starting..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 が見つかりません。インストールしてください。"
    exit 1
fi

# Install dependencies
echo "📦 依存関係をインストール中..."
cd backend
pip3 install -r requirements.txt --quiet
cd ..

# Get IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

# Start backend
echo "🔧 バックエンドを起動中 (ポート 8000)..."
cd backend
python3 main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "🎨 フロントエンドを起動中 (ポート 3000)..."
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ CQOx Demo が起動しました！"
echo ""
echo "📍 アクセスURL:"
echo "   - ローカル: http://localhost:3000"
echo "   - LAN内:    http://${IP_ADDRESS}:3000"
echo ""
echo "🔍 サンプルデータ: marketing_campaign_2024 (100行)"
echo "🧪 推定量: DR, IPW, DiD, IV, CF, SCM, RD"
echo ""
echo "🛑 停止するには: pkill -f 'python3 main.py' && pkill -f 'http.server 3000'"
echo ""
