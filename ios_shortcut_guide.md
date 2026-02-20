# iOS ショートカット連携ガイド

このガイドでは、iPhoneからMulti-AI Diagram Automationを操作する方法を説明します。

---

## 方法0: Web API + iOS ショートカット（推奨）

サーバーを起動し、iPhoneの「ショートカット」アプリからHTTPリクエストで質問を送信します。

### サーバーの起動

```bash
# ローカルネットワークに公開（iPhoneからアクセスするため）
python3 server.py --host 0.0.0.0 --port 8000
# または
python3 main.py --server --host 0.0.0.0 --port 8000
```

サーバーのIPアドレスを確認:
```bash
# macOS
ipconfig getifaddr en0
# 例: 192.168.1.100
```

### ブラウザから使う

iPhoneのSafariで `http://192.168.1.100:8000` にアクセスするだけで使えます。

### iOS ショートカットの作成（1タップで質問送信）

**ショートカット名:** `AI図解`

1. **テキストを要求** → 「質問を入力」
2. **URLの内容を取得**（POST）
   - URL: `http://192.168.1.100:8000/ask/sync`
   - ヘッダー: `Content-Type: application/json`
   - 本文（JSON）: `{"question": "（要求した入力）"}`
3. **辞書の値を取得** → キー `diagram_url`
4. **URL** → `http://192.168.1.100:8000` + 上記の値
5. **Webページを表示**（またはSafariで開く）

### API エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| `GET` | `/` | Web UI（ブラウザ用） |
| `POST` | `/ask` | 非同期で質問送信（即座にjob_id返却） |
| `POST` | `/ask/sync` | 同期で質問送信（完了まで待つ） |
| `GET` | `/jobs` | ジョブ一覧 |
| `GET` | `/jobs/{id}` | ジョブ状態確認 |
| `GET` | `/diagrams/{filename}` | 生成されたHTML図解を取得 |

### curl での使用例

```bash
# 同期（完了まで待つ）
curl -X POST http://localhost:8000/ask/sync \
  -H "Content-Type: application/json" \
  -d '{"question": "量子コンピューティングの現状は？"}'

# 非同期（すぐ返る）
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "量子コンピューティングの現状は？"}'

# 状態確認
curl http://localhost:8000/jobs/abc123def456
```

---

## 方法1: iOS ショートカットで自動リマインダー登録

### ステップ1: ショートカットの作成

iPhoneの「ショートカット」アプリで以下のショートカットを作成:

**ショートカット名:** `AddDiagramReminder`

1. **ショートカット入力を受け取る** → URL
2. **テキスト** → `[AI Diagram] {入力}`
3. **新規リマインダーを追加**
   - タイトル: 上記テキスト
   - メモ: ショートカット入力(URL)
   - リスト: 任意のリマインダーリスト
4. **結果を表示** → 「リマインダーに追加しました」

### ステップ2: サーバーからのトリガー

このスクリプトの出力に表示される `shortcuts://` URLをiPhoneで開くと
自動的にショートカットが実行されます。

---

## 方法2: IFTTT / Make.com Webhook連携

### IFTTT設定
1. IFTTT で Webhook トリガーを作成
2. アクションに「iOS Reminders」または「Email」を設定
3. `.env` の `WEBHOOK_URL` にIFTTTのWebhook URLを設定

```
WEBHOOK_URL=https://maker.ifttt.com/trigger/ai_diagram/with/key/YOUR_KEY
```

### Make.com (Integromat) 設定
1. Make.com でWebhookモジュールを作成
2. Apple Reminders / Gmail モジュールを接続
3. `.env` の `WEBHOOK_URL` にMake.comのWebhook URLを設定

---

## 方法3: Pushover / Pushcut（iOSプッシュ通知）

### Pushcut（推奨）
Pushcutを使うと、通知をタップした時にショートカットを実行できます。

1. Pushcut アプリをインストール
2. サーバーアクションを設定
3. Webhook URLを `.env` に設定

### Pushover
1. Pushover アプリをインストール
2. API トークンを取得
3. Webhook で通知を送信

---

## 方法4: GitHub Pages で自動ホスティング

生成されたHTMLをGitHub Pagesで公開すると、
どのデバイスからでもアクセス可能なURLが得られます。

```bash
# output/ ディレクトリを gh-pages ブランチにデプロイ
git subtree push --prefix output origin gh-pages
```

`.env` に公開URLを設定:
```
PUBLIC_BASE_URL=https://username.github.io/for-iphone/
```

---

## 方法5: iCloud Drive 経由

1. `OUTPUT_DIR` をiCloud Driveのパスに設定
2. 生成されたHTMLがiPhone/iPadから直接アクセス可能に

```
OUTPUT_DIR=~/Library/Mobile Documents/com~apple~CloudDocs/AI-Diagrams/
```
