#!/usr/bin/env python3
import sys
import random
import traceback
from pathlib import Path
import ffmpeg
from datetime import datetime
import time

def get_video_duration(input_file):
    """動画の長さを取得"""
    try:
        probe = ffmpeg.probe(str(input_file))
        if 'format' in probe and 'duration' in probe['format']:
            return float(probe['format']['duration'])
        for stream in probe['streams']:
            if stream['codec_type'] == 'video' and 'duration' in stream:
                return float(stream['duration'])
        return None
    except Exception as e:
        print(f"エラー: {input_file}の解析に失敗: {e}")
        return None

def create_timeline_from_clips(resolve, clips, project_name="Random Clips"):
    """クリップからタイムラインを作成"""
    print("\n=== DaVinci Resolveプロジェクトの設定 ===")
    
    # プロジェクトマネージャーとプロジェクトを取得
    projectManager = resolve.GetProjectManager()
    if not projectManager:
        print("❌ プロジェクトマネージャーの取得に失敗しました")
        return False

    project = projectManager.GetCurrentProject()
    if not project:
        print("❌ 現在のプロジェクトの取得に失敗しました")
        return False

    # メディアプールを取得
    mediaPool = project.GetMediaPool()
    if not mediaPool:
        print("❌ メディアプールの取得に失敗しました")
        return False

    # ルートフォルダを取得
    rootFolder = mediaPool.GetRootFolder()
    if not rootFolder:
        print("❌ ルートフォルダの取得に失敗しました")
        return False

    # 新しいビンを作成
    bin_name = f"Random Clips {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\nビン '{bin_name}' を作成中...")
    bin_obj = mediaPool.AddSubFolder(rootFolder, bin_name)
    if not bin_obj:
        print("❌ ビンの作成に失敗しました")
        return False
    mediaPool.SetCurrentFolder(bin_obj)

    # クリップをメディアプールに追加
    clip_paths = [clip_info['file'] for clip_info in clips]
    result = mediaPool.ImportMedia(clip_paths)
    if not result:
        print("❌ クリップの一括追加に失敗しました")
        return False

    added_clips = []
    for i, (media_item, clip_info) in enumerate(zip(result, clips), 1):
        if media_item:
            added_clips.append({
                'clip': media_item,
                'start': clip_info['start'],
                'duration': clip_info['duration']
            })
            print(f"✓ クリップ {i}/{len(clips)}: {Path(clip_info['file']).name}")
        else:
            print(f"❌ クリップ {i}/{len(clips)}: {Path(clip_info['file']).name} の追加に失敗")

    # タイムラインを作成
    timeline_name = f"Random Timeline {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\nタイムライン '{timeline_name}' を作成中...")
    timeline = mediaPool.CreateEmptyTimeline(timeline_name)
    if not timeline:
        print("❌ タイムラインの作成に失敗しました")
        return False

    # タイムライン設定を4Kに変更
    timeline.SetSetting('useCustomSettings', '1')
    timeline.SetSetting('timelineResolutionWidth', '3840')
    timeline.SetSetting('timelineResolutionHeight', '2160')
    # timeline.SetSetting('timelineFrameRate', '30')

    # クリップをタイムラインに追加
    for clip_info in added_clips:
        # クリップの実際のフレームレートを取得
        clip_fps = float(clip_info['clip'].GetClipProperty("FPS"))
        
        # タイムライン上の位置（0から開始）
        start_frame = 0
        end_frame = int(clip_info['duration'] * clip_fps)
        
        # 元動画内の開始位置と終了位置
        source_start = int(clip_info['start'] * clip_fps)
        source_end = int((clip_info['start'] + clip_info['duration']) * clip_fps)
        
        mediaPool.AppendToTimeline([{
            'mediaPoolItem': clip_info['clip'],
            'startFrame': start_frame,
            'endFrame': end_frame,
            'sourceStart': source_start,
            'sourceEnd': source_end
        }])
    
    print("\n=== タイムラインの作成が完了しました ===")
    return True

def main():
    try:
        import DaVinciResolveScript as dvr_script
        resolve = dvr_script.scriptapp("Resolve")
        if not resolve:
            print("DaVinci Resolveに接続できません")
            sys.exit(1)

        import argparse
        parser = argparse.ArgumentParser(description='ランダムな動画クリップを選択してDaVinci Resolveのタイムラインを生成します')
        parser.add_argument('input_dir', help='入力動画フォルダのパス')
        parser.add_argument('--clip-duration', type=float, default=5, help='各クリップの最大長さ（秒）')
        parser.add_argument('--total-duration', type=float, default=60, help='完成動画の長さ（秒）')
        args = parser.parse_args()

        input_dir = Path(args.input_dir).resolve()
        if not input_dir.exists() or not input_dir.is_dir():
            print(f"エラー: 入力ディレクトリ {args.input_dir} が見つかりません")
            sys.exit(1)

        video_files = list(input_dir.glob("*.MP4"))
        if not video_files:
            print(f"エラー: {args.input_dir} に動画ファイルが見つかりません")
            sys.exit(1)

        print(f"\n処理開始: {len(video_files)}個の動画ファイルを検出\n")

        num_clips = int(args.total_duration / args.clip_duration)
        clips = []
        for i in range(num_clips):
            video_file = random.choice(video_files)
            duration = get_video_duration(video_file)
            if duration is None:
                print(f"警告: {video_file.name} の長さを取得できません。スキップします。")
                continue
            max_start = max(0, duration - args.clip_duration)
            start_time = random.uniform(0, max_start)
            print(f"クリップ {i + 1} の選択:")
            print(f"ファイル: {video_file.name}")
            print(f"開始位置: {start_time:.1f}秒")
            print(f"長さ: {args.clip_duration}秒\n")
            clips.append({
                'file': str(video_file.resolve()),
                'start': start_time,
                'duration': args.clip_duration
            })

        result = create_timeline_from_clips(resolve, clips)
        if result:
            print("\nタイムラインの作成が完了しました")
        else:
            print("\nタイムラインの作成に失敗しました")

    except Exception:
        print("\n=== スクリプト全体でキャッチした例外 ===")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()