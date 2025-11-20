# CQOx 本格版 実装マニュアル（Linux/Fedora版）

**対象OS**: Linux（Fedora 42）
**対象者**: プログラミング初心者〜中級者
**所要時間**: 約30分
**前提知識**: なし

---

## 📋 目次

1. [必要な準備](#1-必要な準備)
2. [Docker Composeのインストール](#2-docker-composeのインストール)
3. [環境構築](#3-環境構築)
4. [データベースの準備](#4-データベースの準備)
5. [アプリケーションの起動](#5-アプリケーションの起動)
6. [動作確認](#6-動作確認)
7. [トラブルシューティング](#7-トラブルシューティング)

---

## 1. 必要な準備

### 1.1 Dockerのインストール

```bash
# Dockerをインストール
sudo dnf install -y docker

# Dockerを起動
sudo systemctl start docker
sudo systemctl enable docker

# 自分のアカウントでDockerを使えるようにする
sudo usermod -aG docker $USER

# ログアウトして再ログイン（重要！）
# または以下を実行
newgrp docker

# 確認
docker --version
```

**期待される出力:**
```
Docker version 29.0.0, build 3d4129b
```

---

## 2. Docker Composeのインストール

### ⚠️ 重要: Fedora 42での注意点

Fedora 42では`docker-compose`パッケージに競合があります。
**Docker Compose Plugin**を使用します（推奨）。

### 2.1 インストール手順

```bash
# 古いdocker-composeがあれば削除
sudo dnf remove -y docker-compose 2>/dev/null

# Docker Compose Pluginをインストール
sudo dnf install -y docker-compose-plugin

# 確認（新しいコマンド形式）
docker compose version
```

**期待される出力:**
```
Docker Compose version v2.24.0
```

### 2.2 コマンドの違い

**重要:** コマンドが変わりました！

| 旧形式（使えない） | 新形式（使う） |
|-------------------|---------------|
| `docker-compose up` | `docker compose up` |
| `docker-compose ps` | `docker compose ps` |
| `docker-compose logs` | `docker compose logs` |

**ハイフン（-）がスペースに変わりました。**

---

## 3. 環境構築

### 3.1 プロジェクトの場所

```bash
cd /home/hirokionodera/CQOx_gen
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

# エディタで開く
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

**保存:** `Ctrl + O` → `Enter` → `Ctrl + X`

---

## 4. データベースの準備

### 4.1 Dockerコンテナの起動

```bash
cd /home/hirokionodera/CQOx_gen

# 3つのサービスを起動（スペースに注意！）
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

### 4.2 起動状態の確認

```bash
# 起動しているコンテナを確認（スペース！）
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

### 4.3 ログの確認

```bash
# すべてのログを表示
docker compose logs

# バックエンドだけ表示
docker compose logs backend

# リアルタイムで表示（Ctrl+Cで終了）
docker compose logs -f
```

### 4.4 データベースの初期化

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

### 7.1 「command not found: docker compose」エラー

**原因:** Docker Compose Pluginがインストールされていない。

**解決方法:**
```bash
sudo dnf install -y docker-compose-plugin
docker compose version
```

### 7.2 「permission denied」エラー

**原因:** Dockerを使う権限がない。

**解決方法:**
```bash
sudo usermod -aG docker $USER
newgrp docker
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

### 7.4 データベース接続エラー

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

### 7.5 Fedora 42特有: パッケージ競合

**エラー:**
```
package docker-compose-2.33.1-1.fc42.x86_64 from fedora conflicts with...
```

**解決方法:**
```bash
# 古いdocker-composeを完全削除
sudo dnf remove -y docker-compose

# Docker Compose Pluginを使う
sudo dnf install -y docker-compose-plugin

# 新しいコマンド形式を使用
docker compose up -d
```

### 7.6 すべてをリセット

```bash
# すべて停止
docker compose down

# データも削除（注意：データが消えます）
docker compose down -v

# イメージも削除
docker compose down --rmi all

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
cd /home/hirokionodera/CQOx_gen
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

## 10. Linux固有の注意点

### 10.1 ファイアウォール設定

外部からアクセスする場合（オプション）:

```bash
# ポートを開放
sudo firewall-cmd --add-port=3000/tcp --permanent
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload

# 確認
sudo firewall-cmd --list-ports
```

### 10.2 SELinux設定

SELinuxが有効な場合:

```bash
# SELinuxの状態確認
getenforce

# 一時的に無効化（テスト用）
sudo setenforce 0

# 永続的に無効化（本番では非推奨）
sudo vi /etc/selinux/config
# SELINUX=disabled に変更
```

### 10.3 リソース制限

```bash
# Dockerのリソース確認
docker system df

# 不要なイメージ/コンテナを削除
docker system prune -a
```

---

## 11. よくある質問（Linux版）

### Q1: Fedora以外のLinuxでも動きますか？

**A:** はい、以下のディストリビューションで動作します：

- **Ubuntu/Debian**: `apt`コマンドを使用
- **CentOS/RHEL**: `yum`コマンドを使用
- **Arch Linux**: `pacman`コマンドを使用

**Ubuntu/Debianの場合:**
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
```

### Q2: WSL（Windows Subsystem for Linux）でも動きますか？

**A:** はい、WSL2で動作します。ただし：
- Docker DesktopをWindowsにインストール
- WSL2統合を有効化
- この後、LinuxマニュアルのコマンドをWSL内で実行

### Q3: sudoなしでDockerを使いたい

**A:** dockerグループに追加後、ログアウトが必要です：

```bash
sudo usermod -aG docker $USER
# ログアウトして再ログイン
# または
newgrp docker
```

---

**お疲れ様でした！** 🎉

Linux（Fedora 42）での実装が完了しました。
