# iOS ショートカット連携ガイド

このガイドでは、Multi-AI Diagram Automationで生成されたHTMLダイアグラムを
iPhoneのリマインダーやメールに自動登録する方法を説明します。

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
