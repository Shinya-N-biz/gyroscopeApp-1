#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import argparse
import platform
import datetime
import sys
import subprocess
import time
import shutil
import json
import re

def run_command(cmd, description="", timeout=None, show_output=True, show_progress=False):
    """コマンドを実行し、結果を表示する"""
    if description:
        print(f"\n===== {description} =====")
        print(f"実行: {cmd}")
    
    try:
        if show_output:
            if show_progress:
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                for line in iter(process.stdout.readline, ''):
                    if line:  # 空行をスキップ
                        print(line.rstrip())
                process.stdout.close()
                return_code = process.wait(timeout=timeout)
            else:
                result = subprocess.run(cmd, shell=True, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
                if result.stdout:
                    print(result.stdout)
                return_code = result.returncode
        else:
            result = subprocess.run(cmd, shell=True, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
            return_code = result.returncode
            stdout = result.stdout
        
        if return_code != 0 and show_output:
            print(f"エラー発生 (コード: {return_code})")
            if not show_progress:
                print(f"エラー詳細: {result.stdout}")
            return False, None
        
        return True, stdout if not show_output else None
    except subprocess.TimeoutExpired:
        print(f"タイムアウト: {cmd}")
        return False, None
    except Exception as e:
        print(f"例外発生: {e}")
        return False, None

def check_flutter_installation():
    """Flutter SDKのインストールを確認する"""
    flutter_path = shutil.which("flutter")
    if not flutter_path:
        print("Flutterが見つかりません。Flutterがインストールされ、PATHに追加されていることを確認してください。")
        return False
    
    print(f"Flutter確認済み:")
    flutter_version = get_flutter_version()
    print(flutter_version)
    return True

def get_flutter_version():
    """Flutterのバージョン情報を取得する"""
    try:
        result = subprocess.run("flutter --version", shell=True, check=True, text=True, capture_output=True)
        version_line = result.stdout.strip().split('\n')[0]
        return version_line
    except:
        return "不明"

def check_android_sdk():
    """Android SDKのインストールを確認する"""
    # ANDROID_HOME または ANDROID_SDK_ROOT 環境変数をチェック
    android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    
    if not android_home:
        # macOSならデフォルトの場所をチェック
        if platform.system() == "Darwin":
            default_paths = [
                os.path.expanduser('~/Library/Android/sdk'),
                '/Applications/Android Studio.app/Contents/sdk'
            ]
            for path in default_paths:
                if os.path.exists(path):
                    android_home = path
                    break
        # Windowsならデフォルトの場所をチェック
        elif platform.system() == "Windows":
            default_paths = [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android/Sdk'),
                os.path.join(os.environ.get('APPDATA', ''), 'Local/Android/Sdk')
            ]
            for path in default_paths:
                if os.path.exists(path):
                    android_home = path
                    break
    
    if not android_home or not os.path.exists(android_home):
        print("⚠️ Android SDKが見つかりません。Android Studioをインストールして、環境変数を設定してください。")
        return False
    
    # 一般的なAndroid SDK構成要素のチェック
    sdk_components = {
        'platform-tools': os.path.join(android_home, 'platform-tools'),
        'tools': os.path.join(android_home, 'tools'),
        'emulator': os.path.join(android_home, 'emulator')
    }
    
    for name, path in sdk_components.items():
        if not os.path.exists(path):
            print(f"⚠️ Android SDK {name}が見つかりません: {path}")
            if name == 'emulator':
                return False
    
    # adb コマンドがPATHにあるかチェック
    adb_path = shutil.which("adb")
    if not adb_path:
        print("⚠️ adbがPATHに設定されていません。Android Studioの設定を確認してください。")
        # それでも続行はできるようにする
    else:
        print(f"✅ adbパス: {adb_path}")
    
    # エミュレータコマンドがPATHにあるかチェック
    emulator_path = shutil.which("emulator")
    if not emulator_path:
        # 直接パスを探す
        if os.path.exists(os.path.join(android_home, 'emulator', 'emulator')):
            emulator_path = os.path.join(android_home, 'emulator', 'emulator')
            print(f"⚠️ emulatorがPATHに設定されていません。直接パスを使用します: {emulator_path}")
            os.environ['PATH'] = os.environ['PATH'] + os.pathsep + os.path.dirname(emulator_path)
        else:
            print("⚠️ emulatorコマンドが見つかりません。Android SDK Emulatorがインストールされているか確認してください。")
            return False
    else:
        print(f"✅ emulatorパス: {emulator_path}")
    
    print(f"✅ Android SDK確認済み: {android_home}")
    return True

def get_available_emulators():
    """利用可能なAndroidエミュレータの一覧を取得する"""
    print("\n🔍 利用可能なAndroidエミュレータを検索しています...")
    
    # 実行中のエミュレータを先に検出
    running_emulators = []
    success, adb_output = run_command("adb devices", show_output=False)
    if success and adb_output:
        adb_output = adb_output.decode('utf-8') if isinstance(adb_output, bytes) else adb_output
        for line in adb_output.strip().split('\n')[1:]:  # ヘッダー行をスキップ
            if "emulator-" in line and "device" in line:
                # エミュレータが起動している
                emulator_id = line.split()[0]
                # エミュレータIDからポート番号を抽出 (例: emulator-5554 -> 5554)
                port = emulator_id.split('-')[1]
                running_emulators.append(port)
    
    # 利用可能なエミュレータリストを取得
    success, output = run_command("emulator -list-avds", show_output=False)
    if not success or not output:
        print("⚠️ エミュレータの一覧取得に失敗しました。")
        return []
    
    emulators = []
    if isinstance(output, bytes):
        output = output.decode('utf-8')
    
    # エミュレータ名のリストを取得
    avd_names = output.strip().split('\n')
    
    # 各エミュレータの詳細情報を取得
    for i, name in enumerate(avd_names):
        if name:  # 空行をスキップ
            # エミュレータ詳細情報を取得
            avd_info = {}
            avd_info['name'] = name
            avd_info['id'] = name  # Androidではエミュレータ名がIDとなる
            
            # デフォルトは停止中
            avd_info['state'] = "停止中"
            
            # 実行中のエミュレータリストと照合（より正確な検出）
            if running_emulators:
                # AVDプロセスと起動済みエミュレータのマッピングを取得
                try:
                    # エミュレータが起動しているか確認（様々な方法で）
                    success, emu_ps = run_command("ps aux | grep 'qemu.*" + name + "' | grep -v grep", show_output=False)
                    if success and emu_ps and len(emu_ps) > 0:
                        avd_info['state'] = "実行中"
                except:
                    pass
            
            # エミュレータのAPIレベルやバージョンを取得（可能であれば）
            try:
                avd_info_path = os.path.expanduser(f"~/.android/avd/{name}.avd/config.ini")
                if os.path.exists(avd_info_path):
                    with open(avd_info_path, 'r') as f:
                        for line in f:
                            if line.startswith('target='):
                                api_target = line.strip().split('=')[1]
                                # APIレベルを解析（例: "android-33" -> "33"）
                                api_match = re.search(r'android-(\d+)', api_target)
                                api_level = api_match.group(1) if api_match else "不明"
                                avd_info['api_level'] = api_level
                                
                                # APIレベルからAndroidバージョンを推定
                                api_to_version = {
                                    '33': '13.0', '32': '12.1', '31': '12.0', 
                                    '30': '11.0', '29': '10.0', '28': '9.0',
                                    '27': '8.1', '26': '8.0', '25': '7.1',
                                    '24': '7.0', '23': '6.0', '22': '5.1'
                                }
                                avd_info['android_version'] = api_to_version.get(api_level, f"API {api_level}")
                                break
            except Exception as e:
                print(f"  ⚠️ エミュレータ情報の読み取りエラー ({name}): {e}")
                avd_info['api_level'] = "不明"
                avd_info['android_version'] = "不明"
            
            # ABIアーキテクチャを取得
            try:
                avd_info_path = os.path.expanduser(f"~/.android/avd/{name}.avd/config.ini")
                if os.path.exists(avd_info_path):
                    with open(avd_info_path, 'r') as f:
                        for line in f:
                            if line.startswith('abi.type='):
                                avd_info['abi'] = line.strip().split('=')[1]
                                break
            except:
                avd_info['abi'] = "不明"
            
            emulators.append(avd_info)
    
    print(f"🔍 検出したエミュレータ: {len(emulators)}台 (実行中: {len([e for e in emulators if e['state'] == '実行中'])}台)")
    return emulators

def print_emulator_list(emulators):
    """エミュレータの一覧を表示する"""
    if not emulators:
        print("利用可能なAndroidエミュレータがありません。")
        return
    
    print("\n===== 利用可能なAndroidエミュレータ =====")
    print(f"{'番号':^4} | {'名前':<25} | {'Android バージョン':<15} | {'API':<5} | {'ABI':<10} | {'状態':<10}")
    print("-" * 85)
    
    for i, emu in enumerate(emulators):
        android_ver = emu.get('android_version', '不明')
        api_level = emu.get('api_level', '??')
        abi = emu.get('abi', '不明')
        state = emu.get('state', '不明')
        print(f"{i+1:^4} | {emu['name']:<25} | {android_ver:<15} | {api_level:<5} | {abi:<10} | {state:<10}")

def boot_emulator(emulator_name, wait_time=60):
    """エミュレータを起動する"""
    print(f"\n🚀 エミュレータ「{emulator_name}」を起動しています...")
    
    # より正確に実行中のエミュレータを検出
    success, adb_output = run_command("adb devices", show_output=False)
    success2, ps_output = run_command(f"ps aux | grep '{emulator_name}' | grep -v grep", show_output=False)
    
    is_running = False
    if success and adb_output:
        adb_text = adb_output.decode('utf-8') if isinstance(adb_output, bytes) else adb_output
        if "emulator-" in adb_text and "device" in adb_text:
            is_running = True
    
    if success2 and ps_output and len(ps_output) > 0:
        is_running = True
    
    if is_running:
        print("✅ エミュレータは既に起動しています。そのまま使用します。")
        return True
    
    # バックグラウンドでエミュレータを起動
    if platform.system() == "Windows":
        start_cmd = f"start /B emulator -avd {emulator_name}"
    else:
        start_cmd = f"nohup emulator -avd {emulator_name} > /dev/null 2>&1 &"
    
    success, _ = run_command(start_cmd, "エミュレータ起動")
    if not success:
        print("⚠️ エミュレータの起動に失敗しました")
        return False
    
    # エミュレータの起動を待機
    print("⏳ エミュレータの起動を待機しています...")
    start_time = time.time()
    while time.time() - start_time < wait_time:
        success, output = run_command("adb devices", show_output=False)
        if success and output:
            devices_output = output.decode('utf-8') if isinstance(output, bytes) else output
            if "device" in devices_output and "emulator" in devices_output:
                # bootアニメーションが終了したか確認
                success, boot_output = run_command(
                    "adb shell getprop sys.boot_completed", show_output=False
                )
                if success and boot_output:
                    boot_status = boot_output.decode('utf-8').strip() if isinstance(boot_output, bytes) else boot_output.strip()
                    if boot_status == "1":
                        print(f"✅ エミュレータの起動が完了しました ({int(time.time() - start_time)}秒)")
                        # 追加の待機時間（UIの読み込み待ち）
                        time.sleep(2)
                        return True
        
        # 5秒ごとに状態を表示
        if int(time.time() - start_time) % 5 == 0:
            print(f"  起動中... {int(time.time() - start_time)}秒経過")
        
        time.sleep(1)
    
    print("⚠️ エミュレータの起動がタイムアウトしました。それでも続行します。")
    return True  # タイムアウトしても一応続行する

def find_installed_ndk_version():
    """インストールされているNDKのバージョンを取得する"""
    print("🔍 インストール済みのNDKバージョンを確認中...")
    
    # ANDROID_HOME または ANDROID_SDK_ROOT 環境変数をチェック
    android_home = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
    
    if not android_home:
        # macOSならデフォルトの場所をチェック
        if platform.system() == "Darwin":
            default_paths = [
                os.path.expanduser('~/Library/Android/sdk'),
                '/Applications/Android Studio.app/Contents/sdk'
            ]
            for path in default_paths:
                if os.path.exists(path):
                    android_home = path
                    break
    
    if not android_home:
        print("⚠️ Android SDKディレクトリが見つかりません")
        return None

    # NDKディレクトリを確認
    ndk_dir = os.path.join(android_home, 'ndk')
    if not os.path.exists(ndk_dir):
        print(f"⚠️ NDKディレクトリが見つかりません: {ndk_dir}")
        return None
    
    # インストールされているNDKバージョンを検索
    try:
        ndk_versions = [d for d in os.listdir(ndk_dir) if os.path.isdir(os.path.join(ndk_dir, d))]
        if not ndk_versions:
            print("⚠️ NDKバージョンが見つかりません")
            return None
        
        # 最新のNDKバージョンを返す（通常はソート順で最後のもの）
        latest_version = sorted(ndk_versions)[-1]
        print(f"✅ インストール済みNDKバージョン: {latest_version}")
        return latest_version
    except Exception as e:
        print(f"⚠️ NDKバージョンの確認中にエラーが発生しました: {e}")
        return None

def update_gradle_ndk_version(ndk_version):
    """build.gradleファイルのNDKバージョンを更新する"""
    print(f"🔧 build.gradleファイルのNDKバージョンを {ndk_version} に更新しています...")
    
    # プロジェクトのbuild.gradleファイルのパス
    app_build_gradle = os.path.join(os.getcwd(), 'android', 'app', 'build.gradle')
    project_build_gradle = os.path.join(os.getcwd(), 'android', 'build.gradle')
    
    files_to_check = [app_build_gradle, project_build_gradle]
    updated = False
    
    for gradle_file in files_to_check:
        if os.path.exists(gradle_file):
            try:
                print(f"  Gradleファイルを処理中: {gradle_file}")
                with open(gradle_file, 'r') as f:
                    content = f.read()
                
                # ndkVersionの行を探して置換
                if 'ndkVersion' in content:
                    # 既存のNDKバージョン行を検索して表示
                    ndk_line_match = re.search(r'.*ndkVersion\s+[\'"].*?[\'"].*', content)
                    if ndk_line_match:
                        old_line = ndk_line_match.group(0).strip()
                        print(f"    検出した設定行: {old_line}")
                    
                    # 置換処理
                    old_content = content
                    new_content = re.sub(
                        r'ndkVersion\s+[\'"].*?[\'"]',
                        f'ndkVersion "{ndk_version}"',
                        content
                    )
                    
                    # 変更があれば保存
                    if new_content != old_content:
                        with open(gradle_file, 'w') as f:
                            f.write(new_content)
                        print(f"✅ {gradle_file} のNDKバージョンを {ndk_version} に更新しました")
                        updated = True
                    else:
                        print(f"⚠️ {gradle_file} の内容が変更されませんでした。既に同じ設定の可能性があります。")
            except Exception as e:
                print(f"⚠️ gradleファイルの更新中にエラーが発生しました: {e}")
    
    return updated

def build_and_run_android_emulator(emulator_name, verbose=False, no_clean=False):
    """Flutterアプリをビルドして、Androidエミュレータで実行する"""
    print("\n🚀 FlutterアプリをAndroidエミュレータ用にビルドして実行します")
    
    # まずエミュレータを起動
    if not boot_emulator(emulator_name):
        return False
    
    # クリーンビルドが必要な場合
    if not no_clean:
        print("🧹 クリーンビルド実行中...")
        if not run_command("flutter clean", "クリーンビルド", show_output=verbose)[0]:
            return False
    
    # 依存関係の解決
    print("📦 依存パッケージを取得中...")
    if not run_command("flutter pub get", "依存関係の解決", show_output=verbose)[0]:
        return False
    
    # エミュレータでFlutterアプリを実行
    print(f"📱 エミュレータ ({emulator_name}) でアプリを起動しています...")
    print("💡 終了するにはこのターミナルでCtrl+Cを押してください")
    
    # デバイス検出に先にflutter devicesを使用（ADBよりも信頼性が高い）
    success, flutter_devices_output = run_command("flutter devices", "利用可能なデバイス一覧", show_output=True, show_progress=False)
    
    device_id = None
    if success and flutter_devices_output:
        # Flutter devicesの出力を解析してAndroidエミュレータを探す
        flutter_output = flutter_devices_output.decode('utf-8') if isinstance(flutter_devices_output, bytes) else flutter_devices_output
        lines = flutter_output.strip().split('\n')
        
        # 実行中のエミュレータを特定する
        android_devices = []
        for line in lines:
            if "emulator" in line.lower() and "android" in line.lower():
                print(f"🔍 エミュレータ検出: {line}")
                # ID抽出: 正規表現でemulator-XXXX形式のIDを抽出
                emulator_id_match = re.search(r'emulator-\d+', line)
                if emulator_id_match:
                    emulator_id = emulator_id_match.group(0)
                    android_devices.append({"line": line, "id": emulator_id})
                    print(f"✓ エミュレータID検出: {emulator_id}")
                else:
                    # 代替方法: • で分割して2列目を取得
                    parts = line.split('•')
                    if len(parts) >= 2:
                        potential_id = parts[1].strip()
                        android_devices.append({"line": line, "id": potential_id})
                        print(f"✓ エミュレータID検出 (代替): {potential_id}")
        
        # 検出したデバイスを使用
        if android_devices:
            device_id = android_devices[0]["id"]
            print(f"✅ 使用するエミュレータID: {device_id}")
    
    # 実行コマンドの決定
    if device_id:
        run_cmd = f"flutter run -d {device_id}"
        print(f"📱 エミュレータID: {device_id} を使用します")
    else:
        # エミュレータIDが特定できない場合でも、出力から "sdk gphone" を検出して使用
        for line in lines:
            if "sdk gphone" in line and "emulator" in line.lower():
                device_id = "emulator-5554"  # 標準的なエミュレータID
                print(f"🔍 'sdk gphone' エミュレータを検出しました: {line}")
                run_cmd = f"flutter run -d {device_id}"
                print(f"📱 エミュレータID: {device_id} を使用します")
                break
        else:
            print("⚠️ エミュレータIDが特定できません。デフォルトID（emulator-5554）を試します")
            run_cmd = "flutter run -d emulator-5554"
    
    success, output = run_command(run_cmd, "Androidエミュレータでアプリを実行", show_output=True, show_progress=True)
    
    # NDKエラーチェック - 手動で検出
    if not success:
        # エラー出力からNDK不一致を検出
        error_output = ""
        if isinstance(output, bytes):
            error_output = output.decode('utf-8')
        elif isinstance(output, str):
            error_output = output
        
        # この特定のNDKエラーパターンを検出 (直接見えているエラーメッセージを使用)
        if "NDK from ndk.dir" in error_output and "disagrees with android.ndkVersion" in error_output:
            print("\n⚠️ NDKバージョン不一致を検出しました。直接修正を行います...")
            
            # 明確にエラーメッセージから両方のNDKバージョンを抽出
            installed_ndk_match = re.search(r'NDK.+version\s+\[([0-9.]+)\]', error_output)
            if installed_ndk_match:
                installed_ndk = installed_ndk_match.group(1)
                print(f"  検出したインストール済みNDK: {installed_ndk}")
                
                # 直接ファイル修正を試行
                gradle_files_modified = direct_update_ndk_version(installed_ndk)
                
                if gradle_files_modified:
                    print(f"🔄 {len(gradle_files_modified)}個のファイルのNDK設定を {installed_ndk} に更新しました")
                    print("  ビルドを再実行します...")
                    # 再度実行
                    return run_command(run_cmd, "Androidエミュレータでアプリを実行（NDK設定更新後）", 
                                        show_output=True, show_progress=True)[0]
            else:
                print("⚠️ NDKバージョンを抽出できませんでした")
        
        # 自動選択に失敗したら手動選択に切り替え
        print("⚠️ 自動デバイス選択に失敗しました。通常の実行方法を試します...")
        run_cmd = "flutter run"
        success, output = run_command(run_cmd, "Androidエミュレータでアプリを実行（手動デバイス選択）", 
                                    show_output=True, show_progress=True)
        
        # 手動選択でもNDKエラーがあれば再度処理
        if not success:
            error_output = ""
            if isinstance(output, bytes):
                error_output = output.decode('utf-8')
            elif isinstance(output, str):
                error_output = output
            
            # この特定のNDKエラーパターンを検出 (直接見えているエラーメッセージを使用)
            if "NDK from ndk.dir" in error_output and "disagrees with android.ndkVersion" in error_output:
                print("\n⚠️ NDKバージョン不一致を検出しました。直接修正を行います...")
                
                # 明確にエラーメッセージから両方のNDKバージョンを抽出
                installed_ndk_match = re.search(r'at.+had version\s+\[([0-9.]+)\]', error_output)
                if installed_ndk_match:
                    installed_ndk = installed_ndk_match.group(1)
                    print(f"  検出したインストール済みNDK: {installed_ndk}")
                    
                    # 直接ファイル修正を試行
                    gradle_files_modified = direct_update_ndk_version(installed_ndk)
                    
                    if gradle_files_modified:
                        print(f"🔄 {len(gradle_files_modified)}個のファイルのNDK設定を {installed_ndk} に更新しました")
                        print("  ビルドを再実行します...")
                        # 再度実行
                        return run_command(run_cmd, "Androidエミュレータでアプリを実行（NDK設定更新後）", 
                                            show_output=True, show_progress=True)[0]
    
    return success

def direct_update_ndk_version(ndk_version):
    """build.gradleファイルを直接検索して更新する"""
    print(f"🔎 プロジェクト内のすべてのbuild.gradleファイルを検索し、NDK設定を更新します...")
    
    # Androidディレクトリをルートとして検索
    android_dir = os.path.join(os.getcwd(), 'android')
    if not os.path.exists(android_dir):
        print(f"⚠️ Androidディレクトリが見つかりません: {android_dir}")
        return []
    
    modified_files = []
    
    # すべてのgradleファイルを再帰的に検索
    for root, dirs, files in os.walk(android_dir):
        for file in files:
            if file.endswith('.gradle') or file.endswith('.properties'):
                full_path = os.path.join(root, file)
                try:
                    print(f"  チェック中: {full_path}")
                    file_modified = False
                    
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    # ndkVersionの行を探して置換
                    new_content = content
                    if 'ndkVersion' in content:
                        old_content = content
                        new_content = re.sub(
                            r'ndkVersion\s+[\'"].*?[\'"]',
                            f'ndkVersion "{ndk_version}"',
                            content
                        )
                        if new_content != old_content:
                            file_modified = True
                    
                    # ndk.dirの行を探して置換（local.propertiesファイルなど）
                    if 'ndk.dir' in content:
                        old_content = new_content
                        new_content = re.sub(
                            r'ndk\.dir=.*',
                            f'#ndk.dir=disabled_by_script',  # ndk.dirを無効にし、ndkVersionを優先
                            new_content
                        )
                        if new_content != old_content:
                            file_modified = True
                    
                    # 変更があれば保存
                    if file_modified:
                        with open(full_path, 'w') as f:
                            f.write(new_content)
                        print(f"  ✅ {full_path} を更新しました")
                        modified_files.append(full_path)
                
                except Exception as e:
                    print(f"  ⚠️ {full_path} の処理中にエラー: {e}")
    
    return modified_files

def main():
    """メイン実行関数"""
    # カレントディレクトリをプロジェクトのルートに変更（安全のため）
    os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    
    parser = argparse.ArgumentParser(description="Flutter アプリケーションのAndroidエミュレータでの実行")
    parser.add_argument('--verbose', action='store_true', help='詳細な出力を表示')
    parser.add_argument('--no-clean', action='store_true', help='クリーンビルドをスキップ')
    parser.add_argument('--list', action='store_true', help='利用可能なエミュレータの一覧を表示するだけ')
    parser.add_argument('--emulator', type=str, help='使用するエミュレータの名前またはインデックス番号')
    args = parser.parse_args()
    
    print("=== ジャイロスコープアプリ Android エミュレータ 自動ビルド＆実行スクリプト ===")
    
    # Flutter環境のチェック
    if not check_flutter_installation():
        return 1
    
    # Android SDK環境のチェック
    if not check_android_sdk():
        return 1
    
    # プロジェクトディレクトリの確認
    if not os.path.exists('lib/main.dart'):
        print("エラー: このディレクトリはFlutterプロジェクトではないようです。")
        print("Flutterプロジェクトのルートディレクトリで実行してください。")
        return 1
    
    # 出力フォルダの準備
    os.makedirs("output/android_emulator", exist_ok=True)
    
    # 利用可能なエミュレータの一覧を取得
    emulators = get_available_emulators()
    print_emulator_list(emulators)
    
    # 一覧表示のみの場合はここで終了
    if args.list or not emulators:
        return 0 if emulators else 1
    
    # エミュレータの選択
    selected_emulator = None
    
    if args.emulator:
        # 名前が指定された場合
        for emu in emulators:
            if emu['name'] == args.emulator:
                selected_emulator = emu
                break
                
        # 番号が指定された場合
        if not selected_emulator:
            try:
                idx = int(args.emulator) - 1  # 1ベースのインデックスを0ベースに変換
                if 0 <= idx < len(emulators):
                    selected_emulator = emulators[idx]
                else:
                    print(f"⚠️ 指定されたインデックス '{args.emulator}' は範囲外です。")
                    return 1
            except ValueError:
                print(f"⚠️ '{args.emulator}' は有効なエミュレータ名またはインデックスではありません。")
                return 1
    else:
        # エミュレータが指定されていない場合はユーザーに選択させる
        while True:
            try:
                choice = input("\nエミュレータの番号を選択してください (Ctrl+Cで終了): ")
                idx = int(choice) - 1
                if 0 <= idx < len(emulators):
                    selected_emulator = emulators[idx]
                    break
                else:
                    print("⚠️ 有効な番号を入力してください。")
            except ValueError:
                print("⚠️ 数字を入力してください。")
            except KeyboardInterrupt:
                print("\n\n⚠️ ユーザーにより操作が中断されました。")
                return 1
    
    android_version = selected_emulator.get('android_version', 'バージョン不明')
    print(f"\n✅ 選択されたエミュレータ: {selected_emulator['name']} (Android {android_version})")
    
    # ビルドと実行
    try:
        if build_and_run_android_emulator(selected_emulator['name'], args.verbose, args.no_clean):
            print("\n✨ アプリの実行が終了しました")
            return 0
        else:
            print("\n⚠️ アプリの実行中に問題が発生しました")
            return 1
    except Exception as e:
        print(f"\n予期せぬエラーが発生しました: {e}")
        # エラーログを保存
        log_filename = f"android_emulator_error_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(log_filename, 'w') as f:
                f.write("=== Androidエミュレータ実行エラーログ ===\n")
                f.write(f"日時: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Flutterバージョン: {get_flutter_version()}\n")
                f.write(f"エミュレータ: {selected_emulator['name']} (Android {android_version})\n")
                f.write("エラーメッセージ:\n")
                f.write(f"{str(e)}\n")
            print(f"\nエラーログを保存しました: {log_filename}")
        except Exception as e:
            print(f"エラーログの保存に失敗しました: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによりプログラムが中断されました")
        exit(1)
