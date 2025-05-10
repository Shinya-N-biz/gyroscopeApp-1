#!/bin/bash

echo "=== アセットディレクトリを作成します ==="

# プロジェクトのルートディレクトリに移動
cd "$(dirname "$0")"

# assets/imagesディレクトリを作成
mkdir -p assets/images

echo "✅ assets/imagesディレクトリを作成しました"

# 画像のダミーファイルを作成
# 注意: 実際の画像ファイルを配置してください。これは一時的なものです。
echo "ダミー画像ファイルを作成しています..."

# ダミー画像ファイル作成（本番環境では実際の画像ファイルに置き換えてください）
cat > assets/images/situp_down.png << 'EOL'
PNG

   IHDR          v^_   sRGB ®Î é   gAMA  ±üa   PLTE   ÿÿÿ   tRNS @æØf   IDATxc`    Ï£6;    IEND®B`
EOL

cat > assets/images/situp_middle.png << 'EOL'
PNG

   IHDR          v^_   sRGB ®Î é   gAMA  ±üa   PLTE   ÿÿÿ   tRNS @æØf   IDATxc`    Ï£6;    IEND®B`
EOL

cat > assets/images/situp_up.png << 'EOL'
PNG

   IHDR          v^_   sRGB ®Î é   gAMA  ±üa   PLTE   ÿÿÿ   tRNS @æØf   IDATxc`    Ï£6;    IEND®B`
EOL

echo "✅ ダミー画像ファイルを作成しました"
echo "注意: これらのダミーファイルは実際の画像ファイルに置き換えてください"

# アクセス権を付与
chmod +x setup_assets.sh

echo "=== スクリプト終了 ==="
echo "これでアプリを再実行できます: flutter run -d chrome"
