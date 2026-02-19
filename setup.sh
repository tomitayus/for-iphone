#!/bin/bash
# Multi-AI Diagram Automation - セットアップスクリプト
set -e

echo "=== Multi-AI Diagram Automation Setup ==="
echo ""

# Python3 チェック
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 が見つかりません"
    echo "Homebrew でインストール: brew install python3"
    exit 1
fi

echo "Python3: $(python3 --version)"
echo ""

# 依存パッケージのインストール
echo "[1/3] 依存パッケージをインストール中..."
pip3 install --user -r requirements.txt
echo ""

# .env ファイルの作成
echo "[2/3] .env ファイルを作成中..."
if [ -f .env ]; then
    echo "  .env は既に存在します。スキップします。"
else
    cp .env.example .env
    echo "  .env を作成しました。APIキーを設定してください。"
fi
echo ""

# output ディレクトリの作成
echo "[3/3] output ディレクトリを作成中..."
mkdir -p output
echo ""

echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "  1. .env ファイルを編集してAPIキーを設定"
echo "     nano .env"
echo ""
echo "  2. 実行"
echo "     python3 main.py \"あなたの質問\""
echo ""
