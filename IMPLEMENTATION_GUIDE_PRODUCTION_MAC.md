# CQOx 本格版 実装マニュアル（macOS版）

**対象OS**: macOS (Monterey 12.0+, Ventura, Sonoma)
**対象者**: プログラミング初心者〜中級者
**所要時間**: 約30分
**前提知識**: なし

---

## 📋 目次

1. [必要な準備](#1-必要な準備)
2. [Docker Desktopのインストール](#2-docker-desktopのインストール)
3. [環境構築](#3-環境構築)
4. [データベースの準備](#4-データベースの準備)
5. [アプリケーションの起動](#5-アプリケーションの起動)
6. [動作確認](#6-動作確認)
7. [トラブルシューティング](#7-トラブルシューティング)

---

## 1. 必要な準備

### 1.1 システム要件

- **macOS**: 12.0 (Monterey) 以上
- **CPU**: Intel または Apple Silicon (M1/M2/M3)
- **メモリ**: 8GB以上（推奨16GB）
- **ディスク**: 10GB以上の空き容量

### 1.2 Homebrewのインストール（オプション）

Homebrewがない場合、インストールします：

```bash
# Homebrewをインストール
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# パスを通す（M1/M2/M3 Macの場合）
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"

# 確認
brew --version
```

---

## 2. Docker Desktopのインストール

### 2.1 方法1: 公式サイトからダウンロード（推奨）

1. **Docker公式サイトにアクセス**
   - https://www.docker.com/products/docker-desktop

2. **Download for Mac** をクリック
   - **Intel Mac**: Intel Chip版を選択
   - **Apple Silicon (M1/M2/M3)**: Apple Chip版を選択

3. **ダウンロードした.dmgファイルを開く**
   - Docker.appをApplicationsフォルダにドラッグ

4. **Applicationsフォルダから Docker を起動**
   - 初回起動時に権限を要求されます（許可してください）

5. **Docker Desktopが起動したら、メニューバーにクジラのアイコンが表示されます**

### 2.2 方法2: Homebrewでインストール

```bash
# Docker Desktopをインストール
brew install --cask docker

# Applicationsフォルダから Docker を起動
open /Applications/Docker.app
```

### 2.3 インストール確認

```bash
# Dockerバージョン確認
docker --version

# Docker Composeバージョン確認
docker compose version
```

**期待される出力:**
```
Docker version 24.0.x, build xxxxx
Docker Compose version v2.24.x
```

---

## 3. 環境構築

### 3.1 プロジェクトの取得

**GitHubからクローン:**
```bash
# ホームディレクトリに移動
cd ~

# リポジトリをクローン
git clone https://github.com/onodera22ten/CQOx_gen.git

# プロジェクトディレクトリに移動
cd CQOx_gen
```

**ファイル確認:**
```bash
ls -la
```

**表示されるべきファイル:**
```
backend/
frontend/
docker-compose.yml
.env.example
README.md
```

### 3.2 環境変数の設定

```bash
# サンプルファイルをコピー
cp .env.example .env

# エディタで開く（Visual Studio Codeの場合）
code .env

# またはnanoエディタ
nano .env
```

**編集する内容:**
```bash
# データベースの設定
POSTGRES_PASSWORD=my_secure_password_123  # ← 変更

# 管理者アカウントの設定
ADMIN_EMAIL=admin@cqox.local
ADMIN_PASSWORD=admin_secure_pass_456      # ← 変更

# セキュリティキー（長いランダム文字列）
SECRET_KEY=very_long_random_string_change_this  # ← 変更
```

**保存:**
- VS Code: `Cmd + S`
- nano: `Ctrl + O` → `Enter` → `Ctrl + X`

---

## 4. データベースの準備

### 4.1 Docker Desktopが起動していることを確認

メニューバーにクジラのアイコンがあることを確認してください。

### 4.2 Dockerコンテナの起動

```bash
cd ~/CQOx_gen

# 3つのサービスを起動
docker compose up -d
```

**初回は5〜10分かかります（イメージダウンロード）**

**出力例:**
```
[+] Running 3/3
 ✔ Container cqox_postgres   Started
 ✔ Container cqox_backend    Started
 ✔ Container cqox_frontend   Started
```

### 4.3 起動状態の確認

```bash
# 起動しているコンテナを確認
docker compose ps
```

**期待される出力:**
```
NAME              IMAGE           STATUS         PORTS
cqox_backend      cqox-backend    Up 2 minutes   0.0.0.0:8000->8000/tcp
cqox_frontend     cqox-frontend   Up 2 minutes   0.0.0.0:3000->3000/tcp
cqox_postgres     postgres:15     Up 2 minutes   0.0.0.0:5432->5432/tcp
```

**重要:** `STATUS` 列がすべて `Up` になっていることを確認。

### 4.4 Docker Desktopでの確認（GUI）

1. Docker Desktopを開く
2. **Containers** タブをクリック
3. `cqox_gen` というグループに3つのコンテナが表示される
4. すべてが緑色（Running）であることを確認

### 4.5 ログの確認

```bash
# すべてのログを表示
docker compose logs

# バックエンドだけ表示
docker compose logs backend

# リアルタイムで表示（Ctrl+Cで終了）
docker compose logs -f
```

### 4.6 データベースの初期化

```bash
# バックエンドコンテナの中で初期化スクリプトを実行
docker compose exec backend python cqox/db/init_db.py
```

**成功時の出力:**
```
✓ Database tables created
✓ Admin user created or already exists
  Email: admin@cqox.local
  Role: admin
Database initialization complete!
```

---

## 5. アプリケーションの起動

### 5.1 ブラウザでアクセス

```
http://localhost:3001
```

**注意**: ポート3000がGrafanaなど他のサービスで使用されている場合、CQOxフロントエンドはポート3001で起動します。

### 5.2 ログイン

- **Email**: `admin@cqox.local`
- **Password**: `.env`ファイルで設定した`ADMIN_PASSWORD`

---

## 6. 動作確認

### 6.1 データセットのアップロード

1. 左メニュー → **"Data Management"**
2. **"Upload Dataset"** ボタン
3. CSVファイルを選択
4. **"Upload"**

### 6.2 因果推定の実行

1. 左メニュー → **"Causal Design & Evaluation"**
2. データセット選択
3. Treatment/Outcome/Feature カラム選択
4. **"Train Models"**

---

## 7. トラブルシューティング

### 7.1 Docker Desktopが起動しない

**症状:** Docker Desktopが起動しない、またはクラッシュする。

**解決方法:**

1. **Docker Desktopを完全に終了**
```bash
killall Docker
```

2. **再起動**
```bash
open /Applications/Docker.app
```

3. **設定を確認**
   - Docker Desktop → Preferences → Resources
   - Memory: 4GB以上に設定
   - Swap: 1GB以上に設定

### 7.2 「Cannot connect to the Docker daemon」エラー

**原因:** Docker Desktopが起動していない。

**解決方法:**
```bash
# Docker Desktopを起動
open /Applications/Docker.app

# 数秒待ってから再試行
docker compose up -d
```

### 7.3 ポート競合エラー

**エラー:**
```
Error: bind: address already in use
```

**解決方法:**
```bash
# 使用中のプロセスを確認
lsof -i :3001
lsof -i :8000

# 該当プロセスを停止
kill -9 <PID>

# またはバックグラウンドのnpmを停止
pkill -f "npm run dev"
pkill -f "vite"
```

### 7.4 M1/M2/M3 Mac: Rosetta関連エラー

**エラー:**
```
no matching manifest for linux/arm64/v8
```

**解決方法:**

**方法1: Rosettaを有効化**
```bash
softwareupdate --install-rosetta --agree-to-license
```

**方法2: docker-compose.ymlを編集**
```yaml
# 各serviceに以下を追加
platform: linux/amd64
```

### 7.5 データベース接続エラー

**解決方法:**
```bash
# PostgreSQLコンテナの確認
docker compose ps postgres

# 起動していない場合
docker compose up -d postgres

# ログを確認
docker compose logs postgres

# 再起動
docker compose restart postgres
```

### 7.6 パフォーマンスが遅い

**原因:** Dockerのリソース制限

**解決方法:**

1. Docker Desktop を開く
2. **Preferences (設定)** → **Resources (リソース)**
3. **Memory**: 8GB以上に設定
4. **Swap**: 2GB以上に設定
5. **Apply & Restart**

### 7.7 すべてをリセット

```bash
# すべて停止
docker compose down

# データも削除（注意：データが消えます）
docker compose down -v

# イメージも削除
docker compose down --rmi all

# Dockerのキャッシュをクリア
docker system prune -a

# 再構築
docker compose up -d --build
docker compose exec backend python cqox/db/init_db.py
```

---

## 8. コマンド一覧（クイックリファレンス）

### 起動・停止

```bash
# 起動
docker compose up -d

# 停止
docker compose stop

# 停止して削除（データは残る）
docker compose down

# 停止してデータも削除
docker compose down -v
```

### 状態確認

```bash
# コンテナ一覧
docker compose ps

# ログ表示
docker compose logs
docker compose logs -f backend

# リソース使用状況
docker stats
```

### コンテナ操作

```bash
# コンテナの中に入る
docker compose exec backend bash
docker compose exec postgres bash

# コマンド実行
docker compose exec backend python cqox/db/init_db.py

# 再起動
docker compose restart backend
```

---

## 9. まとめ

### 起動手順（まとめ）

```bash
cd ~/CQOx_gen
cp .env.example .env
nano .env  # パスワード設定
docker compose up -d
docker compose exec backend python cqox/db/init_db.py
# ブラウザで http://localhost:3001 を開く
```

### 停止手順

```bash
docker compose stop
```

### 再起動手順

```bash
docker compose up -d
```

---

## 10. macOS固有の注意点

### 10.1 ファイアウォール設定

外部からアクセスする場合:

1. **システム設定** → **ネットワーク** → **ファイアウォール**
2. **ファイアウォールオプション**
3. **Docker** を許可リストに追加

### 10.2 Rosetta 2（Apple Silicon Macのみ）

一部のイメージがIntel向けの場合、Rosetta 2が必要:

```bash
# Rosetta 2をインストール
softwareupdate --install-rosetta --agree-to-license
```

### 10.3 ディスク容量の管理

```bash
# Dockerのディスク使用状況確認
docker system df

# 不要なイメージ/コンテナを削除
docker system prune -a
```

### 10.4 ネットワーク設定

VPNやプロキシを使用している場合:

1. Docker Desktop → Preferences → Resources → Proxies
2. プロキシ設定を入力

---

## 11. よくある質問（macOS版）

### Q1: Intel MacとApple Silicon Macで違いはありますか？

**A:** 基本的に同じですが、以下の点が異なります：

| 項目 | Intel Mac | Apple Silicon (M1/M2/M3) |
|------|-----------|-------------------------|
| アーキテクチャ | x86_64 | arm64 |
| パフォーマンス | 通常 | より高速 |
| Rosetta 2 | 不要 | 一部必要 |

### Q2: Docker Desktopは必須ですか？

**A:** はい、macOSではDocker Desktopが推奨されます。
代替手段（Colima等）もありますが、初心者には推奨しません。

### Q3: バックグラウンドで動かしたくない

**A:** 以下の設定で自動起動を無効化できます：

1. Docker Desktop → Preferences
2. **General** → **Start Docker Desktop when you log in** のチェックを外す

### Q4: ディスク容量を節約したい

**A:** Docker Desktopの設定で制限できます：

1. Docker Desktop → Preferences → Resources → Advanced
2. **Disk image size** を調整（デフォルト: 64GB）

---

## 12. ショートカット（macOS）

```bash
# alias を設定（オプション）
echo 'alias dc="docker compose"' >> ~/.zshrc
source ~/.zshrc

# 使用例
dc up -d
dc ps
dc logs -f
```

---

**お疲れ様でした！** 🎉

macOSでの実装が完了しました。
