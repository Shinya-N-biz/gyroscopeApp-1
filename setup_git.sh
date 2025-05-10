#!/bin/bash

echo "===== Git設定スクリプト ====="
echo "このスクリプトはGitの基本設定を行います。"
echo ""

# グローバル設定かローカル設定かを選択
read -p "設定をグローバル（すべてのリポジトリ）に適用しますか？(y/n): " global_choice

if [ "$global_choice" = "y" ] || [ "$global_choice" = "Y" ]; then
    # グローバル設定
    echo "グローバル設定を行います。"
    read -p "あなたの名前を入力してください: " user_name
    read -p "あなたのメールアドレスを入力してください: " user_email
    
    git config --global user.name "$user_name"
    git config --global user.email "$user_email"
    
    echo "グローバルGit設定が完了しました！"
else
    # ローカル設定（現在のリポジトリのみ）
    echo "このリポジトリのみに設定を適用します。"
    read -p "あなたの名前を入力してください: " user_name
    read -p "あなたのメールアドレスを入力してください: " user_email
    
    git config user.name "$user_name"
    git config user.email "$user_email"
    
    echo "ローカルGit設定が完了しました！"
fi

# 設定確認
echo ""
echo "現在の設定を確認します:"
echo "ユーザー名: $(git config user.name)"
echo "メールアドレス: $(git config user.email)"

# 基本的なGit操作ガイド
echo ""
echo "===== Git基本操作ガイド ====="
echo "1. 変更をステージングに追加: git add ."
echo "2. 変更をコミット: git commit -m \"コミットメッセージ\""
echo "3. リモートにプッシュ: git push origin main"
echo ""
echo "詳細なエラーメッセージが表示された場合は、そちらの指示に従ってください。"
