#!/usr/bin/env python3
import sys
import random
import traceback
from pathlib import Path
import ffmpeg
from datetime import datetime
import time
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple
import math

@dataclass
class ClipInfo:
    file: str
    start: float
    duration: float
    file_timestamp: str  # ファイル名から抽出した時刻

class VideoFile:
    def __init__(self, path: Path):
        self.path = path
        self.duration = get_video_duration(path)
        if self.duration is None:
            print(f"警告: {path.name} の長さを取得できません。スキップします。")
            self.duration = 0  # 長さが取得できない場合は0とする
        self.used_ranges: Set[Tuple[float, float]] = set()  # (start, end)のタプルのセット
        self.timestamp = self._extract_timestamp()
        self.min_gap = 1.0  # クリップ間の最小間隔（秒）
        
    def _extract_timestamp(self) -> str:
        """ファイル名からタイムスタンプを抽出
        
        以下のような形式に対応：
        - DJI_20250205132608_0003_D.MP4 -> 20250205132608
        - その他のファイル -> ファイルの更新日時をYYYYMMDDHHMMSS形式で返す
        """
        try:
            # DJIファイルの場合
            if self.path.stem.startswith('DJI_'):
                return self.path.stem.split('_')[1]
            
            # その他のファイルの場合は更新日時を使用
            mtime = self.path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime)
            return dt.strftime('%Y%m%d%H%M%S')
        except (IndexError, ValueError, OSError) as e:
            print(f"警告: {self.path.name} のタイムスタンプ抽出に失敗: {e}")
            # 現在時刻を使用
            return datetime.now().strftime('%Y%m%d%H%M%S')
        
    def get_available_duration(self) -> float:
        """まだ使用可能な合計時間を計算"""
        if not self.used_ranges:
            return self.duration
        
        used_duration = sum(end - start for start, end in self.used_ranges)
        # 最小間隔の合計を引く
        gap_duration = self.min_gap * (len(self.used_ranges) - 1) if len(self.used_ranges) > 1 else 0
        return self.duration - used_duration - gap_duration
        
    def can_extract_clip(self, clip_duration: float) -> bool:
        """指定された長さのクリップが抽出可能かチェック"""
        if self.duration < clip_duration:
            return False
            
        # 使用済み範囲をソート
        sorted_ranges = sorted(self.used_ranges)
        
        # 最初の使用済み範囲の前をチェック
        if sorted_ranges and sorted_ranges[0][0] >= clip_duration:
            return True
            
        # 使用済み範囲の間をチェック
        for i in range(len(sorted_ranges) - 1):
            gap = sorted_ranges[i + 1][0] - sorted_ranges[i][1]
            if gap >= clip_duration + self.min_gap * 2:  # 両端に最小間隔を確保
                return True
                
        # 最後の使用済み範囲の後をチェック
        if sorted_ranges:
            remaining = self.duration - sorted_ranges[-1][1]
            if remaining >= clip_duration + self.min_gap:  # 前側の最小間隔を確保
                return True
        
        return self.get_available_duration() >= clip_duration + self.min_gap
        
    def find_available_position(self, clip_duration: float) -> float:
        """使用可能な開始位置を見つける"""
        if not self.used_ranges:
            max_start = self.duration - clip_duration
            return random.uniform(0, max_start)
            
        sorted_ranges = sorted(self.used_ranges)
        available_ranges = []
        
        # 最初の使用済み範囲の前をチェック
        if sorted_ranges[0][0] >= clip_duration + self.min_gap:
            available_ranges.append((0, sorted_ranges[0][0] - clip_duration - self.min_gap))
            
        # 使用済み範囲の間の空きをチェック
        for i in range(len(sorted_ranges) - 1):
            gap_start = sorted_ranges[i][1] + self.min_gap  # 前のクリップの後ろに最小間隔を確保
            gap_end = sorted_ranges[i + 1][0] - self.min_gap  # 次のクリップの前に最小間隔を確保
            if gap_end - gap_start >= clip_duration:
                available_ranges.append((gap_start, gap_end - clip_duration))
                
        # 最後の使用済み範囲の後をチェック
        if sorted_ranges:
            last_end = sorted_ranges[-1][1] + self.min_gap  # 最小間隔を確保
            if self.duration - last_end >= clip_duration:
                available_ranges.append((last_end, self.duration - clip_duration))
        
        if not available_ranges:
            raise ValueError("利用可能な位置が見つかりません")
            
        # ランダムに範囲を選択
        selected_range = random.choice(available_ranges)
        return random.uniform(selected_range[0], selected_range[1])
        
    def add_used_range(self, start: float, duration: float):
        """使用済み範囲を追加"""
        self.used_ranges.add((start, start + duration))

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

def select_clips(video_files: List[VideoFile], clip_duration: float, total_duration: float) -> List[ClipInfo]:
    """必要なクリップを選択"""
    num_clips_needed = math.ceil(total_duration / clip_duration)
    selected_clips = []
    
    # 各ファイルから抽出可能なクリップ数を計算
    file_potentials = []
    for video_file in video_files:
        if video_file.duration >= clip_duration:
            max_clips = math.floor(video_file.duration / clip_duration)
            file_potentials.append((video_file, max_clips))
    
    # 抽出可能なクリップの総数を確認
    total_possible_clips = sum(potential[1] for potential in file_potentials)
    if total_possible_clips < num_clips_needed:
        print(f"警告: 必要なクリップ数 {num_clips_needed} に対して、抽出可能なクリップ数は {total_possible_clips} です")
        num_clips_needed = total_possible_clips
    
    while len(selected_clips) < num_clips_needed:
        # 利用可能なファイルをフィルタリング
        available_files = [
            video_file for video_file in video_files
            if video_file.can_extract_clip(clip_duration)
        ]
        
        if not available_files:
            break
            
        # ファイルをランダムに選択（長い動画を優先）
        available_files.sort(key=lambda x: x.get_available_duration(), reverse=True)
        selected_file = random.choice(available_files[:max(1, len(available_files) // 2)])
        
        try:
            start_time = selected_file.find_available_position(clip_duration)
            selected_file.add_used_range(start_time, clip_duration)
            
            selected_clips.append(ClipInfo(
                file=str(selected_file.path),
                start=start_time,
                duration=clip_duration,
                file_timestamp=selected_file.timestamp
            ))
            
            print(f"クリップ {len(selected_clips)} の選択:")
            print(f"ファイル: {selected_file.path.name}")
            print(f"開始位置: {start_time:.1f}秒")
            print(f"長さ: {clip_duration}秒")
            print(f"残り必要クリップ数: {num_clips_needed - len(selected_clips)}\n")
            
        except ValueError as e:
            print(f"警告: {selected_file.path.name} からのクリップ抽出に失敗: {e}")
            continue
    
    # タイムスタンプでソート
    selected_clips.sort(key=lambda x: (x.file_timestamp, x.start))
    return selected_clips

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

    # クリップをメディアプールに追加（1つずつ追加して順序を保持）
    added_clips = []
    print("\nクリップの順序:")
    for i, clip_info in enumerate(clips, 1):
        # 1つのクリップをメディアプールに追加
        result = mediaPool.ImportMedia([clip_info.file])
        if result and result[0]:
            media_item = result[0]
            added_clips.append({
                'clip': media_item,
                'start': clip_info.start,
                'duration': clip_info.duration,
                'timestamp': clip_info.file_timestamp
            })
            print(f"{i}. {Path(clip_info.file).name} (timestamp: {clip_info.file_timestamp})")
        else:
            print(f"❌ クリップ {i}: {Path(clip_info.file).name} の追加に失敗")

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

    # クリップをタイムラインに追加
    timeline_position = 0
    print("\nタイムラインにクリップを追加:")
    for i, clip_info in enumerate(added_clips, 1):
        # クリップの実際のフレームレートを取得
        clip_fps = float(clip_info['clip'].GetClipProperty("FPS"))
        
        # クリップの開始・終了フレームを計算
        start_frame = int(clip_info['start'] * clip_fps)
        end_frame = int((clip_info['start'] + clip_info['duration']) * clip_fps)
        
        print(f"{i}. {Path(clip_info['clip'].GetClipProperty('File Path')).name}")
        print(f"   Frames: {start_frame}-{end_frame}")
        
        mediaPool.AppendToTimeline([{
            'mediaPoolItem': clip_info['clip'],
            'startFrame': start_frame,
            'endFrame': end_frame
        }])
        
        # 次のクリップの開始位置を更新
        timeline_position = end_frame
    
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

        # 対応する動画形式のパターンを定義
        video_patterns = ["*.mp4", "*.MP4", "*.mov", "*.MOV", "*.avi", "*.AVI", "*.m4v", "*.M4V"]
        
        # すべてのパターンで動画ファイルを検索
        video_files = []
        for pattern in video_patterns:
            video_files.extend(list(input_dir.glob(pattern)))
        
        if not video_files:
            print(f"エラー: {args.input_dir} に動画ファイルが見つかりません")
            print("対応している動画形式:", ", ".join(pattern[2:].upper() for pattern in video_patterns[::2]))
            sys.exit(1)

        print(f"\n処理開始: {len(video_files)}個の動画ファイルを検出")
        print("検出された動画形式:")
        extensions = {f.suffix.lower() for f in video_files}
        for ext in sorted(extensions):
            count = sum(1 for f in video_files if f.suffix.lower() == ext)
            print(f"  {ext}: {count}個")
        print()

        # VideoFileオブジェクトを作成
        video_file_objects = [VideoFile(path) for path in video_files]
        
        # クリップを選択
        clips = select_clips(video_file_objects, args.clip_duration, args.total_duration)
        
        if not clips:
            print("エラー: クリップを選択できませんでした")
            sys.exit(1)

        # タイムラインを作成
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