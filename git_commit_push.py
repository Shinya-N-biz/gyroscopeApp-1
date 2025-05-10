#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import datetime
import sys

def run_command(command):
    """指定されたコマンドを実行し、結果を表示する"""
    print(f"実行: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               text=True, capture_output=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"エラー: {e}")
        if e.stderr:
            print(e.stderr)
        return False

def git_commit_push():
    """プロジェクトをコミットしてGitHubにプッシュする"""
    # 現在のディレクトリを確認
    current_dir = os.path.basename(os.getcwd())
    print(f"現在のディレクトリ: {current_dir}")
    
    # リポジトリの状態を確認
    if not run_command("git status"):
        print("このディレクトリはGitリポジトリではないか、Gitがインストールされていません。")
        if input("リポジトリを初期化しますか？ (y/n): ").lower() == 'y':
            run_command("git init")
        else:
            return False
    
    # リモートリポジトリの設定を確認
    remote_check = subprocess.run("git remote -v", shell=True, text=True, capture_output=True)
    target_remote = "https://github.com/Eiji-Y-work/gyroscopeApp.git"
    
    if "origin" not in remote_check.stdout:
        print("リモートリポジトリ'origin'が設定されていません。")
        if input(f"'{target_remote}'をリモートとして設定しますか？ (y/n): ").lower() == 'y':
            run_command(f"git remote add origin {target_remote}")
        else:
            return False
    
    # 変更をステージングする
    if not run_command("git add ."):
        print("変更のステージングに失敗しました。")
        return False
    
    # コミットメッセージを入力または自動生成
    commit_message = input("コミットメッセージを入力してください (Enterで自動生成): ")
    if not commit_message:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = f"Update at {now}"
    
    # 変更をコミット
    if not run_command(f'git commit -m "{commit_message}"'):
        print("コミットに失敗しました。")
        return False
    
    # 変更をプッシュ
    branch_name = "main"  # またはmasterなど、必要に応じて変更してください
    push_command = input(f"ブランチ名を入力してください (Enterで '{branch_name}' を使用): ")
    if push_command:
        branch_name = push_command
    
    if not run_command(f"git push -u origin {branch_name}"):
        print(f"'{branch_name}'ブランチへのプッシュに失敗しました。")
        print("次のコマンドを試してみてください: git push --force origin " + branch_name)
        return False
    
    print("コミットとプッシュが正常に完了しました！")
    return True

if __name__ == "__main__":
    print("Gitリポジトリへのコミットとプッシュを開始します。")
    git_commit_push()
    input("Enterキーを押して終了...")
