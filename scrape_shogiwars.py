#!/usr/bin/env python3
"""
将棋ウォーズの対局履歴から特定の対戦相手との棋譜URLを抽出するスクリプト
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict
import argparse
from datetime import datetime


def scrape_page(
    user_id: str,
    opponent: str,
    month: str,
    gtype: str,
    page: int
) -> List[Dict[str, str]]:
    """
    1ページ分の棋譜URLを抽出

    Args:
        user_id: ユーザーID
        opponent: 対戦相手のID
        month: 対象月（YYYY-MM形式）
        gtype: ゲームタイプ
        page: ページ番号

    Returns:
        棋譜URLのリスト
    """
    base_url = "https://shogiwars.heroz.jp/games/history"

    params = {
        "animal": "false",
        "init_pos_type": "normal",
        "is_latest": "false",
        "locale": "ja",
        "month": month,
        "opponent_type": "normal",
        "user_id": user_id,
        "page": page
    }

    # gtypeが指定されている場合のみパラメータに追加
    if gtype is not None:
        params["gtype"] = gtype

    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching page {page}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # 棋譜URLを抽出
    game_urls = []

    # 対局履歴のリンクを探す
    # パターン: https://shogiwars.heroz.jp/games/ohakado-guranola_oisi-20251028_220236
    game_links = soup.find_all("a", href=re.compile(r"/games/[^/]+"))

    for link in game_links:
        href = link.get("href")
        if not href:
            continue

        # 完全なURLに変換
        if href.startswith("/games/"):
            full_url = f"https://shogiwars.heroz.jp{href}"
        elif href.startswith("https://"):
            full_url = href
        else:
            continue

        # URLから対戦相手を確認
        # URL形式: /games/{user1}-{user2}-{timestamp}
        game_id = href.split("/games/")[-1]

        # 対戦相手が含まれているか確認
        if opponent.lower() in game_id.lower():
            game_info = {
                "url": full_url,
                "game_id": game_id
            }

            # 追加情報があれば取得
            # 日時や結果など
            parent = link.find_parent()
            if parent:
                text = parent.get_text(strip=True)
                game_info["context"] = text

            game_urls.append(game_info)

    return game_urls


def scrape_game_urls(
    user_id: str,
    opponent: str,
    month: str = None,
    gtype: str = None,
    max_pages: int = None
) -> List[Dict[str, str]]:
    """
    将棋ウォーズの対局履歴ページから特定の対戦相手との棋譜URLを抽出
    複数ページを自動的に巡回して全ての対局を取得

    Args:
        user_id: ユーザーID
        opponent: 対戦相手のID
        month: 対象月（YYYY-MM形式、Noneの場合は現在月）
        gtype: ゲームタイプ（None=10分切れ負け, s1=1手10秒, sb=3分切れ負け）
        max_pages: 最大ページ数（Noneの場合は全ページを取得）

    Returns:
        棋譜URLのリスト
    """
    # monthが指定されていない場合は現在月を使用
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    print(f"Fetching game history for {user_id} vs {opponent} in {month}...")

    all_game_urls = []
    page = 1

    while True:
        if max_pages is not None and page > max_pages:
            print(f"Reached max_pages limit: {max_pages}")
            break

        print(f"Fetching page {page}...")
        game_urls = scrape_page(user_id, opponent, month, gtype, page)

        if not game_urls:
            print(f"No more games found at page {page}")
            break

        for game in game_urls:
            print(f"Found: {game['url']}")

        all_game_urls.extend(game_urls)
        page += 1

    print(f"\nTotal games found: {len(all_game_urls)}")
    return all_game_urls


def save_to_json(data: List[Dict[str, str]], output_file: str = "game_replays.json"):
    """
    抽出したデータをJSONファイルに保存

    Args:
        data: 保存するデータ
        output_file: 出力ファイル名
    """
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(data)} game URLs to {output_file}")


def main():
    # 現在の年月を取得
    current_month = datetime.now().strftime("%Y-%m")

    parser = argparse.ArgumentParser(
        description="将棋ウォーズの棋譜URLを抽出してJSONに保存"
    )
    parser.add_argument(
        "--user-id",
        default="UtadaHikaru",
        help="ユーザーID (default: UtadaHikaru)"
    )
    parser.add_argument(
        "--opponent",
        default="Walk_Wikipedia",
        help="対戦相手のID (default: Walk_Wikipedia)"
    )
    parser.add_argument(
        "--month",
        default=current_month,
        help=f"対象月 YYYY-MM形式 (default: {current_month})"
    )
    parser.add_argument(
        "--gtype",
        default=None,
        choices=["s1", "sb", None],
        help="ゲームタイプ: 無指定=10分切れ負け, s1=1手10秒, sb=3分切れ負け (default: 無指定)"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="取得する最大ページ数 (default: 全ページ)"
    )
    parser.add_argument(
        "--output",
        default="game_replays.json",
        help="出力ファイル名 (default: game_replays.json)"
    )

    args = parser.parse_args()

    # 棋譜URLを抽出
    game_urls = scrape_game_urls(
        user_id=args.user_id,
        opponent=args.opponent,
        month=args.month,
        gtype=args.gtype,
        max_pages=args.max_pages
    )

    if game_urls:
        # JSONに保存
        save_to_json(game_urls, args.output)
    else:
        print(f"\nNo games found with opponent: {args.opponent}")


if __name__ == "__main__":
    main()
