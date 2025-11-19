# CQOx 本格版 実装マニュアル（初心者向け）

**対象**: プログラミング初心者〜中級者
**所要時間**: 約30分
**前提知識**: なし（このマニュアルで全て説明します）

---

## 📋 目次

1. [必要な準備](#1-必要な準備)
2. [環境構築](#2-環境構築)
3. [データベースの準備](#3-データベースの準備)
4. [アプリケーションの起動](#4-アプリケーションの起動)
5. [動作確認](#5-動作確認)
6. [トラブルシューティング](#6-トラブルシューティング)

---

## 1. 必要な準備

### 1.1 ソフトウェアのインストール

以下のソフトウェアが必要です。まだインストールしていない場合は、順番にインストールしてください。

#### ✅ Docker のインストール

**Dockerとは？**
複数のソフトウェア（データベース、Webサーバーなど）を簡単に動かすためのツールです。

**インストール方法（Fedora/Linux）:**
```bash
# Dockerをインストール
sudo dnf install docker docker-compose

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
docker-compose --version
```

**期待される出力:**
```
Docker version 24.0.x
docker-compose version 1.29.x
```

#### ✅ Gitのインストール（既にインストール済みの場合はスキップ）

```bash
sudo dnf install git
git --version
```

---

### 1.2 プロジェクトの取得

**すでにダウンロード済みの場合:**
`/home/hirokionodera/CQOx_gen/` にあります。

**新しくダウンロードする場合:**
```bash
cd ~
git clone https://github.com/onodera22ten/CQOx_gen.git
cd CQOx_gen
```

---

## 2. 環境構築

### 2.1 ディレクトリ構造の確認

まず、プロジェクトのフォルダ構造を確認します。

```bash
cd /home/hirokionodera/CQOx_gen
ls -la
```

**表示されるべきファイル:**
```
backend/          ← バックエンド（サーバー側）のコード
frontend/         ← フロントエンド（画面）のコード
docker-compose.yml ← Docker設定ファイル
.env.example      ← 環境変数のサンプル
README.md         ← 説明書
```

### 2.2 環境変数の設定

**環境変数とは？**
アプリケーションの設定（パスワード、データベース名など）を保存するファイルです。

```bash
# サンプルファイルをコピー
cp .env.example .env

# エディタで開く（nanoは初心者向けエディタ）
nano .env
```

**編集する内容:**
```bash
# データベースの設定
POSTGRES_DB=cqox
POSTGRES_USER=cqox
POSTGRES_PASSWORD=my_secure_password_123  # ← これを変更（好きなパスワード）

# 管理者アカウントの設定
ADMIN_EMAIL=admin@cqox.local
ADMIN_PASSWORD=admin_secure_pass_456      # ← これを変更（好きなパスワード）

# セキュリティキー
SECRET_KEY=very_long_random_string_here_change_this_in_production  # ← これを変更

# API URL（変更不要）
API_URL=http://localhost:8000
```

**nano エディタの使い方:**
- 矢印キーで移動
- 編集したら `Ctrl + O` で保存
- `Enter` で確定
- `Ctrl + X` で終了

---

## 3. データベースの準備

### 3.1 Dockerコンテナの起動

**これから何をするか？**
Docker Composeというツールを使って、以下の3つのサービスを一度に起動します：
1. PostgreSQL（データベース）
2. FastAPI（バックエンドサーバー）
3. React（フロントエンド画面）

```bash
# プロジェクトのルートディレクトリにいることを確認
cd /home/hirokionodera/CQOx_gen

# 3つのサービスを起動（初回は時間がかかります）
docker-compose up -d
```

**`-d` の意味:**
"detached mode" = バックグラウンドで動かす（ターミナルを占有しない）

**初回起動時の出力例:**
```
Creating network "cqox_network" ... done
Creating volume "cqox_postgres_data" ... done
Creating cqox_postgres ... done
Creating cqox_backend  ... done
Creating cqox_frontend ... done
```

**時間がかかる理由:**
初回はDockerがイメージをダウンロードするため、5〜10分かかります。

### 3.2 起動状態の確認

```bash
# 起動しているコンテナを確認
docker-compose ps
```

**期待される出力:**
```
       Name                     Command               State           Ports
----------------------------------------------------------------------------------
cqox_backend      uvicorn cqox.api.main:app ...   Up      0.0.0.0:8000->8000/tcp
cqox_frontend     npm run dev -- --host 0.0.0.0   Up      0.0.0.0:3000->3000/tcp
cqox_postgres     docker-entrypoint.sh postgres   Up      0.0.0.0:5432->5432/tcp
```

**重要:** `State` 列がすべて `Up` になっていることを確認してください。

### 3.3 ログの確認（エラーがある場合）

```bash
# すべてのログを表示
docker-compose logs

# バックエンドだけ表示
docker-compose logs backend

# リアルタイムで表示（Ctrl+Cで終了）
docker-compose logs -f
```

---

### 3.4 データベースの初期化

**これから何をするか？**
管理者アカウントを作成し、データベースのテーブルを作成します。

```bash
# バックエンドコンテナの中で初期化スクリプトを実行
docker-compose exec backend python cqox/db/init_db.py
```

**成功時の出力:**
```
✓ Database tables created
✓ Admin user created or already exists
  Email: admin@cqox.local
  Role: admin
Database initialization complete!
```

**エラーが出た場合:**
→ [トラブルシューティング](#6-トラブルシューティング) を参照

---

## 4. アプリケーションの起動

### 4.1 ブラウザでアクセス

以下のURLをブラウザで開きます：

```
http://localhost:3000
```

**ログイン画面が表示されるはずです。**

### 4.2 ログイン

**認証情報:**
- **Email**: `admin@cqox.local`
- **Password**: `.env` ファイルで設定した `ADMIN_PASSWORD`

**デフォルト（変更していない場合）:**
- Password: `admin_password_change_me`

### 4.3 ログイン後の画面

ログインに成功すると、以下の画面が表示されます：

1. **左サイドバー**: メニュー
   - Data Management
   - Causal Design
   - Decision Console
   - など

2. **メイン画面**: ダッシュボード

---

## 5. 動作確認

### 5.1 データセットのアップロード

**手順:**

1. 左メニューから **"Data Management"** をクリック
2. **"Upload Dataset"** ボタンをクリック
3. CSVファイルを選択（サンプル: `demo-version/sample_data/marketing_campaign_2024.csv`）
4. データセット名と説明を入力
5. **"Upload"** をクリック

**成功すると:**
- データセット一覧に表示される
- 行数・列数が表示される

### 5.2 因果推定の実行

**手順:**

1. 左メニューから **"Causal Design & Evaluation"** をクリック
2. アップロードしたデータセットを選択
3. **Treatment カラム** を選択（例: `treatment`）
4. **Outcome カラム** を選択（例: `revenue`）
5. **Feature カラム** を選択（例: `age`, `gender`, `region`）
6. **推定量** を選択（例: DR, IPW, DiD）
7. **"Train Models"** をクリック

**実行中:**
- 進捗バーが表示される
- "Running analysis..." というメッセージが出る

**完了すると:**
- Decision Card が表示される
- ATE（平均処置効果）が表示される
- Go/Canary/Hold の判定が表示される

### 5.3 決定コンソールの確認

**手順:**

1. 左メニューから **"Decision Console"** をクリック
2. 過去の分析結果一覧が表示される
3. 各カードに以下の情報が表示される：
   - Δ¥（収益インパクト）
   - 判定（Go/Canary/Hold）
   - CAS Score
   - Risk Score

---

## 6. トラブルシューティング

### 6.1 「docker-compose: command not found」エラー

**原因:**
Docker Composeがインストールされていない。

**解決方法:**
```bash
sudo dnf install docker-compose
```

### 6.2 「permission denied」エラー

**原因:**
Dockerを使う権限がない。

**解決方法:**
```bash
# 自分をdockerグループに追加
sudo usermod -aG docker $USER

# ログアウトして再ログイン
exit
# 再度ログイン

# または
newgrp docker
```

### 6.3 ポート競合エラー

**エラーメッセージ:**
```
Error starting userland proxy: listen tcp 0.0.0.0:3000: bind: address already in use
```

**原因:**
ポート3000または8000が既に使われている。

**解決方法1: 使用中のプロセスを確認**
```bash
# ポート3000を使っているプロセスを確認
lsof -i :3000

# 結果例:
# COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
# node    12345 user   22u  IPv4  12345      0t0  TCP *:3000 (LISTEN)

# プロセスを停止
kill -9 12345
```

**解決方法2: バックグラウンドのnpm dev を停止**
```bash
# npm run dev が動いている場合
pkill -f "npm run dev"
pkill -f "vite"
```

### 6.4 データベース接続エラー

**エラーメッセージ:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解決方法:**
```bash
# PostgreSQLコンテナが起動しているか確認
docker-compose ps postgres

# 起動していない場合
docker-compose up -d postgres

# ログを確認
docker-compose logs postgres

# 再起動
docker-compose restart postgres
```

### 6.5 フロントエンドが表示されない

**症状:**
http://localhost:3000 にアクセスしても何も表示されない。

**解決方法:**
```bash
# フロントエンドコンテナのログを確認
docker-compose logs frontend

# 再ビルド
docker-compose down
docker-compose up -d --build frontend
```

### 6.6 ログインできない

**症状:**
Email/Passwordを入力してもログインできない。

**確認事項:**
1. `.env` ファイルの `ADMIN_EMAIL` と `ADMIN_PASSWORD` を確認
2. データベース初期化を再実行

```bash
# 初期化を再実行
docker-compose exec backend python cqox/db/init_db.py
```

### 6.7 すべてをリセットする

**何もかもうまくいかない場合:**
```bash
# すべて停止
docker-compose down

# データも削除（注意：データが消えます）
docker-compose down -v

# イメージも削除
docker-compose down --rmi all

# 再構築
docker-compose up -d --build
docker-compose exec backend python cqox/db/init_db.py
```

---

## 7. よくある質問（FAQ）

### Q1: データベースのデータはどこに保存されますか？

**A:** Dockerボリューム `cqox_postgres_data` に保存されます。

```bash
# ボリュームの確認
docker volume ls | grep postgres_data

# データの場所
docker volume inspect cqox_postgres_data
```

### Q2: 開発中にコードを変更したら再起動が必要ですか？

**A:** いいえ、不要です。
- **バックエンド**: `--reload` オプションで自動リロード
- **フロントエンド**: Viteのホットリロードで自動更新

### Q3: 本番環境にデプロイするには？

**A:** 以下を変更してください：
1. `.env` のパスワードを強力なものに変更
2. `SECRET_KEY` をランダムな長い文字列に変更
3. `docker-compose.yml` の `command` から `--reload` を削除
4. HTTPS証明書を設定

### Q4: 管理者を追加するには？

**A:** データベースに直接追加します：

```bash
# PostgreSQLコンテナに入る
docker-compose exec postgres psql -U cqox -d cqox

# SQLで追加
INSERT INTO users (email, password_hash, role, is_active)
VALUES ('new_admin@example.com', 'hashed_password_here', 'admin', true);

# 終了
\q
```

### Q5: バックアップを取るには？

**A:** PostgreSQLのダンプを取ります：

```bash
# バックアップ
docker-compose exec postgres pg_dump -U cqox cqox > backup_$(date +%Y%m%d).sql

# リストア
docker-compose exec -T postgres psql -U cqox cqox < backup_20250119.sql
```

---

## 8. 停止と再起動

### 8.1 停止

```bash
# すべてのサービスを停止
docker-compose stop

# 停止して削除（データは残る）
docker-compose down
```

### 8.2 再起動

```bash
# 起動
docker-compose up -d

# 特定のサービスだけ再起動
docker-compose restart backend
```

### 8.3 完全削除（データも削除）

```bash
# 注意: データも消えます！
docker-compose down -v
```

---

## 9. 開発のヒント

### 9.1 ログをリアルタイムで見る

```bash
# すべてのログ
docker-compose logs -f

# バックエンドだけ
docker-compose logs -f backend

# フロントエンドだけ
docker-compose logs -f frontend
```

### 9.2 コンテナの中に入る

```bash
# バックエンドコンテナに入る
docker-compose exec backend bash

# PostgreSQLコンテナに入る
docker-compose exec postgres bash

# 終了
exit
```

### 9.3 データベースを直接操作

```bash
# PostgreSQLに接続
docker-compose exec postgres psql -U cqox -d cqox

# テーブル一覧
\dt

# ユーザ一覧
SELECT * FROM users;

# 終了
\q
```

---

## 10. まとめ

**起動手順（まとめ）:**
```bash
cd /home/hirokionodera/CQOx_gen
cp .env.example .env
nano .env  # パスワード設定
docker-compose up -d
docker-compose exec backend python cqox/db/init_db.py
# ブラウザで http://localhost:3000 を開く
```

**停止手順:**
```bash
docker-compose stop
```

**再起動手順:**
```bash
docker-compose up -d
```

---

## 11. 次のステップ

本格版が動作したら、以下を試してみましょう：

1. **自分のデータをアップロード**
2. **因果推定を実行**
3. **結果をDecision Consoleで確認**
4. **カスタムシナリオを作成**

---

**お疲れ様でした！** 🎉

問題が発生した場合は、[トラブルシューティング](#6-トラブルシューティング)を参照してください。
