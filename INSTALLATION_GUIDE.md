# CQOx インストールガイド

## 📦 ワンクリックインストール版

### 前提条件
- Docker Desktop がインストール済み
- 8GB以上のメモリ
- 10GB以上のディスク空き容量

---

## 🚀 インストール手順（3ステップ）

### Step 1: プロジェクトを取得
```bash
# GitHubからダウンロード（またはZIPを解凍）
git clone https://github.com/your-org/CQOx.git
cd CQOx
```

### Step 2: 起動スクリプトを実行
```bash
# Windowsの場合
start.bat

# Mac/Linuxの場合
./start.sh
```

### Step 3: ブラウザでアクセス
- **URL**: http://localhost:3004
- **ログイン情報**:
  - Email: `admin@cqox.com`
  - Password: `admin_password_change_me`

---

## 📝 起動スクリプトの内容

### `start.bat` (Windows用)
```batch
@echo off
echo ========================================
echo  CQOx - Causal Query Optimizer
echo  Starting Application...
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not running. Please start Docker Desktop.
    pause
    exit /b 1
)

echo [1/3] Starting services...
docker compose up -d

echo.
echo [2/3] Waiting for services to be ready (30 seconds)...
timeout /t 30 /nobreak >nul

echo.
echo [3/3] Checking service status...
docker compose ps

echo.
echo ========================================
echo  CQOx is ready!
echo ========================================
echo.
echo  Access the application:
echo  URL: http://localhost:3004
echo.
echo  Default login:
echo  Email: admin@cqox.com
echo  Password: admin_password_change_me
echo.
echo ========================================
echo.
pause
```

### `start.sh` (Mac/Linux用)
```bash
#!/bin/bash

echo "========================================"
echo " CQOx - Causal Query Optimizer"
echo " Starting Application..."
echo "========================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker is not running. Please start Docker."
    exit 1
fi

echo "[1/3] Starting services..."
docker compose up -d

echo ""
echo "[2/3] Waiting for services to be ready (30 seconds)..."
sleep 30

echo ""
echo "[3/3] Checking service status..."
docker compose ps

echo ""
echo "========================================"
echo " CQOx is ready!"
echo "========================================"
echo ""
echo " Access the application:"
echo " URL: http://localhost:3004"
echo ""
echo " Default login:"
echo " Email: admin@cqox.com"
echo " Password: admin_password_change_me"
echo ""
echo "========================================"
echo ""
```

---

## 🛑 停止方法

### アプリケーションを停止
```bash
# Windowsの場合
stop.bat

# Mac/Linuxの場合
./stop.sh
```

### `stop.bat` / `stop.sh`
```bash
#!/bin/bash
echo "Stopping CQOx..."
docker compose down
echo "✅ CQOx stopped successfully"
```

---

## 🔧 トラブルシューティング

### ログインできない
```bash
# APIログを確認
docker compose logs api --tail=50

# 全サービスを再起動
docker compose restart
```

### ポートが使用中
```bash
# ポート8000, 3004が使用中の場合、docker-compose.ymlを編集
# ports:
#   - "8001:8000"  # 8000を8001に変更
#   - "3005:80"    # 3004を3005に変更
```

### データをリセット
```bash
# 全データを削除して再起動
docker compose down -v
docker compose up -d
```

---

## 📦 配布用パッケージの作成

### 1. Docker Imageとして配布
```bash
# イメージを保存
docker save cqox_gen-api cqox_gen-frontend cqox_gen-celery_worker | gzip > cqox-app.tar.gz

# 配布先での読み込み
gunzip -c cqox-app.tar.gz | docker load
docker compose up -d
```

### 2. インストーラーパッケージ
```
CQOx-Installer/
├── docker-compose.yml
├── backend/ (Dockerfileとソースコード)
├── frontend/ (Dockerfileとビルド済みファイル)
├── start.bat
├── start.sh
├── stop.bat
├── stop.sh
└── README.md (このファイル)
```

---

## 🎯 ユーザー向け配布方法

### Option 1: ZIP配布
1. プロジェクト全体をZIPに圧縮
2. ユーザーは解凍して `start.bat` をダブルクリック

### Option 2: インストーラー（Windows）
- Inno Setup等でインストーラーを作成
- Docker Desktop自動インストール
- CQOx自動起動

### Option 3: Docker Hub配布
```bash
# Docker Hubにプッシュ
docker push your-org/cqox-api:latest
docker push your-org/cqox-frontend:latest

# ユーザーは docker-compose.yml だけで起動
docker compose up -d
```

---

## 📚 ドキュメント

- **ユーザーガイド**: `docs/USER_GUIDE.md`
- **管理者ガイド**: `docs/ADMIN_GUIDE.md`
- **API仕様**: http://localhost:8000/api/docs

---

## 🔐 セキュリティ

### 本番環境での推奨設定
1. デフォルトパスワードを変更
2. HTTPS（SSL/TLS）を有効化
3. ファイアウォール設定
4. 定期的なバックアップ

---

## 📞 サポート

- **問題報告**: GitHub Issues
- **質問**: support@cqox.local
- **ドキュメント**: https://docs.cqox.local

