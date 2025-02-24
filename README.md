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

## 必要条件

- Python 3.8以上
- FFmpeg

## インストール

1. 必要なパッケージをインストール:
```bash
pip install -r requirements.txt
```

2. FFmpegがインストールされていることを確認:
```bash
ffmpeg -version
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

#### 例
```bash
# 写真から動画を作成
python photos2video.py ./photos ./videos --duration 5

# 動画を結合（フォルダ順序を指定）
python combine_videos.py ./photos ./videos --photo-duration 5 --folder-order folder1 folder2 folder3

# 動画を結合（フォルダ名順）
python combine_videos.py ./photos ./videos --photo-duration 5
```

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