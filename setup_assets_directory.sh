#!/bin/bash

echo "=== アセットディレクトリを設定しています ==="

# プロジェクトのルートディレクトリに移動
cd "$(dirname "$0")"

# 必要なディレクトリを作成
mkdir -p assets/images
mkdir -p assets/audio

echo "✅ ディレクトリ構造を作成しました:"
echo "  - assets/images/ (腹筋画像用)"
echo "  - assets/audio/ (音楽ファイル用)"
echo ""
echo "👉 次の手順:"
echo "1. 以下のコマンドで音楽ファイルをコピーしてください:"
echo "   cp /path/to/your/1.mp3 assets/audio/"
echo ""
echo "2. Flutter dependenciesを更新してください:"
echo "   flutter pub get"

# 権限を付与
chmod +x setup_assets_directory.sh

echo "=== セットアップ完了 ==="
