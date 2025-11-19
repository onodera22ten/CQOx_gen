# CQOx 本格版 実装マニュアル（Windows版）

**対象OS**: Windows 10/11 (Home, Pro, Enterprise)
**対象者**: プログラミング初心者〜中級者
**所要時間**: 約30分
**前提知識**: なし

---

## 📋 目次

1. [必要な準備](#1-必要な準備)
2. [WSL2のインストール](#2-wsl2のインストール)
3. [Docker Desktopのインストール](#3-docker-desktopのインストール)
4. [環境構築](#4-環境構築)
5. [データベースの準備](#5-データベースの準備)
6. [アプリケーションの起動](#6-アプリケーションの起動)
7. [動作確認](#7-動作確認)
8. [トラブルシューティング](#8-トラブルシューティング)

---

## 1. 必要な準備

### 1.1 システム要件

- **OS**: Windows 10 (version 2004以降) または Windows 11
- **CPU**: 64ビット、仮想化対応（Intel VT-x/AMD-V）
- **メモリ**: 8GB以上（推奨16GB）
- **ディスク**: 10GB以上の空き容量
- **BIOS**: 仮想化が有効化されていること

### 1.2 仮想化の確認

**タスクマネージャーで確認:**

1. `Ctrl + Shift + Esc` でタスクマネージャーを開く
2. **パフォーマンス** タブをクリック
3. **CPU** を選択
4. 右下に「仮想化: 有効」と表示されていることを確認

**無効の場合:**
- BIOSで仮想化（Intel VT-x/AMD-V）を有効化する必要があります
- 各PCメーカーのマニュアルを参照してください

---

## 2. WSL2のインストール

### 2.1 WSL2とは？

**WSL (Windows Subsystem for Linux)** は、Windows上でLinuxを動かすための機能です。
Docker DesktopはWSL2を使用します。

### 2.2 インストール手順

**管理者権限でPowerShellを開く:**

1. `Win` キーを押す
2. 「PowerShell」と入力
3. **Windows PowerShell** を右クリック
4. **管理者として実行** を選択

**WSL2をインストール:**

```powershell
# WSLをインストール（再起動が必要）
wsl --install
```

**再起動後、再度PowerShellを開いて確認:**

```powershell
# WSLバージョン確認
wsl --version

# Ubuntuが自動インストールされます
wsl --list --verbose
```

**期待される出力:**
```
NAME      STATE           VERSION
Ubuntu    Running         2
```

### 2.3 Ubuntuの初期設定

初回起動時にユーザー名とパスワードを設定します:

```
Enter new UNIX username: (好きなユーザー名)
New password: (パスワード)
Retype new password: (パスワード再入力)
```

---

## 3. Docker Desktopのインストール

### 3.1 ダウンロードとインストール

1. **Docker公式サイトにアクセス**
   - https://www.docker.com/products/docker-desktop

2. **Download for Windows** をクリック

3. **ダウンロードした.exeファイルを実行**
   - `Docker Desktop Installer.exe`

4. **インストール オプション**
   - ✅ **Use WSL 2 instead of Hyper-V** にチェック
   - ✅ **Add shortcut to desktop** にチェック（オプション）

5. **インストール完了後、再起動**

### 3.2 Docker Desktopの起動

1. デスクトップまたはスタートメニューから **Docker Desktop** を起動
2. 初回起動時に利用規約に同意
3. タスクバーにクジラのアイコンが表示されればOK

### 3.3 WSL2統合の有効化

1. Docker Desktop を開く
2. **Settings (設定)** をクリック
3. **Resources** → **WSL Integration**
4. **Enable integration with my default WSL distro** をON
5. **Ubuntu** もON
6. **Apply & Restart**

### 3.4 インストール確認

**PowerShellまたはコマンドプロンプトで:**

```powershell
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

## 4. 環境構築

### 4.1 Gitのインストール

**Git for Windowsをインストール:**

1. https://git-scm.com/download/win にアクセス
2. インストーラーをダウンロード
3. デフォルト設定でインストール

**確認:**
```powershell
git --version
```

### 4.2 プロジェクトの取得

**PowerShellまたはコマンドプロンプトで:**

```powershell
# ホームディレクトリに移動
cd $HOME

# リポジトリをクローン
git clone https://github.com/onodera22ten/CQOx_gen.git

# プロジェクトディレクトリに移動
cd CQOx_gen
```

**ファイル確認:**
```powershell
dir
```

**表示されるべきフォルダ:**
```
backend
frontend
docker-compose.yml
.env.example
README.md
```

### 4.3 環境変数の設定

**メモ帳で編集:**

```powershell
# サンプルファイルをコピー
copy .env.example .env

# メモ帳で開く
notepad .env
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

**保存:** `Ctrl + S` で保存して閉じる

---

## 5. データベースの準備

### 5.1 Docker Desktopが起動していることを確認

タスクバーにクジラのアイコンがあることを確認してください。

### 5.2 Dockerコンテナの起動

**PowerShellで:**

```powershell
cd $HOME\CQOx_gen

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

### 5.3 起動状態の確認

```powershell
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

### 5.4 Docker Desktopでの確認（GUI）

1. Docker Desktopを開く
2. **Containers** タブをクリック
3. `cqox_gen` というグループに3つのコンテナが表示される
4. すべてが緑色（Running）であることを確認

### 5.5 ログの確認

```powershell
# すべてのログを表示
docker compose logs

# バックエンドだけ表示
docker compose logs backend

# リアルタイムで表示（Ctrl+Cで終了）
docker compose logs -f
```

### 5.6 データベースの初期化

```powershell
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

## 6. アプリケーションの起動

### 6.1 ブラウザでアクセス

```
http://localhost:3000
```

### 6.2 ログイン

- **Email**: `admin@cqox.local`
- **Password**: `.env`ファイルで設定した`ADMIN_PASSWORD`

---

## 7. 動作確認

### 7.1 データセットのアップロード

1. 左メニュー → **"Data Management"**
2. **"Upload Dataset"** ボタン
3. CSVファイルを選択
4. **"Upload"**

### 7.2 因果推定の実行

1. 左メニュー → **"Causal Design & Evaluation"**
2. データセット選択
3. Treatment/Outcome/Feature カラム選択
4. **"Train Models"**

---

## 8. トラブルシューティング

### 8.1 「WSL 2 installation is incomplete」エラー

**原因:** WSL2が正しくインストールされていない。

**解決方法:**

1. **管理者権限でPowerShellを開く**
2. 以下を実行:

```powershell
# WSLを更新
wsl --update

# WSL2をデフォルトに設定
wsl --set-default-version 2

# 確認
wsl --list --verbose
```

### 8.2 「Docker Desktop is starting...」が終わらない

**原因:** WSL2との統合に問題がある。

**解決方法:**

```powershell
# Docker Desktopを完全に終了
wsl --shutdown

# Docker Desktopを再起動
# スタートメニューから Docker Desktop を起動
```

### 8.3 「Cannot connect to the Docker daemon」エラー

**原因:** Docker Desktopが起動していない。

**解決方法:**

1. スタートメニューから **Docker Desktop** を起動
2. タスクバーのクジラアイコンが白色になるまで待つ
3. 再試行:

```powershell
docker compose up -d
```

### 8.4 ポート競合エラー

**エラー:**
```
Error: bind: address already in use
```

**解決方法:**

```powershell
# 使用中のポートを確認
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# プロセスIDを確認して停止
taskkill /PID <プロセスID> /F
```

### 8.5 Hyper-V関連エラー

**エラー:**
```
Hardware assisted virtualization and data execution protection must be enabled in the BIOS
```

**解決方法:**

1. **BIOSで仮想化を有効化**
   - PC起動時に `F2` / `Del` / `F10` キーを押す（PCによって異なる）
   - **Virtualization Technology** を Enabled に設定
   - 保存して再起動

2. **Hyper-Vを有効化**

```powershell
# 管理者権限でPowerShellを開く
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All

# 再起動
```

### 8.6 Windows Defender / ファイアウォールのブロック

**症状:** コンテナが起動しない、またはネットワークエラー

**解決方法:**

1. **Windows セキュリティ** を開く
2. **ファイアウォールとネットワーク保護**
3. **アプリの通過を許可**
4. **Docker Desktop** を探して、両方（プライベート/パブリック）にチェック

### 8.7 パフォーマンスが遅い

**原因:** Dockerのリソース制限

**解決方法:**

1. Docker Desktop を開く
2. **Settings** → **Resources**
3. **CPUs**: 4以上
4. **Memory**: 8GB以上
5. **Swap**: 2GB以上
6. **Apply & Restart**

### 8.8 すべてをリセット

```powershell
# すべて停止
docker compose down

# データも削除（注意：データが消えます）
docker compose down -v

# イメージも削除
docker compose down --rmi all

# Dockerのキャッシュをクリア
docker system prune -a

# WSLを再起動
wsl --shutdown

# Docker Desktopを再起動

# 再構築
docker compose up -d --build
docker compose exec backend python cqox/db/init_db.py
```

---

## 9. コマンド一覧（クイックリファレンス）

### 起動・停止

```powershell
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

```powershell
# コンテナ一覧
docker compose ps

# ログ表示
docker compose logs
docker compose logs -f backend

# リソース使用状況
docker stats
```

### コンテナ操作

```powershell
# コンテナの中に入る
docker compose exec backend bash
docker compose exec postgres bash

# コマンド実行
docker compose exec backend python cqox/db/init_db.py

# 再起動
docker compose restart backend
```

---

## 10. まとめ

### 起動手順（まとめ）

```powershell
cd $HOME\CQOx_gen
copy .env.example .env
notepad .env  # パスワード設定
docker compose up -d
docker compose exec backend python cqox/db/init_db.py
# ブラウザで http://localhost:3000 を開く
```

### 停止手順

```powershell
docker compose stop
```

### 再起動手順

```powershell
docker compose up -d
```

---

## 11. Windows固有の注意点

### 11.1 パスの違い

Windowsではパスの区切り文字が異なります:

- **Windows**: `C:\Users\username\CQOx_gen`
- **Linux/Mac**: `/home/username/CQOx_gen`

PowerShellでは両方使えますが、`\` を推奨。

### 11.2 ファイルの改行コード

Gitで取得したファイルの改行コードに注意:

```powershell
# Gitの設定を確認
git config --global core.autocrlf

# trueに設定（Windows推奨）
git config --global core.autocrlf true
```

### 11.3 ディスク容量の管理

```powershell
# Dockerのディスク使用状況確認
docker system df

# 不要なイメージ/コンテナを削除
docker system prune -a

# WSL2のディスク最適化
wsl --shutdown
Optimize-VHD -Path $env:LOCALAPPDATA\Docker\wsl\data\ext4.vhdx -Mode Full
```

### 11.4 WSL2とWindowsのファイル共有

WSL2内のファイルにWindowsからアクセス:

```
\\wsl$\Ubuntu\home\username\CQOx_gen
```

エクスプローラーのアドレスバーに入力。

---

## 12. よくある質問（Windows版）

### Q1: Windows Homeでも動きますか？

**A:** はい、Windows 10/11 Home でも動作します。
WSL2とDocker Desktopが対応しています。

### Q2: Hyper-Vは必要ですか？

**A:** WSL2を使う場合、Hyper-Vは不要です（自動で使われます）。
Windows Proの場合、どちらでも選択できます。

### Q3: PowerShellとコマンドプロンプトの違いは？

**A:** どちらでも使えますが、PowerShellを推奨します：

- **PowerShell**: 新しい、高機能
- **コマンドプロンプト**: 古い、互換性重視

### Q4: WSL2内でコマンドを実行したい

**A:** 以下の方法があります：

**方法1: WSLを起動**
```powershell
wsl
# Ubuntuが起動します
cd ~/CQOx_gen
```

**方法2: wslコマンドで実行**
```powershell
wsl -d Ubuntu cd ~/CQOx_gen && docker compose ps
```

### Q5: アンチウイルスソフトがブロックする

**A:** Docker関連のフォルダを除外リストに追加:

- `%LOCALAPPDATA%\Docker`
- `%APPDATA%\Docker`
- `C:\Program Files\Docker`

---

## 13. ショートカット（Windows）

```powershell
# PowerShellのエイリアスを設定（オプション）
Set-Alias -Name dc -Value docker-compose

# プロファイルに保存
Add-Content $PROFILE "Set-Alias -Name dc -Value docker-compose"

# 使用例
dc up -d
dc ps
dc logs -f
```

---

**お疲れ様でした！** 🎉

Windowsでの実装が完了しました。
