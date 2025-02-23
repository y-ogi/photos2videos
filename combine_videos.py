#!/usr/bin/env python3
import os
import argparse
from pathlib import Path
import ffmpeg
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import tempfile
import shutil
from PIL import ExifTags

def create_title_video(text, output_path, duration=2):
    """タイトル画面の動画を作成する"""
    # 4K解像度で黒背景の画像を作成
    width, height = 3840, 2160
    image = Image.new('RGB', (width, height), 'black')
    draw = ImageDraw.Draw(image)
    
    # フォントサイズを計算（画面の高さの1/10程度）
    font_size = height // 10
    try:
        # macOSのシステムフォントを使用
        font = ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc', font_size)
    except:
        # フォントが見つからない場合はデフォルトフォントを使用
        font = ImageFont.load_default()
    
    # テキストを中央に配置
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # 白色でテキストを描画
    draw.text((x, y), text, font=font, fill='white')
    
    # 一時ファイルとして保存
    temp_image = output_path.with_suffix('.png')
    image.save(temp_image)
    
    try:
        # FFmpegで画像から動画を作成（フェードイン/アウト付き）
        stream = ffmpeg.input(str(temp_image), loop=1, t=duration)
        stream = ffmpeg.filter(stream, 'fade', type='in', start_time=0, duration=0.5)
        stream = ffmpeg.filter(stream, 'fade', type='out', start_time=duration-0.5, duration=0.5)
        stream = ffmpeg.output(stream, str(output_path),
                             vcodec='libx264',
                             preset='slow',
                             video_bitrate='20M',
                             pix_fmt='yuv420p',
                             r=24)
        ffmpeg.run(stream, overwrite_output=True, capture_stderr=True)
    finally:
        # 一時ファイルを削除
        os.remove(temp_image)

def get_video_duration(video_path):
    """動画の長さを取得する"""
    probe = ffmpeg.probe(str(video_path))
    return float(probe['streams'][0]['duration'])

def combine_videos_with_transition(video_files, output_path, transition_duration=1.0):
    """動画を結合し、クロスフェードトランジションを追加する"""
    if not video_files:
        print("警告: 結合する動画がありません")
        return
        
    print(f"動画結合を開始: {len(video_files)}個のファイル")
    print(f"出力先: {output_path}")
    
    # 一時ディレクトリを作成
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        print(f"一時ディレクトリを作成: {temp_dir_path}")
        
        # 各動画にトランジションを適用して一時ファイルとして保存
        processed_files = []
        for i, video_path in enumerate(video_files):
            try:
                print(f"\n動画 {i+1}/{len(video_files)} を処理中: {video_path.name}")
                duration = get_video_duration(video_path)
                print(f"動画の長さ: {duration:.2f}秒")
                
                temp_output = temp_dir_path / f"temp_{i}.mp4"
                print(f"一時ファイル: {temp_output}")
                
                if i == 0:
                    print("最初の動画: フェードアウトのみ適用")
                    stream = ffmpeg.input(str(video_path))
                    stream = ffmpeg.filter(stream, 'fade', type='out',
                                        start_time=duration-transition_duration,
                                        duration=transition_duration)
                elif i == len(video_files) - 1:
                    print("最後の動画: フェードインのみ適用")
                    stream = ffmpeg.input(str(video_path))
                    stream = ffmpeg.filter(stream, 'fade', type='in',
                                        start_time=0,
                                        duration=transition_duration)
                else:
                    print("中間の動画: フェードイン/アウト適用")
                    stream = ffmpeg.input(str(video_path))
                    stream = ffmpeg.filter(stream, 'fade', type='in',
                                        start_time=0,
                                        duration=transition_duration)
                    stream = ffmpeg.filter(stream, 'fade', type='out',
                                        start_time=duration-transition_duration,
                                        duration=transition_duration)
                
                # FFmpegコマンドを表示
                print("FFmpegコマンド:")
                print(" ".join(ffmpeg.compile(stream.output(str(temp_output),
                                            vcodec='libx264',
                                            preset='slow',
                                            video_bitrate='20M',
                                            pix_fmt='yuv420p',
                                            r=24))))
                
                # 一時ファイルとして保存
                ffmpeg.run(stream.output(str(temp_output),
                                       vcodec='libx264',
                                       preset='slow',
                                       video_bitrate='20M',
                                       pix_fmt='yuv420p',
                                       r=24),
                          overwrite_output=True,
                          capture_stderr=True)
                
                processed_files.append(temp_output)
                print(f"動画 {i+1} の処理が完了")
                
            except ffmpeg.Error as e:
                print(f"FFmpegエラー (動画 {i+1}): {e.stderr.decode()}")
                raise
            except Exception as e:
                print(f"予期せぬエラー (動画 {i+1}): {e}")
                raise
        
        try:
            # 動画リストファイルを作成
            list_file = temp_dir_path / "videos.txt"
            print(f"\n動画リストファイルを作成: {list_file}")
            with open(list_file, 'w') as f:
                for video in processed_files:
                    print(f"リストに追加: {video.name}")
                    f.write(f"file '{video.absolute()}'\n")
            
            # 最終的な結合
            print("\n最終結合を開始")
            stream = ffmpeg.input(str(list_file), format='concat', safe=0)
            stream = ffmpeg.output(stream, str(output_path),
                                 vcodec='libx264',
                                 preset='slow',
                                 video_bitrate='20M',
                                 pix_fmt='yuv420p',
                                 r=24)
            
            print("最終FFmpegコマンド:")
            print(" ".join(ffmpeg.compile(stream)))
            
            ffmpeg.run(stream, overwrite_output=True, capture_stderr=True)
            print(f"最終結合が完了: {output_path}")
            
        except ffmpeg.Error as e:
            print(f"最終結合中のFFmpegエラー: {e.stderr.decode()}")
            raise
        except Exception as e:
            print(f"最終結合中の予期せぬエラー: {e}")
            raise

def get_image_date(img_path):
    """画像のEXIF情報から撮影日時を取得する関数"""
    try:
        img = Image.open(img_path)
        exif = img._getexif()
        if exif is None:
            # EXIF情報がない場合はファイルの更新日時を使用
            return datetime.fromtimestamp(os.path.getmtime(img_path))
            
        for tag_id in ExifTags.TAGS:
            if ExifTags.TAGS[tag_id] == 'DateTimeOriginal':
                if tag_id in exif:
                    # EXIF内の撮影日時を解析
                    date_str = exif[tag_id]
                    return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                break
                
        # DateTimeOriginalが見つからない場合は更新日時を使用
        return datetime.fromtimestamp(os.path.getmtime(img_path))
    except Exception as e:
        print(f"日時取得エラー ({img_path}): {e}")
        # エラーの場合は更新日時を使用
        return datetime.fromtimestamp(os.path.getmtime(img_path))

def main():
    parser = argparse.ArgumentParser(description='フォルダ内の動画を結合するスクリプト')
    parser.add_argument('input_dir', help='入力フォルダのパス')
    parser.add_argument('output_dir', help='出力フォルダのパス')
    parser.add_argument('--photo-duration', type=int, default=5,
                       help='各写真の動画の長さ（秒）')
    parser.add_argument('--folder-order', type=str, nargs='+',
                       help='フォルダの処理順序（スペース区切りで指定。例: "Uta Rioto Leo"）')
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 写真から動画を生成
        print("写真から動画を生成中...")
        os.system(f'python photos2video.py "{input_dir}" "{output_dir}/個別" --duration {args.photo_duration}')
        
        # 各フォルダの動画を結合
        print("\n動画を結合中...")
        person_dirs = [d for d in (output_dir / "個別").iterdir() if d.is_dir()]
        
        # フォルダの順序を決定
        if args.folder_order:
            print("\nフォルダを指定順にソート中...")
            folder_order = args.folder_order
            
            def get_folder_order(person_dir):
                try:
                    return folder_order.index(person_dir.name)
                except ValueError:
                    return len(folder_order)  # 指定されていないフォルダは最後に
            
            person_dirs.sort(key=get_folder_order)
        else:
            print("\nフォルダをファイル名順にソート中...")
            person_dirs.sort(key=lambda x: x.name)
            
        print(f"処理するフォルダ順: {[d.name for d in person_dirs]}")
        all_videos = []
        
        for person_dir in person_dirs:
            try:
                print(f"\n{person_dir.name}の動画を処理中...")
                
                # フォルダ内の動画を取得してソート
                videos = list(person_dir.glob('*.mp4'))
                if not videos:
                    print(f"警告: {person_dir.name}に動画が見つかりません")
                    continue
                
                print(f"見つかった動画: {len(videos)}個")
                
                # ファイル名でビデオをソート
                print("動画をファイル名順にソート中...")
                videos.sort(key=lambda x: x.stem)
                print(f"ソート後の動画順: {[v.stem for v in videos]}")
                
                # タイトル動画を作成
                title_video = output_dir / f"title_{person_dir.name}.mp4"
                print(f"タイトル動画を作成中: {title_video}")
                create_title_video(person_dir.name, title_video)
                
                # タイトルとフォルダ内の動画を結合
                person_output = output_dir / f"{person_dir.name}_combined.mp4"
                print(f"動画を結合中: {person_output}")
                combine_videos_with_transition([title_video, *videos], person_output)
                all_videos.append(person_output)
                
                # タイトル動画を削除
                os.remove(title_video)
                print(f"{person_dir.name}の処理が完了しました")
                
            except Exception as e:
                print(f"フォルダ処理中にエラー ({person_dir.name}): {e}")
                continue
        
        # すべての動画を結合
        if all_videos:
            final_output = output_dir / "最終動画.mp4"
            print("\n最終動画を生成中...")
            print(f"結合する動画: {[v.stem for v in all_videos]}")
            combine_videos_with_transition(all_videos, final_output)
            print(f"\n完了！最終動画: {final_output}")
            
            # 中間ファイルを削除
            for video in all_videos:
                os.remove(video)
            shutil.rmtree(output_dir / "個別")
        else:
            print("\n警告: 結合する動画が見つかりません")
            
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        raise

if __name__ == '__main__':
    main() 