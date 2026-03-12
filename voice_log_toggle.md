# Voice Log Toggle ショートカット設計書

アクションボタン1回で録音開始、もう1回で停止。ポケット内で完結する音声メモショートカット。

---

## 概要

| 押下 | 触覚フィードバック | 動作 |
|------|-------------------|------|
| 1回目（録音開始） | ブッ（強×1） | フラグ作成 → 消音ON → JPR録音開始 |
| 2回目（録音停止） | ブブッ（弱×2） | フラグ削除 → 消音OFF → JPR録音停止 |

**状態管理**: iCloud Drive上のファイルフラグで録音中/停止中を判定
**録音制御**: Just Press Record の URL スキーム `justpressrecord://toggle`
**通知方式**: 触覚フィードバック（画面を見ずに状態がわかる）

---

## iOS ショートカット構成（全7アクション）

### ショートカット名: `Voice Log Toggle`

```
┌─────────────────────────────────────────────────┐
│ アクション 1: ファイルの存在確認                      │
│   ファイルパス: /Shortcuts/VoiceLog/.recording     │
│   (iCloud Drive)                                  │
├─────────────────────────────────────────────────┤
│ アクション 2: if ファイルが存在する → 録音停止フロー    │
│                                                   │
│   2a: ファイルを削除                                │
│       /Shortcuts/VoiceLog/.recording               │
│                                                   │
│   2b: 消音モードを設定 → OFF                        │
│       「消音モードを設定」アクション                   │
│                                                   │
│   2c: 触覚フィードバック（弱 × 2回）                  │
│       「デバイスを振動させる」× 2                     │
│       → 0.15秒待機 → もう1回                        │
│                                                   │
│   2d: URLを開く                                    │
│       justpressrecord://toggle                     │
│       （録音を停止）                                 │
│                                                   │
├─────────────────────────────────────────────────┤
│ アクション 3: otherwise → 録音開始フロー              │
│                                                   │
│   3a: フォルダ作成（初回のみ）                        │
│       /Shortcuts/VoiceLog/                         │
│                                                   │
│   3b: テキストファイルを保存                          │
│       内容: タイムスタンプ（現在の日時）               │
│       保存先: /Shortcuts/VoiceLog/.recording        │
│                                                   │
│   3c: 消音モードを設定 → ON                         │
│       （録音中に通知音が入らないように）               │
│                                                   │
│   3d: 触覚フィードバック（強 × 1回）                  │
│       「デバイスを振動させる」                        │
│                                                   │
│   3e: URLを開く                                    │
│       justpressrecord://toggle                     │
│       （録音を開始）                                 │
│                                                   │
├─────────────────────────────────────────────────┤
│ アクション 4: end if                               │
└─────────────────────────────────────────────────┘
```

---

## アクションボタンへの割り当て

1. **設定** → **アクションボタン** → **ショートカット**
2. 「Voice Log Toggle」を選択

---

## ステップバイステップ作成手順

### 準備
- [Just Press Record](https://apps.apple.com/app/just-press-record/id1033342465) をインストール
- JPR を一度起動し、マイクの権限を許可

### ショートカットの作成

#### 1. フラグファイルの存在確認

| 設定項目 | 値 |
|---------|------|
| アクション | **ファイルにフィルタを適用** または **Get File** |
| サービス | iCloud Drive |
| パス | `/Shortcuts/VoiceLog/.recording` |
| エラー時 | 続行（ファイルが無い場合にエラーにしない） |

> **注意**: iOS ショートカットでは「ファイルの存在確認」を直接行うアクションがありません。
> 代わりに **Get File** を使い、**If** で「結果に値がある」かどうかで分岐します。

#### 2. If 分岐: 録音中 → 停止

```
If 「Get Fileの結果」に値がある
```

**2a. フラグファイル削除**
- アクション: **Delete File**
- パス: `/Shortcuts/VoiceLog/.recording`

**2b. 消音モード OFF**
- アクション: **消音モードを設定**
- 値: **オフ**

**2c. 触覚フィードバック（停止通知: 弱×2）**
- アクション: **Play Haptic**  →  pattern: `notification-warning` (弱い振動)
- アクション: **Wait** → 0.15秒
- アクション: **Play Haptic** →  pattern: `notification-warning`

**2d. JPR 録音停止**
- アクション: **URLを開く**
- URL: `justpressrecord://toggle`

#### 3. Otherwise: 待機中 → 録音開始

**3a. フラグファイル作成**
- アクション: **テキスト** → `Recording started at [Current Date]`
- アクション: **Save File**
- 保存先: `/Shortcuts/VoiceLog/.recording`
- 上書き: はい

**3b. 消音モード ON**
- アクション: **消音モードを設定**
- 値: **オン**

**3c. 触覚フィードバック（開始通知: 強×1）**
- アクション: **Play Haptic** → pattern: `notification-success` (強い振動)

**3d. JPR 録音開始**
- アクション: **URLを開く**
- URL: `justpressrecord://toggle`

#### 4. End If

---

## 制約・注意事項

### Just Press Record URL スキーム

| URL | 動作 |
|-----|------|
| `justpressrecord://` | アプリを開く |
| `justpressrecord://toggle` | 録音の開始/停止をトグル |
| `justpressrecord://record` | 録音開始（すでに録音中なら無効） |
| `justpressrecord://stop` | 録音停止 |

### 触覚フィードバックの制限

- `Play Haptic` アクションは iOS 17.2+ で利用可能
- ロック画面/バックグラウンドでも動作する
- Apple Watch ペアリング中は Watch 側にも振動が伝わる

### 消音モード自動制御

- 録音開始時に自動で消音ON → 通知音の混入を防止
- 録音停止時に自動で消音OFF → 通常状態に復帰
- 手動で消音を変更した場合、フラグとの不整合に注意

### ロック画面での動作

- アクションボタンは **ロック画面でもショートカットを実行可能**
- ただし「URLを開く」でJPRが起動する際、**初回のみロック解除が必要**な場合がある
- JPRがバックグラウンドで残っていれば、ロック解除不要で録音開始される

---

## 将来拡張: JPR → Whisper パイプライン

### 概要
録音ファイルを自動的に Whisper（文字起こし）に送り、テキストログ化する。

### パイプライン構想

```
JPR録音停止
    ↓
iCloud Drive に .m4a 保存（JPR自動）
    ↓
ショートカット or サーバー側で検知
    ↓
Whisper API で文字起こし
    ↓
テキストをメモ/ファイルに保存
```

### 実装方針（未確認・要検証）

1. **JPR の保存先**: JPR は録音を iCloud Drive の `Just Press Record/` フォルダに自動保存
2. **ファイル検知**: ショートカットの「Automation → ファイル受信時」、またはサーバー側での iCloud 同期監視
3. **Whisper API 連携**: `server.py` に `/transcribe` エンドポイントを追加し、音声ファイルを受け取って文字起こし
4. **連携例**:
   ```python
   # server.py に追加する想定のエンドポイント
   @app.post("/transcribe")
   async def transcribe(file: UploadFile):
       import openai
       client = openai.OpenAI()
       transcript = client.audio.transcriptions.create(
           model="whisper-1",
           file=file.file,
       )
       return {"text": transcript.text}
   ```

### 未確認事項
- [ ] JPR が iCloud Drive のどのパスに保存するか（`/Just Press Record/` ?）
- [ ] JPR の録音ファイル形式（.m4a? .wav?）
- [ ] ショートカット側からの自動トリガーが可能か
- [ ] JPR 録音停止後、ファイルが iCloud に同期されるまでの遅延

---

## クイックリファレンス

```
アクションボタン
    → Voice Log Toggle ショートカット
        → ファイルフラグ確認 (.recording)
            ├─ なし → 作成 → 消音ON → 強振動 → JPR開始
            └─ あり → 削除 → 消音OFF → 弱振動×2 → JPR停止
```
