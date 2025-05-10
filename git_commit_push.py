#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
import datetime
import sys
import socket
import time

def check_internet_connection():
    """インターネット接続を確認する"""
    try:
        # githubへの接続をテスト (タイムアウト3秒)
        socket.create_connection(("github.com", 443), timeout=3)
        return True
    except (socket.timeout, socket.gaierror, OSError):
        return False

def run_command(command):
    """指定されたコマンドを実行し、結果を表示する"""
    print(f"実行: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                               text=True, capture_output=True)
        if result.stdout:
            print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"エラー: {e}")
        if e.stderr:
            print(e.stderr)
        return False, e.stderr

def git_commit_push():
    """プロジェクトをコミットしてGitHubにプッシュする"""
    # 現在のディレクトリを確認
    current_dir = os.path.basename(os.getcwd())
    print(f"現在のディレクトリ: {current_dir}")
    
    # インターネット接続の確認
    internet_available = check_internet_connection()
    if not internet_available:
        print("警告: インターネット接続が確認できません。GitHub.comにアクセスできない可能性があります。")
        print("ローカルでのコミットのみ行うことができます。")
        offline_mode = True
    else:
        print("インターネット接続: OK")
        offline_mode = False
    
    # リポジトリの状態を確認
    status_success, status_output = run_command("git status")
    if not status_success:
        print("このディレクトリはGitリポジトリではないか、Gitがインストールされていません。")
        if input("リポジトリを初期化しますか？ (y/n): ").lower() == 'y':
            run_command("git init")
        else:
            return False
    
    # 変更があるか確認
    has_changes = "nothing to commit" not in status_output
    
    # リモートリポジトリの確認と修正
    remote_success, remote_output = run_command("git remote -v")
    current_remote = None
    if remote_success and remote_output and "origin" in remote_output:
        # 現在のリモートURLを抽出
        for line in remote_output.split('\n'):
            if "origin" in line and "(fetch)" in line:
                current_remote = line.split()[1]
                print(f"現在のリモート: {current_remote}")
                break
    
    # リモートリポジトリの設定・変更
    target_remote = "https://github.com/Eiji-Y-work/gyroscopeApp.git"
    
    # リモートが設定されていない場合は設定する
    if not current_remote:
        print("リモートリポジトリ'origin'が設定されていません。")
        if input(f"'{target_remote}'をリモートとして設定しますか？ (y/n): ").lower() == 'y':
            run_command(f"git remote add origin {target_remote}")
    # 設定されているが異なる場合は変更するか尋ねる
    elif current_remote != target_remote:
        print(f"現在のリモート({current_remote})が目標のリモート({target_remote})と異なります。")
        if input("リモートURLを変更しますか？ (y/n): ").lower() == 'y':
            run_command(f"git remote set-url origin {target_remote}")
    
    # 変更がなければコミットをスキップ
    if not has_changes:
        print("変更がありません。コミットをスキップします。")
    else:
        # 変更をステージングする
        stage_success, _ = run_command("git add .")
        if not stage_success:
            print("変更のステージングに失敗しました。")
            return False
        
        # コミットメッセージを入力または自動生成
        commit_message = input("コミットメッセージを入力してください (Enterで自動生成): ")
        if not commit_message:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            commit_message = f"Update at {now}"
        
        # 変更をコミット
        commit_success, _ = run_command(f'git commit -m "{commit_message}"')
        if not commit_success:
            print("コミットに失敗しました。")
            return False
        print("変更がローカルにコミットされました。")
        
        # オフラインモードならプッシュをスキップ
        if offline_mode:
            print("オフラインモードで実行中のため、GitHubへのプッシュはスキップされました。")
            print("インターネット接続が回復したら、次のコマンドを実行してください:")
            print(f"git push -u origin main")
            return True
    
    # ブランチ名の取得
    branch_name = "main"  # デフォルト値
    branch_input = input(f"ブランチ名を入力してください (Enterで '{branch_name}' を使用): ")
    if branch_input:
        branch_name = branch_input
    
    # DNS問題のトラブルシューティング情報
    print("\nネットワーク接続を確認しています...")
    for i in range(3):
        if check_internet_connection():
            print("GitHub.comへの接続が確認できました。")
            break
        print(f"試行 {i+1}/3: GitHub.comへの接続を確認できません。再試行中...")
        time.sleep(1)
    else:
        print("\nネットワーク接続の問題があるようです。以下を確認してください:")
        print("1. インターネット接続が機能していること")
        print("2. VPNを使用している場合は一時的に無効にしてみてください")
        print("3. DNSの問題の場合は、/etc/hostsファイルにgithub.comのエントリを追加してみてください")
        print("\nDNSの代替設定として以下のコマンドを試すことができます:")
        print("echo '140.82.121.4 github.com' | sudo tee -a /etc/hosts")
        print("\nGitのプロキシ設定を確認/設定するには:")
        print("git config --global http.proxy")
        print("git config --global --unset http.proxy  # プロキシを削除")
        
        if input("\nGitコマンドのプロキシ設定を確認しますか？ (y/n): ").lower() == 'y':
            run_command("git config --get http.proxy")
            
        if input("ローカルのDNS解決で接続を試みますか？ (y/n): ").lower() == 'y':
            print("GitHubのIPアドレスを使用して接続を試みます...")
            target_remote = "https://github.com/Eiji-Y-work/gyroscopeApp.git"
            alt_remote = "https://140.82.121.4/Eiji-Y-work/gyroscopeApp.git"
            push_success, push_output = run_command(f"git push -u {alt_remote} {branch_name}")
            if push_success:
                print("代替IPアドレスでの接続に成功しました！")
                return True
        
        print("\nローカルコミットは保存されました。インターネット接続が回復したらプッシュしてください。")
        print(f"git push -u origin {branch_name}")
        return False
    
    # 認証方法の確認
    auth_method = input("認証方法を選択してください (1: SSH, 2: HTTPS トークン認証, 3: HTTPS パスワード認証) [2]: ") or "2"
    
    if auth_method == "1":
        # SSHを使用
        if current_remote and current_remote.startswith("https://"):
            ssh_url = f"git@github.com:{target_remote.split('github.com/')[1]}"
            if input(f"リモートURLをSSH形式に変更しますか？ ({ssh_url}) (y/n): ").lower() == 'y':
                run_command(f"git remote set-url origin {ssh_url}")
        # 通常のプッシュ試行
        push_success, push_output = run_command(f"git push -u origin {branch_name}")
        
    elif auth_method == "2":
        # アクセストークンを使用
        token = input("GitHubのアクセストークンを入力してください: ")
        if token:
            # ユーザー名を入力
            username = input("GitHubのユーザー名を入力してください: ")
            if username:
                token_url = f"https://{username}:{token}@github.com/{target_remote.split('github.com/')[1]}"
                # トークンURLで一時的にプッシュ
                push_success, push_output = run_command(f"git push -u {token_url} {branch_name}")
            else:
                print("ユーザー名が入力されていません。")
                return False
        else:
            print("トークンが入力されていません。")
            return False
            
    elif auth_method == "3":
        # 通常のHTTPS認証でプッシュ (Gitがパスワードを要求)
        print("通常のHTTPS認証でプッシュします。プロンプトが表示されたらユーザー名とパスワードを入力してください。")
        push_success, push_output = run_command(f"git push -u origin {branch_name}")
    else:
        print("無効な認証方法が選択されました。")
        return False
    
    # プッシュ結果の確認
    if 'push_success' in locals() and push_success:
        print("コミットとプッシュが正常に完了しました！")
        return True
    else:
        print(f"'{branch_name}'ブランチへのプッシュに失敗しました。")
        print("以下のコマンドを試すことができます:")
        print(f"git push --force origin {branch_name}")
        return False

if __name__ == "__main__":
    # スクリプトの作業ディレクトリを修正
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("Gitリポジトリへのコミットとプッシュを開始します。")
    result = git_commit_push()
    
    if result:
        print("処理が正常に完了しました。")
    else:
        print("処理が完了しましたが、一部エラーが発生しました。")
    
    input("Enterキーを押して終了...")