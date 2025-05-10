import 'package:flutter/material.dart';
import 'package:sensors_plus/sensors_plus.dart';
import 'dart:async';
import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'ボール移動デモ',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
      ),
      home: const BallPage(),
    );
  }
}

class BallPage extends StatefulWidget {
  const BallPage({super.key});
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
  bool lastCountedAtTop = false;

  // センサーデータのデバッグ用
  double gyroX = 0.0;
  double gyroY = 0.0;
  double gyroZ = 0.0;
  bool sensorAvailable = false;

  @override
  void initState() {
    super.initState();

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

          // 上部に達した場合
          if (ballPosition <= 0.0 && previousPosition > 0.0) {
            // 前回のカウントが下部だった場合のみカウント
            if (lastCountedAtTop == false) {
              counter++;
              lastCountedAtTop = true;
            }
          }

          // 下部に達した場合
          if (ballPosition >= 1.0 && previousPosition < 1.0) {
            // 前回のカウントが上部だった場合のみカウント
            if (lastCountedAtTop == true) {
              counter++;
              lastCountedAtTop = false;
            }
          }
        });
      });
    } catch (e) {
      print('センサー初期化エラー: $e');
      sensorAvailable = false;
    }
  }

  @override
  void dispose() {
    // リソース解放
    _gyroSub?.cancel();
    super.dispose();
  }

  // テスト用ボタン操作
  void moveBallUp() {
    setState(() {
      // 前回の位置を保存
      double previousPosition = ballPosition;

      ballPosition -= 0.1;
      if (ballPosition < 0) ballPosition = 0;

      // 上部に達した場合
      if (ballPosition <= 0.0 && previousPosition > 0.0) {
        // 前回のカウントが下部だった場合のみカウント
        if (lastCountedAtTop == false) {
          counter++;
          lastCountedAtTop = true;
        }
      }
    });
  }

  void moveBallDown() {
    setState(() {
      // 前回の位置を保存
      double previousPosition = ballPosition;

      ballPosition += 0.1;
      if (ballPosition > 1) ballPosition = 1;

      // 下部に達した場合
      if (ballPosition >= 1.0 && previousPosition < 1.0) {
        // 前回のカウントが上部だった場合のみカウント
        if (lastCountedAtTop == true) {
          counter++;
          lastCountedAtTop = false;
        }
      }
    });
  }

  void resetCounter() {
    setState(() {
      counter = 0;
      lastCountedAtTop = false; // リセット時は最後のカウントを下部とする（次は上部でカウント）
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

  @override
  Widget build(BuildContext context) {
    // バーとボールのサイズ定義
    const double barWidth = 20;
    const double barHeight = 200; // バーの長さを2/3程度に短縮
    const double ballSize = 40;

    // 現在選択されている軸の感度
    double currentSensitivity = axisSensitivity[selectedAxis] ?? 0.015;

    return Scaffold(
      appBar: AppBar(
        title: const Text('ボール移動デモ'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
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

              const SizedBox(height: 10),

              // センサー設定コントロール
              const SizedBox(height: 10),
              Text('ジャイロ設定', style: TextStyle(fontWeight: FontWeight.bold)),
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(
                    '${axisNames[selectedAxis]}軸の感度: ${currentSensitivity.toStringAsFixed(3)}',
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
              Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  ElevatedButton.icon(
                    icon: Icon(
                      invertAxis ? Icons.swap_vert : Icons.swap_vert_outlined,
                    ),
                    label: Text(invertAxis ? '軸反転: ON' : '軸反転: OFF'),
                    onPressed: toggleInvertAxis,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: invertAxis ? Colors.orange : null,
                    ),
                  ),
                  const SizedBox(width: 10),
                  ElevatedButton.icon(
                    icon: const Icon(Icons.screen_rotation),
                    label: Text('使用軸: ${axisNames[selectedAxis]}'),
                    onPressed: changeAxis,
                  ),
                ],
              ),

              // センサー状態表示
              sensorAvailable
                  ? Text('センサー: 使用可能', style: TextStyle(color: Colors.green))
                  : Text('センサー: 使用不可', style: TextStyle(color: Colors.red)),

              // デバッグ情報表示 - 各軸の感度も表示
              Container(
                margin: const EdgeInsets.symmetric(vertical: 10),
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
                        color: selectedAxis == 0 ? Colors.red : Colors.black,
                      ),
                    ),
                    Text(
                      'Y軸: ${gyroY.toStringAsFixed(5)} (感度: ${axisSensitivity[1]?.toStringAsFixed(3)})',
                      style: TextStyle(
                        color: selectedAxis == 1 ? Colors.red : Colors.black,
                      ),
                    ),
                    Text(
                      'Z軸: ${gyroZ.toStringAsFixed(5)} (感度: ${axisSensitivity[2]?.toStringAsFixed(3)})',
                      style: TextStyle(
                        color: selectedAxis == 2 ? Colors.red : Colors.black,
                      ),
                    ),
                    Text(
                      '現在使用中: ${axisNames[selectedAxis]}軸${invertAxis ? " (反転)" : ""}',
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 10),

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
                'カウンター: $counter/10',
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
                    '※Webブラウザではセンサーが使えない場合があります',
                    style: TextStyle(color: Colors.red),
                  )
                  : const Text('端末を前後に傾けてボールを動かしてください'),
              const Text('設定を調整して最適な動きになるよう調整してください'),
              const Text('最上部・最下部でカウンターが増えます'),

              const SizedBox(height: 20), // 下部の余白
            ],
          ),
        ),
      ),
    );
  }
}
