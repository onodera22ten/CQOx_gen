# CQOx デモ版 実装マニュアル（初心者向け）

**対象**: プログラミング初心者〜中級者
**所要時間**: 約10分
**前提知識**: なし（このマニュアルで全て説明します）

---

## 📋 目次

1. [デモ版とは？](#1-デモ版とは)
2. [必要な準備](#2-必要な準備)
3. [インストール](#3-インストール)
4. [起動方法](#4-起動方法)
5. [使い方](#5-使い方)
6. [トラブルシューティング](#6-トラブルシューティング)
7. [社内レビュー時の注意点](#7-社内レビュー時の注意点)

---

## 1. デモ版とは？

### 1.1 デモ版の特徴

**デモ版は「すぐ使える」社内レビュー用の簡易版です。**

| 項目 | デモ版 | 本格版 |
|------|--------|--------|
| 認証 | ❌ なし | ✅ あり |
| データベース | ❌ なし | ✅ PostgreSQL |
| 起動時間 | ⚡ 10秒 | 🐢 5分 |
| データ | CSV直接読み込み | DB保存 |
| 用途 | 社内レビュー | 本番運用 |

### 1.2 デモ版のメリット

✅ **URLを開くだけで使える**
- ログイン不要
- パスワード設定不要

✅ **インストールが簡単**
- Dockerなし
- データベースなし
- Python 3 だけでOK

✅ **軽量**
- ThinkPad 1台で完結
- 他のPCからLAN経由でアクセス可能

✅ **機能は完全**
- 7つの因果推定手法を搭載
- 本格版と同じ分析エンジン

### 1.3 デモ版のデメリット

❌ **データが保存されない**
- PC再起動で結果が消える
- 履歴が残らない

❌ **セキュリティなし**
- 誰でもアクセス可能
- 本番データは使えない

❌ **同時アクセスに弱い**
- 10人以上の同時アクセスは推奨しない

---

## 2. 必要な準備

### 2.1 必要なソフトウェア

#### ✅ Python 3.8以上

**確認方法:**
```bash
python3 --version
```

**期待される出力:**
```
Python 3.11.x
```

**インストール方法（Fedora/Linux）:**
```bash
# Python 3をインストール
sudo dnf install python3 python3-pip

# 確認
python3 --version
pip3 --version
```

**インストール方法（Ubuntu/Debian）:**
```bash
sudo apt update
sudo apt install python3 python3-pip

# 確認
python3 --version
pip3 --version
```

---

## 3. インストール

### 3.1 プロジェクトの場所を確認

```bash
# デモ版のディレクトリに移動
cd /home/hirokionodera/CQOx_gen/demo-version

# ファイル一覧を確認
ls -la
```

**表示されるべきファイル:**
```
backend/          ← バックエンド（Python）
frontend/         ← フロントエンド（HTML）
sample_data/      ← サンプルCSVデータ
start.sh          ← 起動スクリプト
README.md         ← 説明書
```

### 3.2 依存関係のインストール

**依存関係とは？**
アプリケーションが動くために必要な他のソフトウェア（ライブラリ）のことです。

```bash
# backendディレクトリに移動
cd backend

# 必要なライブラリをインストール
pip3 install -r requirements.txt
```

**インストールされるライブラリ:**
- `fastapi` - Webサーバー
- `uvicorn` - FastAPIを動かすツール
- `pandas` - データ分析
- `numpy` - 数値計算

**所要時間:** 約1〜2分

**成功時の出力（最後の方）:**
```
Successfully installed fastapi-0.104.x uvicorn-0.24.x pandas-2.x.x numpy-1.24.x
```

### 3.3 起動スクリプトに実行権限を付与

```bash
# プロジェクトのルートに戻る
cd /home/hirokionodera/CQOx_gen/demo-version

# 実行権限を付与
chmod +x start.sh

# 確認
ls -l start.sh
```

**期待される出力:**
```
-rwxr-xr-x 1 user user 1234 Nov 19 18:00 start.sh
```

`x` が付いていれば実行可能です。

---

## 4. 起動方法

### 4.1 標準的な起動（ローカルのみ）

**この方法で起動した場合:**
- 自分のPCだけでアクセス可能
- 他のPCからはアクセスできない

```bash
cd /home/hirokionodera/CQOx_gen/demo-version
./start.sh
```

**起動中の出力:**
```
🚀 CQOx Demo Version - Starting...

📦 依存関係をインストール中...
🔧 バックエンドを起動中 (ポート 8000)...
🎨 フロントエンドを起動中 (ポート 3000)...

✅ CQOx Demo が起動しました！

📍 アクセスURL:
   - ローカル: http://localhost:3000
   - LAN内:    http://192.168.1.100:3000

🔍 サンプルデータ: marketing_campaign_2024 (100行)
🧪 推定量: DR, IPW, DiD, IV, CF, SCM, RD

🛑 停止するには: pkill -f 'python3 main.py' && pkill -f 'http.server 3000'
```

### 4.2 LAN内の他PCからもアクセスできるようにする起動

**この方法で起動した場合:**
- 自分のPCからアクセス可能
- **同じネットワーク内の他のPCからもアクセス可能**

**手動起動（推奨：社内レビュー用）:**

**ターミナル1: バックエンド起動**
```bash
cd /home/hirokionodera/CQOx_gen/demo-version/backend
python3 main.py
```

**出力:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**ターミナル2: フロントエンド起動（新しいターミナルを開く）**
```bash
cd /home/hirokionodera/CQOx_gen/demo-version/frontend
python3 -m http.server 3000
```

**出力:**
```
Serving HTTP on 0.0.0.0 port 3000 (http://0.0.0.0:3000/) ...
```

### 4.3 ThinkPadのIPアドレスを確認

**他のPCからアクセスするために、ThinkPadのIPアドレスを確認します。**

```bash
# IPアドレスを確認
hostname -I
```

**出力例:**
```
192.168.1.100 fe80::1234:5678:abcd:ef01
```

最初の数字（例: `192.168.1.100`）があなたのIPアドレスです。

**または `ip addr` コマンド:**
```bash
ip addr show | grep "inet "
```

**出力例:**
```
inet 127.0.0.1/8 scope host lo
inet 192.168.1.100/24 brd 192.168.1.255 scope global wlp2s0
```

`192.168.1.100` がLAN内のIPアドレスです。

---

## 5. 使い方

### 5.1 ブラウザでアクセス

**自分のPC（ThinkPad）から:**
```
http://localhost:3000
```

**他のPC（同じネットワーク内）から:**
```
http://192.168.1.100:3000
```
（`192.168.1.100` は実際のIPアドレスに置き換えてください）

### 5.2 画面の説明

**画面構成:**

```
┌─────────────────────────────────────────────────────┐
│  🔬 CQOx Demo                                       │
│  Causal Query Optimizer - 因果推定プラットフォーム   │
│  [Demo Mode / Sample Data Only]                    │
├───────────────┬─────────────────────────────────────┤
│ 📊 分析設定   │                                     │
│               │                                     │
│ データセット  │        結果表示エリア                │
│ Treatment     │                                     │
│ Outcome       │                                     │
│ 推定量選択    │                                     │
│               │                                     │
│ [🚀 分析実行] │                                     │
└───────────────┴─────────────────────────────────────┘
```

### 5.3 分析の実行手順

**ステップ1: データセットを選択**

1. 左側の「データセット」ドロップダウンをクリック
2. `marketing_campaign_2024` を選択

**自動で表示される情報:**
- 100行 × 8列

**ステップ2: カラムを選択**

1. **Treatment カラム**: `treatment` を選択
   - これは「介入があったかどうか」を示す列です
   - 1 = 介入あり、0 = 介入なし

2. **Outcome カラム**: `revenue` を選択
   - これは「結果」を示す列です
   - 例: 売上、コンバージョン率など

**ステップ3: 推定量を選択**

デフォルトで7つすべてがチェック済みです：

- ✅ **DR** (Doubly Robust)
- ✅ **IPW** (Inverse Propensity Weighting)
- ✅ **DiD** (Difference-in-Differences)
- ✅ **IV** (Instrumental Variables)
- ✅ **CF** (Causal Forest)
- ✅ **SCM** (Structural Causal Model)
- ✅ **RD** (Regression Discontinuity)

**初回は全てチェックしたまま実行してください。**

**ステップ4: 分析を実行**

1. 「🚀 分析実行」ボタンをクリック
2. 数秒待つ（7つの推定量を計算中）

**実行中の表示:**
```
因果推定を実行中... (7個の推定量)
[ローディングアニメーション]
```

### 5.4 結果の見方

**分析完了後、2つのセクションが表示されます:**

#### ① 判定カード（大きなカード）

```
┌─────────────────────────────────┐
│  判定: Go                        │
│  Δ¥12.45M                       │
│  平均ATE: 12000 [10500, 13500]  │
│  CAS Score: 0.85 | Risk: 0.15   │
└─────────────────────────────────┘
```

**各項目の意味:**

- **判定**: Go/Canary/Hold
  - **Go**: 効果あり（信頼区間の下限が正）
  - **Canary**: 不確実（段階的に実装推奨）
  - **Hold**: 効果なし/リスクあり（信頼区間の上限が負）

- **Δ¥**: 収益インパクト（円換算）
  - 介入によって増加/減少する収益の予測値

- **平均ATE**: 平均処置効果
  - [下限, 上限] は95%信頼区間

- **CAS Score**: Causal Assurance Score（因果確信度）
  - 0.0〜1.0（高いほど確信度が高い）

- **Risk Score**: リスクスコア
  - 0.0〜1.0（低いほど安全）

#### ② 推定量別の結果（複数のカード）

各推定量ごとに以下が表示されます:

```
┌─────────────────────────┐
│ Doubly Robust           │
├─────────────────────────┤
│ ATE        12345.67     │
│ 95% CI    [10500, 13500]│
│ Treated群  50人         │
│ Control群  50人         │
└─────────────────────────┘
```

**比較のポイント:**

1. **ATEの一貫性**
   - 7つの推定量のATEが近い値 → 信頼性が高い
   - バラバラ → データに問題がある可能性

2. **信頼区間の幅**
   - 狭い → 精度が高い
   - 広い → サンプル数を増やす必要あり

3. **サンプル数**
   - Treated群とControl群のバランスを確認
   - 極端に偏っていると推定の精度が下がる

---

## 6. トラブルシューティング

### 6.1 「ModuleNotFoundError」エラー

**エラーメッセージ:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**原因:**
必要なライブラリがインストールされていない。

**解決方法:**
```bash
cd /home/hirokionodera/CQOx_gen/demo-version/backend
pip3 install -r requirements.txt
```

### 6.2 「Address already in use」エラー

**エラーメッセージ:**
```
OSError: [Errno 98] Address already in use
```

**原因:**
ポート8000または3000が既に使われている。

**解決方法1: 使用中のプロセスを確認**
```bash
# ポート8000を使っているプロセス
lsof -i :8000

# ポート3000を使っているプロセス
lsof -i :3000
```

**出力例:**
```
COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
python3 12345 user    4u  IPv4  12345      0t0  TCP *:8000 (LISTEN)
```

**プロセスを停止:**
```bash
kill -9 12345
```

**解決方法2: 一括停止**
```bash
# バックエンドを停止
pkill -f 'python3 main.py'

# フロントエンドを停止
pkill -f 'http.server 3000'
```

### 6.3 「No such file or directory: sample_data/...」エラー

**エラーメッセージ:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'sample_data/marketing_campaign_2024.csv'
```

**原因:**
バックエンドが間違ったディレクトリから起動されている。

**解決方法:**
```bash
# 必ずdemo-versionディレクトリから起動
cd /home/hirokionodera/CQOx_gen/demo-version

# backendディレクトリ内で起動
cd backend
python3 main.py
```

### 6.4 ブラウザで「localhost refused to connect」

**症状:**
`http://localhost:3000` にアクセスしても接続できない。

**確認事項:**

1. **バックエンドが起動しているか確認**
```bash
ps aux | grep "python3 main.py"
```

2. **フロントエンドが起動しているか確認**
```bash
ps aux | grep "http.server 3000"
```

3. **ポートが開いているか確認**
```bash
netstat -tuln | grep 3000
```

**解決方法:**
起動していない場合は再度起動してください。

### 6.5 他のPCからアクセスできない

**症状:**
ThinkPadでは動くが、他のPCから `http://192.168.1.100:3000` にアクセスできない。

**確認事項:**

1. **同じネットワークにいるか確認**
```bash
# ThinkPad側
hostname -I

# 他のPC側（Windowsの場合）
ipconfig

# 他のPC側（Mac/Linuxの場合）
ifconfig
```

最初の3つの数字が同じネットワーク（例: `192.168.1.x`）であることを確認。

2. **ファイアウォールを確認**
```bash
# ファイアウォールの状態確認
sudo firewall-cmd --state

# ポート3000と8000を開放
sudo firewall-cmd --add-port=3000/tcp --permanent
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

3. **pingで疎通確認**
```bash
# 他のPCから
ping 192.168.1.100
```

### 6.6 結果が表示されない

**症状:**
「分析実行」をクリックしても結果が表示されない。

**確認事項:**

1. **ブラウザのコンソールを確認**
   - F12キーを押す
   - "Console" タブを開く
   - エラーメッセージを確認

2. **バックエンドのログを確認**
   - ターミナルに戻る
   - エラーメッセージを確認

**よくあるエラー:**
```
CORS policy: No 'Access-Control-Allow-Origin' header
```

**解決方法:**
バックエンドを再起動してください。

---

## 7. 社内レビュー時の注意点

### 7.1 事前準備（レビュー開始前）

**1日前:**
- [ ] ThinkPadを完全に充電
- [ ] 依存関係をインストール
- [ ] 動作確認（自分で1回実行してみる）

**当日朝:**
- [ ] ThinkPadを電源に接続
- [ ] アプリケーションを起動
- [ ] IPアドレスを確認
- [ ] テスト実行（結果が表示されるか確認）

### 7.2 レビュー参加者への案内

**メールまたはSlackで共有:**

```
【CQOxデモ版 社内レビューのご案内】

下記URLにアクセスしてください：
http://192.168.1.100:3000

■ 確認事項
- データセット選択 → 分析実行の流れ
- 7つの推定量の結果表示
- Go/Canary/Hold判定の妥当性
- UIの使いやすさ

■ 操作手順
1. ブラウザで上記URLを開く
2. 左側「データセット」で marketing_campaign_2024 を選択
3. Treatment: treatment を選択
4. Outcome: revenue を選択
5. 「分析実行」をクリック
6. 結果を確認

■ フィードバックお願いします
- わかりにくい点
- 追加してほしい機能
- バグや不具合

■ 注意事項
- デモ版のため、データは保存されません
- ThinkPadの電源が切れるとアクセスできなくなります
```

### 7.3 レビュー中のチェックリスト

**操作性:**
- [ ] データセット選択が直感的か
- [ ] カラム選択がわかりやすいか
- [ ] 分析実行ボタンが見つけやすいか

**結果表示:**
- [ ] 判定（Go/Canary/Hold）が目立っているか
- [ ] Δ¥の意味が理解できるか
- [ ] 信頼区間の表示が適切か

**パフォーマンス:**
- [ ] 分析が2秒以内に完了するか
- [ ] 複数人が同時にアクセスしても問題ないか

**バグ:**
- [ ] エラーメッセージが出ていないか
- [ ] 結果が正しく表示されているか

### 7.4 レビュー後の停止

**参加者全員が退出後:**

```bash
# バックエンドを停止（Ctrl+Cまたは）
pkill -f 'python3 main.py'

# フロントエンドを停止（Ctrl+Cまたは）
pkill -f 'http.server 3000'

# 確認
ps aux | grep python3
```

---

## 8. よくある質問（FAQ）

### Q1: デモ版と本格版の違いは？

**A:** 主な違いは以下の通りです：

| 機能 | デモ版 | 本格版 |
|------|--------|--------|
| 認証 | なし | JWT + OAuth2 |
| DB | なし | PostgreSQL |
| データ保存 | なし | あり |
| 起動時間 | 10秒 | 5分 |
| セキュリティ | なし | あり |
| 用途 | レビュー | 本番 |

### Q2: サンプルデータを変更できますか？

**A:** はい、可能です。

```bash
# 新しいCSVを sample_data/ に配置
cp your_data.csv demo-version/sample_data/

# ファイル名に注意（拡張子は .csv）
```

**CSVファイルの要件:**
- UTF-8エンコーディング
- 1行目にカラム名
- Treatment列（0または1）
- Outcome列（数値）

### Q3: 100人以上でレビューできますか？

**A:** 推奨しません。

- **推奨**: 10人以下
- **最大**: 30人程度
- **理由**: データベースがないため、同時アクセスに弱い

100人以上の場合は本格版を使用してください。

### Q4: レビュー結果を保存できますか？

**A:** デフォルトでは保存されませんが、手動で保存できます。

**方法1: スクリーンショット**
- ブラウザで結果画面をスクリーンショット

**方法2: JSONファイル**
```bash
# artifacts/ ディレクトリに結果が保存されている
ls -la demo-version/artifacts/

# コピーして保存
cp demo-version/artifacts/*.json ~/backup/
```

### Q5: 本格版に移行するには？

**A:** 本格版の実装マニュアルを参照してください。

```bash
# 本格版のマニュアル
cat /home/hirokionodera/CQOx_gen/IMPLEMENTATION_GUIDE_PRODUCTION.md
```

---

## 9. まとめ

### 9.1 起動手順（まとめ）

```bash
# 1. ディレクトリに移動
cd /home/hirokionodera/CQOx_gen/demo-version

# 2. 依存関係インストール（初回のみ）
cd backend && pip3 install -r requirements.txt && cd ..

# 3. バックエンド起動（ターミナル1）
cd backend && python3 main.py

# 4. フロントエンド起動（ターミナル2）
cd frontend && python3 -m http.server 3000

# 5. ブラウザで開く
http://localhost:3000
```

### 9.2 停止手順

```bash
# Ctrl+C で停止
# または
pkill -f 'python3 main.py'
pkill -f 'http.server 3000'
```

### 9.3 社内レビュー用の簡易手順

```bash
# 起動
cd /home/hirokionodera/CQOx_gen/demo-version
./start.sh

# IPアドレス確認
hostname -I

# 参加者に案内
# http://[あなたのIP]:3000 を共有

# 停止
pkill -f 'python3 main.py' && pkill -f 'http.server 3000'
```

---

## 10. 次のステップ

デモ版のレビューが完了したら：

1. **フィードバックを収集**
   - 使いやすさ
   - 追加機能
   - バグ報告

2. **本格版への移行を検討**
   - 認証が必要か？
   - データを保存する必要があるか？
   - 複数ユーザで使うか？

3. **本格版の実装**
   - `IMPLEMENTATION_GUIDE_PRODUCTION.md` を参照

---

**お疲れ様でした！** 🎉

問題が発生した場合は、[トラブルシューティング](#6-トラブルシューティング)を参照してください。
