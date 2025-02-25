# Photos2Videos

写真から4K動画を作成し、複数の動画を結合するスクリプト

## 機能

### photos2video.py
- JPG画像から4K (3840x2160) 動画を作成
- 縦長画像や横長画像に対応（ぼかし背景を自動生成）
- フォルダ構造を維持したまま出力
- H.264コーデックを使用した高品質な動画出力
- 24fpsのフレームレート

### combine_videos.py
- 個別の写真から生成した動画を結合
- フォルダごとにタイトル画面を自動生成
- フェードイン/アウトによるスムーズな遷移効果
- フォルダの処理順序をカスタマイズ可能
- 最終的に全フォルダの動画を1つの動画に結合

### davinci_resolve_generator.py
- DaVinci Resolveでランダムな動画クリップを使用してタイムラインを生成
- 指定したフォルダから動画をランダムに選択
- 各クリップの開始位置をランダムに設定
- 4Kタイムラインの自動作成
- メディアプールへのクリップの一括追加

## 必要条件

- Python 3.8以上
- FFmpeg
- DaVinci Resolve Studio（davinci_resolve_generator.pyを使用する場合）

## インストール

1. 必要なパッケージをインストール:
```bash
pip install -r requirements.txt
```

2. FFmpegがインストールされていることを確認:
```bash
ffmpeg -version
```

3. DaVinci Resolve Python APIの設定（davinci_resolve_generator.pyを使用する場合）:
```bash
source setup_resolve_env.sh
```

## 使用方法

### 写真から動画を作成

```bash
python photos2video.py 入力フォルダ 出力フォルダ [--duration 秒数]
```

#### 引数
- `入力フォルダ`: JPG画像が含まれているフォルダのパス
- `出力フォルダ`: 動画を出力するフォルダのパス
- `--duration`: 動画の長さ（秒）。デフォルトは5秒

### 動画の結合

```bash
python combine_videos.py 入力フォルダ 出力フォルダ [--photo-duration 秒数] [--folder-order フォルダ名1 フォルダ名2 ...]
```

#### 引数
- `入力フォルダ`: 写真が含まれているフォルダのパス
- `出力フォルダ`: 結合した動画を出力するフォルダのパス
- `--photo-duration`: 各写真の動画の長さ（秒）。デフォルトは5秒
- `--folder-order`: フォルダの処理順序を指定（オプション）。指定しない場合はファイル名順

### DaVinci Resolveでタイムラインを生成

```bash
source setup_resolve_env.sh
python davinci_resolve_generator.py 入力フォルダ [--clip-duration 秒数] [--total-duration 秒数]
```

#### 引数
- `入力フォルダ`: MP4動画が含まれているフォルダのパス
- `--clip-duration`: 各クリップの長さ（秒）。デフォルトは5秒
- `--total-duration`: 完成動画の目標長さ（秒）。デフォルトは60秒

#### 使用手順
1. DaVinci Resolveを起動し、プロジェクトを開く
2. スクリプトを実行してタイムラインを生成
3. 生成されたタイムラインにトランジションを手動で追加
   - クリップ間の境界をダブルクリック
   - 「クロスディゾルブ」などの任意のトランジションを選択
   - 必要に応じてトランジションの長さを調整

## DaVinci Resolve APIの制限事項

現在のDaVinci Resolve APIには以下の制限があります：

1. トランジションの自動追加
   - APIを通じたトランジションの追加が正常に機能しない
   - トランジションは手動で追加する必要がある
   - スクリプトはタイムラインをコピーし、トランジションを追加すべき位置に再生ヘッドを配置する

2. Fusionエフェクト
   - スクリプトからのFusionエフェクトの完全な制御が困難
   - 複雑なエフェクトは手動で追加することを推奨

3. プロジェクト設定
   - 一部のプロジェクト設定がAPIを通じて変更できない
   - 重要な設定は事前にGUIで設定することを推奨

## トランジションの追加方法

スクリプトを実行すると、以下の2つのタイムラインが作成されます：

1. `Random Timeline YYYYMMDD_HHMMSS`
   - 選択されたクリップが配置された基本的なタイムライン
   - トランジションなし

2. `Random Timeline with Transitions YYYYMMDD_HHMMSS`
   - 上記タイムラインのコピー
   - トランジションを追加するための準備済み

トランジションを追加するには：
1. DaVinci Resolveで `Random Timeline with Transitions` タイムラインを開く
2. タイムライン上でクリップの境界をダブルクリック
3. 「クロスディゾルブ」などのトランジションを選択
4. 必要に応じてトランジションの長さを調整

## 出力仕様

### 個別の動画
- 解像度: 3840x2160 (4K)
- コーデック: H.264
- フレームレート: 24fps
- ビットレート: 20Mbps
- 出力形式: MP4

### 結合後の動画
- フォルダごとのタイトル画面付き
- フェードイン/アウトによる遷移効果
- 個別の動画と同じ品質仕様
- 最終的に1つの動画ファイルとして出力

### DaVinci Resolveタイムライン
- 解像度: 3840x2160 (4K)
- フレームレート: 24fps
- ランダムに選択されたクリップで構成
- トランジションは手動で追加が必要

## 新機能: トランジション

DaVinci Resolve 19でクリップ間にトランジションを追加する機能が追加されました。ただし、DaVinci Resolve APIの制限により、トランジションの自動追加は現在完全には機能しません。

### 使用方法

トランジションを追加するには、以下のコマンドラインオプションを使用します：

```bash
python davinci_resolve_generator.py 入力フォルダ --add-transitions --transition-duration 24
```

- `--add-transitions`: クリップ間にトランジションを追加するための準備を行います
- `--transition-duration`: トランジションの長さをフレーム数で指定します（デフォルト: 24フレーム）

### 制限事項

- **APIの制限**: 現在のDaVinci Resolve APIでは、スクリプトからトランジションを完全に自動で追加することができません
- **手動追加が必要**: トランジションは手動でDaVinci Resolveのインターフェースから追加する必要があります
- **解決策**: スクリプトは元のタイムラインをコピーし、トランジションを追加すべき位置に再生ヘッドを配置します

### 手動でトランジションを追加する手順

スクリプトを実行すると、以下の2つのタイムラインが作成されます：

1. `Random Timeline YYYYMMDD_HHMMSS`
   - 選択されたクリップが配置された基本的なタイムライン
   - トランジションなし

2. `Random Timeline with Transitions YYYYMMDD_HHMMSS`
   - 上記タイムラインのコピー
   - トランジションを追加するための準備済み

トランジションを追加するには：
1. DaVinci Resolveで `Random Timeline with Transitions` タイムラインを開く
2. タイムライン上でクリップの境界をダブルクリック
3. 「クロスディゾルブ」などのトランジションを選択
4. 必要に応じてトランジションの長さを調整

### 将来の改善

将来のDaVinci Resolve APIのバージョンでは、トランジションの自動追加機能が改善される可能性があります。その場合、スクリプトを更新して完全に自動化されたトランジション追加をサポートする予定です。

# DaVinci Resolve タイムライン生成ツール

このツールは、指定したフォルダ内の動画ファイルからランダムにクリップを選択し、DaVinci Resolveのタイムラインを自動生成します。

## 機能

- 複数の動画ファイルからランダムにクリップを選択
- クリップの長さと合計時間を指定可能
- DaVinci Resolveのタイムラインに自動配置
- スマートクリップ選択（動画の内容に基づいた選択）
- 最適な切り替えポイントの検出

## 必要条件

- Python 3.6以上
- DaVinci Resolve Studio（無料版では動作しない可能性があります）
- ffmpeg（動画分析に使用）

## インストール

1. このリポジトリをクローン
2. 必要なPythonパッケージをインストール:
   ```
   pip install -r requirements.txt
   ```
3. DaVinci Resolve Python APIの環境変数を設定:
   ```
   source setup_resolve_env.sh
   ```

## 使い方

基本的な使い方:

```bash
python davinci_resolve_generator.py <動画フォルダのパス> [オプション]
```

### オプション

- `--clip-duration <秒数>`: 各クリップの長さ（秒）を指定（デフォルト: 5秒）
- `--total-duration <秒数>`: 完成動画の合計長さ（秒）を指定（デフォルト: 60秒）
- `--smart-selection`: スマートクリップ選択アルゴリズムを使用
- `--diversity-weight <0.0-1.0>`: クリップ選択の多様性の重み（デフォルト: 0.5）
- `--detect-scenes`: シーン検出を使用して最適な切り替え点を見つける
- `--min-scene-score <0.0-1.0>`: シーン検出の最小スコア（デフォルト: 0.3）

### 使用例

標準的な使用方法:
```bash
python davinci_resolve_generator.py videos --clip-duration 5 --total-duration 30
```

スマートクリップ選択を使用:
```bash
python davinci_resolve_generator.py videos --clip-duration 5 --total-duration 30 --smart-selection
```

シーン検出を使用:
```bash
python davinci_resolve_generator.py videos --clip-duration 5 --total-duration 30 --detect-scenes
```

すべての機能を使用:
```bash
python davinci_resolve_generator.py videos --clip-duration 5 --total-duration 30 --smart-selection --diversity-weight 0.7 --detect-scenes --min-scene-score 0.4
```

## スマートクリップ選択機能

スマートクリップ選択機能は、動画の内容を分析して、より視覚的に興味深いクリップを選択します。以下の特徴を考慮します:

1. **シーン変化**: シーン変化が多いクリップを検出
2. **動きの量**: 動きの多いクリップを検出
3. **色の多様性**: 色彩が豊かなクリップを検出

また、選択されたクリップ間の多様性も考慮し、似たようなクリップが連続しないようにします。

### 多様性の重み

`--diversity-weight`パラメータを使用して、クリップ選択における多様性の重要度を調整できます:

- 値が大きい（1.0に近い）: より多様なクリップが選択される
- 値が小さい（0.0に近い）: より品質の高いクリップが選択される

## 切り替え点検出機能

切り替え点検出機能は、各クリップの最適な開始位置を見つけます。以下の方法で検出します:

1. **シーン変化の検出**: クリップ内のシーン変化を検出し、最適な切り替えポイントを見つける
2. **動きの分析**: シーン変化が見つからない場合、動きの少ない部分を探して切り替えポイントとする

### シーンスコア

`--min-scene-score`パラメータを使用して、シーン検出の感度を調整できます:

- 値が大きい: より明確なシーン変化のみを検出
- 値が小さい: わずかなシーン変化も検出

## 注意事項

- DaVinci Resolveが実行中である必要があります
- 大量の動画ファイルや長い動画を処理する場合は時間がかかる場合があります
- スマート選択機能とシーン検出機能は追加の処理時間を必要とします

## トラブルシューティング

DaVinci Resolve APIに接続できない場合:

1. DaVinci Resolveが起動していることを確認
2. 環境変数が正しく設定されていることを確認:
   ```
   source setup_resolve_env.sh
   ```
3. DaVinci Resolve Studioを使用していることを確認（無料版では動作しない可能性があります）