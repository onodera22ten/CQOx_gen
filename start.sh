#!/bin/bash

echo "========================================"
echo " CQOx - Causal Query Optimizer"
echo " アプリケーションを起動しています..."
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[エラー] Dockerが起動していません。Dockerを起動してください。"
    exit 1
fi

echo "[1/3] サービスを起動中..."
docker compose up -d

echo ""
echo "[2/3] サービスの準備を待っています (30秒)..."
sleep 30

echo ""
echo "[3/3] サービス状態を確認中..."
docker compose ps

echo ""
echo "========================================"
echo " CQOx の起動が完了しました！"
echo "========================================"
echo ""
echo " ブラウザで以下にアクセスしてください:"
echo " URL: http://localhost:3004"
echo ""
echo " ログイン情報:"
echo " Email: admin@cqox.com"
echo " Password: admin_password_change_me"
echo ""
echo "========================================"
echo ""

