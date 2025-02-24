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

def wait_for_operation(operation_name, timeout=10):
    """操作の完了を待機"""
    start_time = time.time()
    print(f"{operation_name}の完了を待機中...", end="", flush=True)
    while time.time() - start_time < timeout:
        print(".", end="", flush=True)
        time.sleep(1)
    print(" タイムアウト")
    return False

def create_timeline_from_clips(resolve, clips, project_name="Random Clips"):
    """クリップからタイムラインを作成(トレースバック表示用に大きなtryを外した版)"""

    print("\n=== DaVinci Resolveプロジェクトの設定 ===")
    
    # プロジェクトマネージャーを取得
    print("プロジェクトマネージャーに接続中...")
    projectManager = resolve.GetProjectManager()
    if not projectManager:
        print("❌ プロジェクトマネージャーの取得に失敗しました")
        return False
    print("✓ プロジェクトマネージャーに接続しました")
    
    # 現在のプロジェクトを取得
    print("\n現在のプロジェクトを取得中...")
    project = projectManager.GetCurrentProject()
    if not project:
        print("❌ 現在のプロジェクトの取得に失敗しました")
        return False
    print(f"✓ プロジェクト '{project.GetName()}' を使用します")
    
    # メディアプールを取得
    print("\nメディアプールを取得中...")
    mediaPool = project.GetMediaPool()
    if not mediaPool:
        print("❌ メディアプールの取得に失敗しました")
        return False
    print("✓ メディアプールを取得しました")
    
    # ルートフォルダを取得
    print("\nメディアプールのルートフォルダを取得中...")
    rootFolder = mediaPool.GetRootFolder()
    if not rootFolder:
        print("❌ ルートフォルダの取得に失敗しました")
        return False
    print("✓ ルートフォルダを取得しました")
    
    # 新しいビンを作成
    bin_name = f"Random Clips {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\nビン '{bin_name}' を作成中...")
    bin_obj = mediaPool.AddSubFolder(rootFolder, bin_name)
    if not bin_obj:
        print("❌ ビンの作成に失敗しました")
        return False
    print(f"✓ ビン '{bin_name}' を作成しました")
    
    print("\n=== クリップの追加 ===")
    # クリップをメディアプールに追加（バッチ処理）
    mediaPool.SetCurrentFolder(bin_obj)
    print(f"\n{len(clips)}個のクリップをメディアプールに一括追加中...")
    
    # すべてのクリップのパスをリストにまとめる
    clip_paths = [clip_info['file'] for clip_info in clips]
    result = mediaPool.ImportMedia(clip_paths)
    
    if not result:
        print("❌ クリップの一括追加に失敗しました")
        return False
        
    # 追加されたクリップと元の情報を紐付け
    added_clips = []
    for i, (media_item, clip_info) in enumerate(zip(result, clips), 1):
        if media_item:
            # トランジション用にクリップの長さを少し延長（前後に0.5秒ずつ）
            start = max(0, clip_info['start'] - 0.5)
            duration = clip_info['duration'] + 1.0  # 合計1秒延長
            
            added_clips.append({
                'clip': media_item,
                'start': start,
                'duration': duration
            })
            print(f"✓ クリップ {i}/{len(clips)}: {Path(clip_info['file']).name}")
        else:
            print(f"❌ クリップ {i}/{len(clips)}: {Path(clip_info['file']).name} の追加に失敗")
    
    if not added_clips:
        print("\n❌ クリップの追加に失敗しました")
        return False
    
    print(f"\n✓ {len(added_clips)}個のクリップを追加しました")
    
    print("\n=== タイムラインの作成 ===")
    # 新しいタイムラインを作成（4K設定）
    timeline_name = f"Random Timeline {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"\nタイムライン '{timeline_name}' を作成中...")
    timeline = mediaPool.CreateEmptyTimeline(timeline_name)
    if not timeline:
        print("❌ タイムラインの作成に失敗しました")
        return False
    print(f"✓ タイムライン '{timeline_name}' を作成しました")
    
    print("\nタイムライン設定を4Kに変更中...")
    # タイムライン設定を4Kに変更
    timeline.SetSetting('useCustomSettings', '1')
    timeline.SetSetting('timelineResolutionWidth', '3840')
    timeline.SetSetting('timelineResolutionHeight', '2160')
    timeline.SetSetting('timelineFrameRate', '24')
    print("✓ タイムライン設定を更新しました")
    
    print("\n=== クリップの配置とトランジションの追加 ===")
    # クリップをタイムラインに一括追加
    print(f"\n{len(added_clips)}個のクリップをタイムラインに追加中...")
    
    # クリップの追加情報を準備（ハンドル用に前後12フレームずつ余裕を持たせる）
    timeline_items = []
    for clip_info in added_clips:
        # 開始位置を12フレーム後ろにずらし、長さを24フレーム短くする
        timeline_items.append({
            'mediaPoolItem': clip_info['clip'],
            'startFrame': int(clip_info['start'] * 24) + 12,
            'duration': int(clip_info['duration'] * 24) - 24
        })
    
    result = mediaPool.AppendToTimeline(timeline_items)
    if not result:
        print("❌ クリップの一括追加に失敗しました")
        return False
    
    print("✓ クリップを追加しました")
    
    # print("project =", project)
    # print("type(project) =", type(project))

    # # OK: ProjectオブジェクトのSave()を呼ぶ
    # save_result = project.Save()
    # print(f"プロジェクトの保存結果: {save_result}")
    projectManager = resolve.GetProjectManager()
    if callable(getattr(projectManager, "SaveProject", None)):
        result = projectManager.SaveProject(project)
        print("プロジェクトの保存結果:", result)
    else:
        print("projectManager.SaveProject は存在しません")
        
        print("\n=== トランジションの追加 ===")
    
    # 現在のプロジェクトから作成したタイムラインを再取得
    timeline_count = project.GetTimelineCount()
    timeline_reloaded = None
    for idx in range(1, timeline_count + 1):
        tline = project.GetTimelineByIndex(idx)
        if tline and tline.GetName() == timeline_name:
            timeline_reloaded = tline
            break
    
    if not timeline_reloaded:
        print("❌ 作成したタイムラインの再取得に失敗")
        return False
    
    # ビデオトラック1のアイテムを取得
    print("\nビデオトラック1上のアイテムを取得します...")
    video_track = timeline_reloaded.GetItemListInTrack("video", 1)
    if not video_track:
        print("❌ ビデオトラック1にアイテムがありません")
        return False
    
    print(f"  取得アイテム数: {len(video_track)}")
    
    # クリップ一覧を表示（callableチェックを入れてエラー箇所をあぶり出す）
    print("\n--- クリップの配置状況 ---")
    for i, clip in enumerate(video_track):
        print(f"[Clip {i+1}] ---------------")
        
        # GetStart() / GetEnd() を安全に呼び出す
        get_start = getattr(clip, "GetStart", None)
        get_end = getattr(clip, "GetEnd", None)
        
        if callable(get_start):
            start_val = get_start()
        else:
            start_val = "呼び出せません"
        
        if callable(get_end):
            end_val = get_end()
        else:
            end_val = "呼び出せません"
        
        print(f"  start={start_val}, end={end_val}")


    current_page = resolve.GetCurrentPage()
    print("Current Page:", current_page)
    print("Timeline attributes:", dir(timeline))
       
    # トランジションを追加
    print("\n--- クリップ間にトランジションを追加します ---")
    for i in range(len(video_track)-1):
        print(f"\n  {i+1}番目と{i+2}番目の間でトランジション追加試行...")
        # AddTransition呼び出し前に callabe() 確認
        add_transition_method = getattr(timeline_reloaded, "AddTransition", None)
        if not callable(add_transition_method):
            print("  ❌ timeline.AddTransitionメソッドが呼び出せません (None or not callable)")
            continue
        
        # i+1 → itemIndex は1ベース
        result = add_transition_method("video", 1, i+1, "Cross Dissolve", 12)
        print(f"  追加結果: {result}")
    
    print("\n=== タイムラインの作成が完了しました ===")
    return True

def main():
    """
    メインのエントリポイント。
    大きなtryは残すが、詳細なエラーを traceback.print_exc() で表示する。
    """
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
        
        # 入力ディレクトリのチェック
        input_dir = Path(args.input_dir).resolve()
        if not input_dir.exists() or not input_dir.is_dir():
            print(f"エラー: 入力ディレクトリ {args.input_dir} が見つかりません")
            return
        
        # 動画ファイルを検索
        video_files = list(input_dir.glob("*.MP4"))
        if not video_files:
            print(f"エラー: {args.input_dir} に動画ファイルが見つかりません")
            return
        
        print(f"\n処理開始: {len(video_files)}個の動画ファイルを検出\n")
        
        # 必要なクリップ数を計算
        num_clips = int(args.total_duration / args.clip_duration)
        clips = []
        
        for i in range(num_clips):
            # ランダムな動画を選択
            video_file = random.choice(video_files)
            duration = get_video_duration(video_file)
            if duration is None:
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
        
        # タイムラインを作成
        result = create_timeline_from_clips(resolve, clips)
        if result:
            print("\nタイムラインの作成が完了しました")
        else:
            print("\nタイムラインの作成に失敗しました")
    
    except Exception:
        print("\n=== スクリプト全体でキャッチした例外 ===")
        traceback.print_exc()  # 詳細なスタックトレースを表示
        sys.exit(1)

if __name__ == "__main__":
    main()