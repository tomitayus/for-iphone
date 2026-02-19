# Multi-AI Diagram Automation

4つのAI（Claude, ChatGPT, Gemini, Grok）に同じ質問を並列で投げ、
回答を統合分析し、インタラクティブなHTML図解を自動生成するツール。
生成されたURLをメール・リマインダーに自動登録。

## アーキテクチャ

```
質問入力
   │
   ├─→ Claude API  ──┐
   ├─→ ChatGPT API ──┤
   ├─→ Gemini API  ──┼──→ Claude で統合分析 ──→ HTML図解生成
   └─→ Grok API    ──┘                              │
                                                     ├─→ Email通知
                                                     ├─→ Webhook (Slack/IFTTT等)
                                                     └─→ iOS Shortcut / Reminder
```

## セットアップ

### ワンコマンドセットアップ（推奨）

```bash
bash setup.sh
```

### 手動セットアップ

```bash
# 1. 依存パッケージのインストール
pip3 install --user -r requirements.txt

# 2. 環境変数の設定（.env.example をコピー）
cp .env.example .env

# 3. APIキーを設定（エディタで開いて編集）
nano .env
```

## 使い方

```bash
# 単一の質問
python3 main.py "量子コンピューティングの現状と将来は？"

# バッチモード（ファイルから複数質問）
python3 main.py --file questions.txt

# インタラクティブモード
python3 main.py --interactive

# 通知なし
python3 main.py "質問" --no-notify

# 出力先指定
python3 main.py "質問" --output ./my_diagram.html
```

## 必要なAPIキー

| AI | 環境変数 | 取得先 |
|----|---------|--------|
| Claude | `ANTHROPIC_API_KEY` | console.anthropic.com |
| ChatGPT | `OPENAI_API_KEY` | platform.openai.com |
| Gemini | `GOOGLE_AI_API_KEY` | aistudio.google.com |
| Grok | `XAI_API_KEY` | console.x.ai |

## 出力

生成されるHTMLファイルには以下が含まれます:

- **統合サマリー**: 全AIの回答を統合した要約
- **関係性ダイアグラム**: ノード・エッジによるSVG図解
- **一致点（Consensus）**: 全AIが合意したポイント
- **相違点（Differences）**: AIごとの見解の違い
- **独自洞察（Unique Insights）**: 特定のAIだけが言及した点
- **信頼性メモ**: 情報の信頼性に関する注意
- **個別回答**: 各AIの元回答（折りたたみ表示）

## iOS連携

詳細は [ios_shortcut_guide.md](./ios_shortcut_guide.md) を参照。

## プロジェクト構造

```
for-iphone/
├── main.py                  # エントリーポイント・CLI
├── src/
│   ├── ai_clients.py        # 4つのAI API並列呼び出し
│   ├── synthesizer.py       # Claude による回答統合
│   ├── renderer.py          # HTML図解生成（Jinja2）
│   └── notifier.py          # Email/Webhook/iOS通知
├── templates/
│   └── diagram.html         # HTMLテンプレート
├── setup.sh                 # ワンコマンドセットアップ
├── .env.example             # 環境変数テンプレート
├── requirements.txt         # Python依存パッケージ
├── ios_shortcut_guide.md    # iOS連携ガイド
└── README.md
```

## 代替アプローチ

本ツール以外にも、以下のような方法で同様のワークフローを実現できます:

### 1. n8n / Make.com（ノーコード）
ビジュアルワークフローエディタで各API呼び出しをノードとして接続。
プログラミング不要でメンテナンスが容易。

### 2. GitHub Actions（スケジュール実行）
`.github/workflows/` にYAMLを配置し、cron で定期実行。
GitHub Pages で自動ホスティングも可能。

### 3. Apple Shortcuts 単体
iPhoneの「ショートカット」アプリだけで各APIを呼び出すことも可能。
ただし処理が複雑になりデバッグが困難。

### 4. Zapier
Webhook → AI API → Email/Reminder の連携をGUIで設定。
月間タスク数に制限あり。

### 5. LangChain / CrewAI
Pythonのマルチエージェントフレームワークで、
より高度なAI間の対話・議論を実装可能。
