import 'package:flutter/material.dart';
import 'package:sensors_plus/sensors_plus.dart';
import 'dart:async';
import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:vibration/vibration.dart';

// アプリ全体でテーマモードを管理するクラス
class ThemeProvider extends ChangeNotifier {
  ThemeMode _themeMode = ThemeMode.dark; // 初期値をダークモードに設定

  ThemeMode get themeMode => _themeMode;

  void toggleTheme() {
    _themeMode = _themeMode == ThemeMode.light 
                 ? ThemeMode.dark 
                 : ThemeMode.light;
    notifyListeners();
  }
}

void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  final ThemeProvider _themeProvider = ThemeProvider();

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _themeProvider,
      builder: (context, child) {
        return MaterialApp(
          title: 'ボール移動デモ',
          theme: ThemeData(
            colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
            useMaterial3: true,
          ),
          darkTheme: ThemeData(
            colorScheme: ColorScheme.fromSeed(
              seedColor: Colors.deepPurple,
              brightness: Brightness.dark,
            ),
            useMaterial3: true,
          ),
          themeMode: _themeProvider.themeMode, // テーマモードを設定
          home: BallPage(themeProvider: _themeProvider),
        );
      }
    );
  }
}

class BallPage extends StatefulWidget {
  final ThemeProvider themeProvider;
  
  const BallPage({super.key, required this.themeProvider});
  
  @override
  State<BallPage> createState() => _BallPageState();
}

class _BallPageState extends State<BallPage> {
  // 基本的な状態変数
  double ballPosition = 0.5; // 0.0: 上端, 1.0: 下端
  int counter = 0;
  // 軸ごとの感度設定 - すべての感度を上げる
  Map<int, double> axisSensitivity = {
    0: 0.15, // X軸 - さらに高く設定
    1: 0.01, // Y軸 - 少し上げる
    2: 0.03, // Z軸 - 上げる
  };
  bool invertAxis = false;
  int selectedAxis = 0; // X軸をデフォルトに変更
  String axisNames = "XYZ";
  StreamSubscription? _gyroSub;
  
  // カウンター状態変数
  bool reachedTop = false;    // 最上部に到達したかどうか
  bool reachedBottom = true;  // 最初は下からスタートとみなす
  
  // バイブレーション制御用
  bool canVibrate = false;
  DateTime? lastVibration;

  // センサーデータのデバッグ用
  double gyroX = 0.0;
  double gyroY = 0.0;
  double gyroZ = 0.0;
  bool sensorAvailable = false;

  @override
  void initState() {
    super.initState();
    
    // バイブレーション機能をチェック
    _checkVibrationSupport();

    try {
      // ジャイロスコープセンサーのリスナーをセットアップ
      _gyroSub = gyroscopeEvents.listen((GyroscopeEvent event) {
        setState(() {
          // デバッグ用にセンサーデータを保存
          gyroX = event.x;
          gyroY = event.y;
          gyroZ = event.z;
          sensorAvailable = true;

          // 前回の位置を保存
          double previousPosition = ballPosition;

          // 選択された軸に基づいてボールの位置を更新
          double axisValue = 0;
          switch (selectedAxis) {
            case 0:
              axisValue = event.x;
              break;
            case 1:
              axisValue = event.y;
              break;
            case 2:
              axisValue = event.z;
              break;
          }

          // 軸の向きを反転する場合
          if (invertAxis) {
            axisValue = -axisValue;
          }

          // 選択された軸の感度を使用
          double currentSensitivity = axisSensitivity[selectedAxis] ?? 0.015;

          // ボール位置の更新
          ballPosition -= axisValue * currentSensitivity;
          if (ballPosition < 0) ballPosition = 0;
          if (ballPosition > 1) ballPosition = 1;

          // 最上部に達した場合
          if (ballPosition <= 0.0 && previousPosition > 0.0) {
            // 最上部に到達時にバイブレーション
            _vibrateIfNeeded();
            
            // 下からスタートして上に到達した場合
            if (reachedBottom) {
              reachedTop = true;
              reachedBottom = false;
            }
          }

          // 最下部に達した場合
          if (ballPosition >= 1.0 && previousPosition < 1.0) {
            // 最下部に到達時にバイブレーション
            _vibrateIfNeeded();
            
            // 上に到達してから下に戻った場合、カウント増加
            if (reachedTop) {
              counter++; // 1サイクル完了でカウント増加
              reachedTop = false;
              reachedBottom = true;
            }
          }
        });
      });
    } catch (e) {
      print('センサー初期化エラー: $e');
      sensorAvailable = false;
    }
  }
  
  // バイブレーション機能をチェック
  Future<void> _checkVibrationSupport() async {
    if (!kIsWeb) {
      try {
        canVibrate = await Vibration.hasVibrator() ?? false;
      } catch (e) {
        canVibrate = false;
        print('バイブレーション機能チェックエラー: $e');
      }
    }
  }
  
  // 必要に応じてバイブレーションを実行（連続実行防止付き）
  void _vibrateIfNeeded() {
    if (!canVibrate) return;
    
    // 連続実行防止（前回から1秒以内は実行しない）
    final now = DateTime.now();
    if (lastVibration != null && now.difference(lastVibration!).inMilliseconds < 1000) {
      return;
    }
    
    lastVibration = now;
    
    try {
      // 0.5秒のバイブレーション
      Vibration.vibrate(duration: 500);
    } catch (e) {
      print('バイブレーション実行エラー: $e');
    }
  }

  @override
  void dispose() {
    // リソース解放
    _gyroSub?.cancel();
    super.dispose();
  }

  // テスト用ボタン操作を修正
  void moveBallUp() {
    setState(() {
      double previousPosition = ballPosition;
      ballPosition -= 0.1;
      if (ballPosition < 0) ballPosition = 0;
      
      // 最上部に達した場合
      if (ballPosition <= 0.0 && previousPosition > 0.0) {
        _vibrateIfNeeded();
        
        if (reachedBottom) {
          reachedTop = true;
          reachedBottom = false;
        }
      }
    });
  }

  void moveBallDown() {
    setState(() {
      double previousPosition = ballPosition;
      ballPosition += 0.1;
      if (ballPosition > 1) ballPosition = 1;
      
      // 最下部に達した場合
      if (ballPosition >= 1.0 && previousPosition < 1.0) {
        _vibrateIfNeeded();
        
        if (reachedTop) {
          counter++;
          reachedTop = false;
          reachedBottom = true;
        }
      }
    });
  }

  void resetCounter() {
    setState(() {
      counter = 0;
      reachedTop = false;
      reachedBottom = true; // リセット時は下部スタートにする
    });
  }

  // 感度調整メソッドを軸ごとに更新
  void increaseSensitivity() {
    setState(() {
      double current = axisSensitivity[selectedAxis] ?? 0.015;
      current += 0.005;
      if (current > 0.2) current = 0.2; // 上限を高めに設定
      axisSensitivity[selectedAxis] = current;
    });
  }

  void decreaseSensitivity() {
    setState(() {
      double current = axisSensitivity[selectedAxis] ?? 0.015;
      current -= 0.005;
      if (current < 0.001) current = 0.001;
      axisSensitivity[selectedAxis] = current;
    });
  }

  void toggleInvertAxis() {
    setState(() {
      invertAxis = !invertAxis;
    });
  }

  void changeAxis() {
    setState(() {
      selectedAxis = (selectedAxis + 1) % 3;
    });
  }

  // ジャイロ設定ダイアログを表示
  void _showGyroscopeSettings() {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('ジャイロスコープ設定'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                // センサー状態表示
                sensorAvailable
                    ? Text('センサー: 使用可能', style: TextStyle(color: Colors.green))
                    : Text('センサー: 使用不可', style: TextStyle(color: Colors.red)),
                
                const SizedBox(height: 15),
                
                // 軸と感度の設定
                Text('使用軸: ${axisNames[selectedAxis]}', style: TextStyle(fontWeight: FontWeight.bold)),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    ElevatedButton(
                      onPressed: changeAxis,
                      child: const Text('軸を変更'),
                    ),
                    const SizedBox(width: 10),
                    ElevatedButton(
                      onPressed: toggleInvertAxis,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: invertAxis ? Colors.orange : null,
                      ),
                      child: Text(invertAxis ? '軸反転: ON' : '軸反転: OFF'),
                    ),
                  ],
                ),

                const SizedBox(height: 15),

                // 感度調整
                Text('感度設定', style: TextStyle(fontWeight: FontWeight.bold)),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Text(
                      '${axisNames[selectedAxis]}軸: ${(axisSensitivity[selectedAxis] ?? 0.015).toStringAsFixed(3)}',
                    ),
                    const SizedBox(width: 10),
                    IconButton(
                      icon: const Icon(Icons.remove),
                      onPressed: decreaseSensitivity,
                      tooltip: '感度を下げる',
                    ),
                    IconButton(
                      icon: const Icon(Icons.add),
                      onPressed: increaseSensitivity,
                      tooltip: '感度を上げる',
                    ),
                  ],
                ),

                const SizedBox(height: 15),
                
                // デバッグ情報表示
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    border: Border.all(color: Colors.grey),
                    borderRadius: BorderRadius.circular(5),
                  ),
                  child: Column(
                    children: [
                      Text(
                        'ジャイロセンサーの値',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                      Text(
                        'X軸: ${gyroX.toStringAsFixed(5)} (感度: ${axisSensitivity[0]?.toStringAsFixed(3)})',
                        style: TextStyle(
                          color: selectedAxis == 0 ? Colors.red : null,
                        ),
                      ),
                      Text(
                        'Y軸: ${gyroY.toStringAsFixed(5)} (感度: ${axisSensitivity[1]?.toStringAsFixed(3)})',
                        style: TextStyle(
                          color: selectedAxis == 1 ? Colors.red : null,
                        ),
                      ),
                      Text(
                        'Z軸: ${gyroZ.toStringAsFixed(5)} (感度: ${axisSensitivity[2]?.toStringAsFixed(3)})',
                        style: TextStyle(
                          color: selectedAxis == 2 ? Colors.red : null,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              child: const Text('閉じる'),
              onPressed: () {
                Navigator.of(context).pop();
              },
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    // バーとボールのサイズ定義
    const double barWidth = 20;
    const double barHeight = 200; // バーの長さを2/3程度に短縮
    const double ballSize = 40;

    // 現在選択されている軸の感度
    double currentSensitivity = axisSensitivity[selectedAxis] ?? 0.015;

    // テーマモードを確認
    bool isDarkMode = widget.themeProvider.themeMode == ThemeMode.dark;

    return Scaffold(
      appBar: AppBar(
        title: const Text('ボール移動デモ'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          // ジャイロ設定ボタン
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: _showGyroscopeSettings,
            tooltip: 'ジャイロスコープ設定',
          ),
          // テーマ切り替えボタン
          IconButton(
            icon: Icon(isDarkMode ? Icons.light_mode : Icons.dark_mode),
            onPressed: () {
              widget.themeProvider.toggleTheme();
            },
            tooltip: isDarkMode ? 'ライトモードに切替' : 'ダークモードに切替',
          ),
          // リセットボタン
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: resetCounter,
            tooltip: 'リセット',
          ),
        ],
      ),
      // スクロール可能にする
      body: SingleChildScrollView(
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const SizedBox(height: 20), // 上部の余白
              
              // カウンターとリセットボタン
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text('カウンター: $counter', style: const TextStyle(fontSize: 24)),
                  const SizedBox(width: 15),
                  ElevatedButton.icon(
                    onPressed: resetCounter,
                    icon: const Icon(Icons.refresh),
                    label: const Text('リセット'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.orangeAccent,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 20),

              // 上移動ボタン
              ElevatedButton(onPressed: moveBallUp, child: const Text('上に移動')),

              const SizedBox(height: 10),
              // バーとボール
              Container(
                width: 100, // ボールが表示されるよう十分な幅
                height: barHeight + 20, // 余白も含む
                decoration: BoxDecoration(
                  border: Border.all(color: Colors.grey.shade300),
                ),
                child: Stack(
                  alignment: Alignment.topCenter,
                  children: [
                    // バー
                    Container(
                      width: barWidth,
                      height: barHeight,
                      decoration: BoxDecoration(
                        color: Colors.grey.shade300,
                        borderRadius: BorderRadius.circular(10),
                      ),
                    ),
                    // ボール
                    Positioned(
                      top: ballPosition * (barHeight - ballSize),
                      child: Container(
                        width: ballSize,
                        height: ballSize,
                        decoration: const BoxDecoration(
                          color: Colors.red,
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 10),

              // 下移動ボタン
              ElevatedButton(
                onPressed: moveBallDown,
                child: const Text('下に移動'),
              ),

              const SizedBox(height: 10),
              Text(
                '下→上→下で1カウント: $counter/10',
                style: TextStyle(
                  fontSize: 18,
                  color: counter >= 10 ? Colors.green : Colors.black,
                  fontWeight:
                      counter >= 10 ? FontWeight.bold : FontWeight.normal,
                ),
              ),

              const SizedBox(height: 10),
              kIsWeb
                  ? const Text(
                    '※Webブラウザではセンサーとバイブレーションが使えない場合があります',
                    style: TextStyle(color: Colors.red),
                  )
                  : Column(
                      children: [
                        const Text('端末を前後に傾けてボールを動かしてください'),
                        const Text('下→上→下で1カウントします'),
                        Text(canVibrate 
                          ? '最上部・最下部でバイブレーションします' 
                          : 'バイブレーション機能は使用できません',
                          style: TextStyle(
                            fontWeight: FontWeight.bold,
                            color: canVibrate ? Colors.green : Colors.orange,
                          ),
                        ),
                      ],
                    ),

              const SizedBox(height: 20), // 下部の余白
            ],
          ),
        ),
      ),
    );
  }
}
