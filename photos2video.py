#!/usr/bin/env python3
import os
import argparse
import cv2
import numpy as np
from PIL import Image
import ffmpeg
from pathlib import Path
from PIL import ExifTags

def create_blurred_background(img, target_width, target_height):
    """ぼかし背景を作成する関数"""
    # PILイメージをOpenCV形式に変換
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    # 画像のアスペクト比を保持しながら、目標サイズより大きくリサイズ
    aspect = img_cv.shape[1] / img_cv.shape[0]
    if aspect > target_width / target_height:
        # 横長の画像
        new_height = int(target_height * 1.5)
        new_width = int(new_height * aspect)
    else:
        # 縦長の画像
        new_width = int(target_width * 1.5)
        new_height = int(new_width / aspect)
    
    # リサイズ（幅と高さが2の倍数になるように調整）
    new_width = (new_width // 2) * 2
    new_height = (new_height // 2) * 2
    scaled_img = cv2.resize(img_cv, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
    
    # ぼかし処理
    blurred = cv2.GaussianBlur(scaled_img, (0, 0), 30)
    
    # 中央部分を切り出し
    start_x = (new_width - target_width) // 2
    start_y = (new_height - target_height) // 2
    cropped = blurred[start_y:start_y+target_height, start_x:start_x+target_width]
    
    return cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)

def process_image(img_path, output_path, target_width=3840, target_height=2160, duration=5):
    """画像を処理して動画を作成する関数"""
    print(f"画像を処理中: {img_path}")  # 処理状況を表示
    
    # 画像を開く（EXIFの回転情報を適用）
    img = Image.open(img_path)
    print(f"元画像サイズ: {img.size}")  # デバッグ情報
    
    # EXIFの回転情報を適用
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = img._getexif()
        if exif is not None and orientation in exif:
            if exif[orientation] == 3:
                img = img.rotate(180, expand=True)
                print("画像を180度回転")
            elif exif[orientation] == 6:
                img = img.rotate(270, expand=True)
                print("画像を270度回転")
            elif exif[orientation] == 8:
                img = img.rotate(90, expand=True)
                print("画像を90度回転")
    except (AttributeError, KeyError, IndexError, TypeError) as e:
        print(f"EXIF処理中のエラー: {e}")
        pass
    
    # 画像のアスペクト比を計算
    aspect_ratio = img.width / img.height
    target_aspect = target_width / target_height
    print(f"アスペクト比: 元={aspect_ratio:.2f}, 目標={target_aspect:.2f}")  # デバッグ情報
    
    # 新しい画像サイズを計算（2の倍数に調整）
    if aspect_ratio > target_aspect:  # 横長の画像
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
    else:  # 縦長の画像
        new_height = target_height
        new_width = int(target_height * aspect_ratio)
    
    # 幅と高さを2の倍数に調整
    new_width = (new_width // 2) * 2
    new_height = (new_height // 2) * 2
    
    print(f"リサイズ後のサイズ: {new_width}x{new_height}")  # デバッグ情報
    
    # 画像をリサイズ
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # 背景用の空の画像を作成（サイズを2の倍数に調整）
    background_width = (target_width // 2) * 2
    background_height = (target_height // 2) * 2
    try:
        background = create_blurred_background(img, background_width, background_height)
        background = Image.fromarray(background)
        print(f"ぼかし背景のサイズ: {background.size}")  # デバッグ情報
    except Exception as e:
        print(f"背景作成中のエラー: {e}")
        raise
    
    # リサイズした画像を背景の中央に配置
    x = (background_width - new_width) // 2
    y = (background_height - new_height) // 2
    background.paste(img_resized, (x, y))
    
    # 一時的なフレーム画像を保存
    temp_frame = output_path.with_suffix('.png')
    try:
        background.save(temp_frame)
        print(f"一時ファイルを保存: {temp_frame}")  # デバッグ情報
    except Exception as e:
        print(f"一時ファイル保存中のエラー: {e}")
        raise
    
    print(f"動画を生成中: {output_path}")  # 処理状況を表示
    
    try:
        # FFmpegを使用して動画を作成
        stream = ffmpeg.input(str(temp_frame), loop=1, t=duration)
        stream = ffmpeg.output(stream, str(output_path),
                             vcodec='libx264',      # H.264コーデック
                             preset='slow',         # 高品質設定
                             video_bitrate='20M',   # 高ビットレート
                             pix_fmt='yuv420p',     # QuickTime互換のピクセルフォーマット
                             movflags='+faststart', # ストリーミング最適化
                             r=24)                  # フレームレート
        
        # FFmpegコマンドを表示
        print("FFmpegコマンド:")
        print(" ".join(ffmpeg.compile(stream)))
        
        ffmpeg.run(stream, overwrite_output=True, capture_stderr=True)  # エラー出力をキャプチャ
        print(f"動画生成完了: {output_path}")  # 完了を表示
    except ffmpeg.Error as e:
        print(f"動画生成エラー ({img_path} -> {output_path}):")
        print(e.stderr.decode())  # FFmpegのエラーメッセージを表示
        # エラー時は一時ファイルを保持
        print(f"デバッグ用に一時ファイルを保持: {temp_frame}")
        return
    except Exception as e:
        print(f"その他のエラー ({img_path} -> {output_path}): {str(e)}")
        # エラー時は一時ファイルを保持
        print(f"デバッグ用に一時ファイルを保持: {temp_frame}")
        return
        
    # 成功時のみ一時ファイルを削除
    os.remove(temp_frame)

def main():
    parser = argparse.ArgumentParser(description='写真から動画を作成するスクリプト')
    parser.add_argument('input_dir', help='入力フォルダのパス')
    parser.add_argument('output_dir', help='出力フォルダのパス')
    parser.add_argument('--duration', type=int, default=5, help='動画の長さ（秒）')
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    # 入力フォルダ内のすべてのJPGファイルを処理（大文字小文字を区別しない）
    jpg_files = []
    for ext in ['*.jpg', '*.JPG', '*.jpeg', '*.JPEG']:
        jpg_files.extend(list(input_dir.rglob(ext)))
    
    if not jpg_files:
        print(f"警告: {input_dir}内にJPG画像が見つかりませんでした。")
        return
        
    print(f"合計{len(jpg_files)}枚の画像を処理します。")
    
    for img_path in jpg_files:
        # 出力パスを作成（フォルダ構造を維持）
        relative_path = img_path.relative_to(input_dir)
        output_path = output_dir / relative_path.parent / relative_path.stem
        output_path = output_path.with_suffix('.mp4')
        
        # 出力ディレクトリが存在しない場合は作成
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            process_image(img_path, output_path, duration=args.duration)
        except Exception as e:
            print(f'エラー ({img_path}): {str(e)}')

if __name__ == '__main__':
    main() 