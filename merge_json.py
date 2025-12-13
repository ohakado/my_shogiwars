#!/usr/bin/env python
"""
既存の古いフォーマットのJSONファイルを新しいフォーマット（1ファイルに全組み合わせ）にマージするスクリプト
"""

import json
import os
from typing import List, Dict, Set

def merge_json_files(input_files: List[str], output_file: str):
    """
    複数のJSONファイルをマージして1つのファイルに統合

    Args:
        input_files: 入力ファイルのリスト
        output_file: 出力ファイル名
    """
    all_replays = []
    seen_game_ids: Set[str] = set()
    user = None
    month = None
    opponent = None

    print(f"マージ対象ファイル: {len(input_files)}個")

    for file_path in input_files:
        if not os.path.exists(file_path):
            print(f"警告: ファイルが見つかりません: {file_path}")
            continue

        print(f"\n読み込み中: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # paramsから情報を取得
        params = data.get('params', {})
        if user is None:
            user = params.get('user')
        if month is None:
            month = params.get('month')
        if opponent is None:
            opponent = params.get('opponent')

        # replaysを統合（重複排除）
        replays = data.get('replays', [])
        duplicates = 0
        new_games = 0

        for replay in replays:
            game_id = replay.get('game_id')
            if game_id and game_id not in seen_game_ids:
                all_replays.append(replay)
                seen_game_ids.add(game_id)
                new_games += 1
            else:
                duplicates += 1

        print(f"  - 対局数: {len(replays)}")
        print(f"  - 新規追加: {new_games}")
        print(f"  - 重複スキップ: {duplicates}")

    # 日時順にソート（降順）
    all_replays.sort(key=lambda x: x.get('datetime', ''), reverse=True)

    # 統合データを作成
    merged_data = {
        "params": {
            "user": user,
            "opponent": opponent if opponent else "(all)",
            "month": month,
            "gtype": "(all)",
            "opponent_type": "(all)",
            "init_pos_type": "(all)",
            "limit": "(all)"
        },
        "replays": all_replays
    }

    # ファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"マージ完了！")
    print(f"  - 総対局数: {len(all_replays)}")
    print(f"  - 出力ファイル: {output_file}")
    print(f"{'='*60}\n")

def main():
    # マージ対象のファイル
    base_dir = "/Users/ohakado/my_workspace/my_shogiwars/result"
    input_files = [
        os.path.join(base_dir, "game_replays_s1_2025-12_ohakado.json"),
        os.path.join(base_dir, "game_replays_s1_normal_normal_2025-12_ohakado.json"),
        os.path.join(base_dir, "game_replays_sf_closed_event_normal_2025-12_ohakado.json")
    ]

    output_file = os.path.join(base_dir, "game_replays_2025-12_ohakado.json")

    # マージ実行
    merge_json_files(input_files, output_file)

    # 古いファイルをバックアップディレクトリに移動
    backup_dir = os.path.join(base_dir, "backup")
    os.makedirs(backup_dir, exist_ok=True)

    print("古いファイルをバックアップディレクトリに移動中...")
    for file_path in input_files:
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            backup_path = os.path.join(backup_dir, filename)
            os.rename(file_path, backup_path)
            print(f"  - {filename} -> backup/{filename}")

    print("\n完了！")

if __name__ == "__main__":
    main()
