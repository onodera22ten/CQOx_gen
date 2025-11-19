# 🔬 CQOx Demo Version

**Causal Query Optimizer - デモ版**

社内レビュー用の簡易版です。ThinkPad 1台で完結し、URLアクセスのみで使用できます。

---

## ⚡ 5分クイックスタート

### 必要な環境
- Python 3.8+
- Linux（Fedora/Ubuntu等）または WSL

### 起動方法

```bash
cd demo-version
./start.sh
```

起動後、以下のURLにアクセス：
- **ローカル**: http://localhost:3000
- **LAN内の他PC**: http://[ThinkPadのIP]:3000

---

## 🎯 主な機能

### 1. 認証なし
- URLを開くだけで即座に使用可能
- ログイン不要

### 2. 7つの因果推定手法
- **DR**: Doubly Robust
- **IPW**: Inverse Propensity Weighting
- **DiD**: Difference-in-Differences
- **IV**: Instrumental Variables
- **CF**: Causal Forest
- **SCM**: Structural Causal Model
- **RD**: Regression Discontinuity

### 3. 1画面完結UI
- データセット選択 → カラム選択 → 推定量選択 → 分析実行
- すべて1つの画面で完結

### 4. 自動判定
- **Go**: 信頼区間の下限が正（効果あり）
- **Canary**: 不確実（段階的実装推奨）
- **Hold**: 信頼区間の上限が負（効果なし・リスク）

---

## 📊 サンプルデータ

### marketing_campaign_2024.csv
- **100行** × 8カラム
- 東京・大阪・福岡等の地域データ
- treatment（1/0）× revenue（outcome）

**カラム:**
- `user_id`: ユーザID
- `treatment`: 介入有無（1=処置群, 0=対照群）
- `revenue`: 収益（outcome変数）
- `age`: 年齢
- `gender`: 性別
- `region`: 地域
- `previous_purchases`: 過去購入回数
- `email_opens`: メール開封数

---

## 🛠️ アーキテクチャ

### バックエンド
- **FastAPI** (ポート 8000)
- **DBなし** - CSVファイル直接読み込み
- **結果保存** - artifacts/ にJSON形式で保存

### フロントエンド
- **Pure HTML/CSS/JavaScript**
- **ポート 3000** - Python http.server

### データフロー
```
1. ユーザがデータセット選択
2. バックエンドがCSVを読み込み
3. 7つの推定量を並列実行
4. 結果をJSON形式で返却
5. フロントエンドが可視化
```

---

## 🚀 使い方

### 1. ブラウザでアクセス
```
http://localhost:3000
```

### 2. 左側のサイドバーで設定
1. **データセット**: `marketing_campaign_2024` を選択
2. **Treatment カラム**: `treatment` を選択
3. **Outcome カラム**: `revenue` を選択
4. **推定量**: デフォルトで全7つが選択済み

### 3. 分析実行
「🚀 分析実行」ボタンをクリック

### 4. 結果確認
- **判定カード**: Go/Canary/Hold + Δ¥
- **推定量別結果**: ATE, 95% CI, サンプル数

---

## 🔍 技術詳細

### 因果推定の実装

#### Doubly Robust (DR)
```python
ate = E[Y|T=1] - E[Y|T=0]
Bootstrap 200回で95%信頼区間を計算
```

#### Causal Forest (CF)
- 条件付き効果（CATE）を推定
- 顧客セグメント別の効果を表示

#### その他
- IPW: Propensity score weighting（簡易版）
- DiD: 時系列がない場合は差分のみ
- IV: Instrumental variables（シミュレート版）
- SCM: 構造方程式モデル
- RD: Regression discontinuity

---

## ⚠️ 制約事項

### デモ版の制限
1. **DBなし** - PC再起動で結果が消える
2. **認証なし** - 誰でもアクセス可能
3. **1台限定** - ThinkPad起動中のみ利用可能
4. **サンプルデータのみ** - 本番データは使用不可

### 本番版との違い
| 機能 | デモ版 | 本格版 |
|------|--------|--------|
| 認証 | なし | JWT + OAuth2 |
| DB | なし | PostgreSQL |
| ユーザ | 単一 | マルチユーザ |
| データ | CSV | CSV/Parquet/DWH |
| 永続性 | なし | あり |
| 監視 | なし | Prometheus/Grafana |

---

## 🛑 停止方法

### 手動停止
```bash
pkill -f 'python3 main.py'
pkill -f 'http.server 3000'
```

### プロセス確認
```bash
ps aux | grep python3
```

---

## 📝 社内レビュー用チェックリスト

### UX確認
- [ ] URLアクセスだけで使えるか
- [ ] データセット選択が直感的か
- [ ] 7つの推定量が全て動作するか
- [ ] 結果表示が分かりやすいか

### 分析ロジック確認
- [ ] ATEの計算が正しいか
- [ ] 信頼区間が妥当か
- [ ] Go/Canary/Hold判定が適切か
- [ ] Δ¥の計算式を確認

### パフォーマンス
- [ ] 100行データの分析時間（目安: 1-2秒）
- [ ] 複数推定量の並列実行
- [ ] ブラウザのレスポンス

---

## 🔗 次のステップ

### 本格版への移行
デモ版の体験後、本格版（`/home/hirokionodera/CQOx_gen/`）では以下が追加されます：

1. **認証機能** - JWT + 管理者ログイン
2. **PostgreSQL** - データ永続化
3. **Docker Compose** - 一発起動
4. **ロゴ・ブランディング** - UI統一
5. **マルチユーザ対応** - 将来の拡張性

---

## 🐛 トラブルシューティング

### ポート競合エラー
```bash
# 既存プロセスを確認
lsof -i :8000
lsof -i :3000

# 該当プロセスを停止
kill -9 <PID>
```

### モジュールが見つからない
```bash
cd backend
pip3 install -r requirements.txt
```

### ThinkPadのIP確認
```bash
hostname -I
```

---

## 📞 サポート

社内レビュー中に問題が発生した場合：
1. `artifacts/` フォルダの結果JSONを確認
2. ブラウザのコンソールログを確認
3. バックエンドのログを確認（ターミナル出力）

---

## 📄 ライセンス

社内使用限定 - デモ版

---

**🤖 Generated with CQOx Demo Engine**
