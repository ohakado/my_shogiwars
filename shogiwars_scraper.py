#!/usr/bin/env python
"""
将棋ウォーズの対局履歴から特定の対戦相手との棋譜URLを抽出するスクリプト
ログイン認証に対応
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import json
import re
from typing import List, Dict, Optional
import argparse
from datetime import datetime
import time
import os
import getpass


def login_to_shogiwars(driver, username: str, password: str, manual_captcha: bool = False) -> tuple[bool, str]:
    """
    将棋ウォーズにログイン

    Args:
        driver: Seleniumのwebdriver
        username: ログインユーザー名（メールアドレスまたはアカウント名）
        password: ログインパスワード
        manual_captcha: TrueならCAPTCHAを手動で完了できるように待機する

    Returns:
        (ログイン成功の可否, ログインユーザーのID)
    """
    try:
        print("Logging in to 将棋ウォーズ...")

        # ログインページにアクセス（/loginmにリダイレクトされる）
        login_url = "https://shogiwars.heroz.jp/loginm?locale=ja"
        driver.get(login_url)

        # ページの読み込みを待機
        wait = WebDriverWait(driver, 15)

        # ユーザー名入力フィールドを探す
        print("Waiting for login form...")
        username_field = wait.until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        password_field = driver.find_element(By.NAME, "password")

        # 認証情報を入力（人間らしくゆっくりと）
        print(f"Entering credentials for: {username}")
        time.sleep(1)
        username_field.clear()
        username_field.send_keys(username)
        time.sleep(1)
        password_field.clear()
        password_field.send_keys(password)
        time.sleep(1)

        # tmpディレクトリを作成（存在しない場合）
        tmp_dir = "tmp"
        os.makedirs(tmp_dir, exist_ok=True)

        # スクリーンショット保存（デバッグ用）
        screenshot_path = os.path.join(tmp_dir, "login_before_captcha.png")
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")

        # Cloudflare Turnstileの読み込みとCAPTCHAの自動解決を待つ
        print("Waiting for Cloudflare Turnstile to load and auto-solve...")
        print("(This may take 10-15 seconds...)")
        time.sleep(15)

        # スクリーンショット保存（デバッグ用）
        screenshot_path = os.path.join(tmp_dir, "login_after_captcha_wait.png")
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")

        # 手動介入モードの場合
        if manual_captcha:
            print("\n" + "="*60)
            print("手動介入モード:")
            print("ブラウザウィンドウでCAPTCHAを確認してください。")
            print("必要に応じてCAPTCHAを完了し、ログインボタンを手動でクリックしてください。")
            print("ログインが完了したら、このターミナルでEnterキーを押してください。")
            print("="*60 + "\n")
            try:
                input("Enterキーを押して続行...")
            except EOFError:
                print("Warning: Cannot read input in non-interactive mode")
                time.sleep(30)  # 手動で操作する時間を与える
        else:
            # CAPTCHAが解決されたか確認
            page_source = driver.page_source
            if "cf-turnstile-response" in page_source:
                print("Cloudflare Turnstile detected - attempting to proceed...")

            # ログインボタンを探してクリック
            print("Clicking login button...")
            login_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='ログインする']")
            login_button.click()

            # ログイン後のダイアログを待機
            print("Waiting for login response...")
            time.sleep(3)

            # カスタムダイアログ（「ログインしました。」）のOKボタンをクリック
            try:
                # ダイアログ内のOKボタンを探す
                ok_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'OK')] | //input[@value='OK']"))
                )
                print("Login success dialog detected - clicking OK button...")
                ok_button.click()
                print("Dialog closed")
                time.sleep(3)
            except TimeoutException:
                print("No dialog detected - login may have failed or no dialog shown")

            # スクリーンショット保存（デバッグ用）
            screenshot_path = os.path.join(tmp_dir, "login_after_submit.png")
            driver.save_screenshot(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")

        # ログイン成功の確認（URLの変化を確認）
        current_url = driver.current_url
        print(f"Current URL after login: {current_url}")

        if "loginm" not in current_url and "login" not in current_url:
            print("Login successful!")

            # URLからユーザーIDを抽出
            # 例: https://shogiwars.heroz.jp/users/mypage/ohakado?locale=ja&signup=false
            user_id = None
            if "/users/mypage/" in current_url:
                # /users/mypage/の後ろからユーザーIDを抽出
                parts = current_url.split("/users/mypage/")
                if len(parts) > 1:
                    user_id = parts[1].split("?")[0]
                    print(f"Detected user ID: {user_id}")

            if not user_id:
                print("Warning: Could not extract user ID from URL")
                user_id = ""

            return True, user_id
        else:
            # エラーメッセージがあるか確認
            page_source = driver.page_source
            if "アカウント名またはパスワードが違います" in page_source:
                print("Login failed - incorrect username or password")
            elif "Cloudflare" in page_source or "turnstile" in page_source:
                print("Login blocked by Cloudflare Turnstile (CAPTCHA)")
                print("You may need to complete the CAPTCHA manually or wait a moment...")
            else:
                print("Login failed - still on login page")
            return False, ""

    except TimeoutException:
        print("Login timeout - could not find login form elements")
        return False, ""
    except Exception as e:
        print(f"Login error: {e}")
        import traceback
        traceback.print_exc()
        return False, ""


def scrape_page(
    driver,
    user: str,
    opponent: str,
    month: str,
    gtype: str,
    opponent_type: str,
    init_pos_type: str,
    page: int
) -> tuple[List[Dict[str, str]], bool]:
    """
    1ページ分の棋譜URLを抽出

    Args:
        driver: Seleniumのwebdriver
        user: ユーザーID
        opponent: 対戦相手のID
        month: 対象月（YYYY-MM形式）
        gtype: ゲームタイプ
        opponent_type: 対戦相手タイプ
        init_pos_type: 初期配置タイプ
        page: ページ番号

    Returns:
        (棋譜URLのリスト, ページに対局が存在するか)
    """
    base_url = "https://shogiwars.heroz.jp/games/history"

    params = {
        "animal": "false",
        "init_pos_type": init_pos_type,
        "is_latest": "false",
        "locale": "ja",
        "month": month,
        "opponent_type": opponent_type,
        "user_id": user,
        "page": page
    }

    # gtypeが指定されている場合のみパラメータに追加
    if gtype is not None:
        params["gtype"] = gtype

    # URLを構築
    param_str = "&".join([f"{k}={v}" for k, v in params.items()])
    url = f"{base_url}?{param_str}"

    try:
        driver.get(url)
        # ページの読み込みを待機
        time.sleep(2)
        page_source = driver.page_source
    except Exception as e:
        print(f"Error fetching page {page}: {e}")
        return [], False

    soup = BeautifulSoup(page_source, "html.parser")

    # デバッグ用: 一時的にHTMLを保存
    if page == 1:
        with open("tmp/history_page_for_badges.html", "w", encoding="utf-8") as f:
            f.write(page_source)

    # 棋譜URLを抽出
    game_urls = []

    # 対局履歴のリンクを探す
    # パターン: https://shogiwars.heroz.jp/games/ohakado-guranola_oisi-20251028_220236
    game_links = soup.find_all("a", href=re.compile(r"/games/[^/]+"))

    # ページに対局が存在するかを記録（フィルタリング前）
    total_games_on_page = 0

    for link in game_links:
        href = link.get("href")
        if not href:
            continue

        # ページネーションリンクは除外（"history"や"page="を含む）
        if "history" in href or "page=" in href:
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

        # クエリパラメータを削除（?locale=jaなど）
        game_id = game_id.split("?")[0]

        # 対戦IDが正しい形式かチェック（user1-user2-timestampの形式）
        # timestampは YYYYMMDD_HHMMSS の形式
        if not re.match(r'^[^-]+-[^-]+-\d{8}_\d{6}', game_id):
            continue

        # ここまで来たら有効な対局
        total_games_on_page += 1

        # 対戦相手が指定されている場合はフィルタリング
        if opponent and opponent.lower() not in game_id.lower():
            continue

        # game_idから情報を抽出
        # 形式: [先手]-[後手]-YYYYMMDD_HHMMSS
        parts = game_id.split("-")
        if len(parts) >= 3:
            sente = parts[0]  # 先手
            gote = parts[1]   # 後手
            timestamp_str = parts[2]

            # タイムスタンプをISO形式に変換
            # YYYYMMDD_HHMMSS → YYYY-MM-DDTHH:MM:SS
            if "_" in timestamp_str:
                date_part, time_part = timestamp_str.split("_")
                if len(date_part) == 8 and len(time_part) == 6:
                    iso_datetime = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}T{time_part[:2]}:{time_part[2:4]}:{time_part[4:6]}"
                else:
                    iso_datetime = None
            else:
                iso_datetime = None
        else:
            sente = None
            gote = None
            iso_datetime = None

        # 勝敗情報を取得
        winner = "draw"  # デフォルトは引き分け
        # リンクの親要素（game_players）から勝敗画像を探す
        # HTMLの構造: <div class="game_players"> ... <div class="left_player"> ... <img class="win_lose_img" src="...sente_win.png">
        game_players_div = link.find_parent("div", class_="game_players")
        if not game_players_div:
            # game_players が見つからない場合は、上位の親要素を探す
            game_players_div = link.find_parent()
            for _ in range(5):  # 最大5階層まで探す
                if game_players_div and "game_players" in game_players_div.get("class", []):
                    break
                if game_players_div:
                    game_players_div = game_players_div.find_parent()
                else:
                    break

        if game_players_div:
            # game_players内のすべての画像を探す
            img_tags = game_players_div.find_all("img")
            for img in img_tags:
                src = img.get("src", "")
                if "sente_win" in src:
                    winner = "sente"
                    break
                elif "sente_lose" in src:
                    winner = "gote"
                    break

        # プレイヤークラス（段位）情報を取得
        sente_class = None
        gote_class = None
        if game_players_div:
            # player_names div内から段位を取得
            player_names_div = game_players_div.find("div", class_="player_names")
            if player_names_div:
                # 先手（左側）の段位
                player_dan_text_left = player_names_div.find("div", class_="player_dan_text_left")
                if player_dan_text_left:
                    sente_class = player_dan_text_left.get_text(strip=True)

                # 後手（右側）の段位
                player_dan_text_right = player_names_div.find("div", class_="player_dan_text_right")
                if player_dan_text_right:
                    gote_class = player_dan_text_right.get_text(strip=True)

        # バッジ情報を取得
        badges = []
        # game_players_divの親要素からgame_badgesを探す
        if game_players_div:
            parent_container = game_players_div.find_parent()
            if parent_container:
                game_badges_div = parent_container.find("div", class_="game_badges")
                if game_badges_div:
                    badge_links = game_badges_div.find_all("a", class_="badge_text")
                    for badge_link in badge_links:
                        badge_text = badge_link.get_text(strip=True)
                        if badge_text and badge_text.startswith("#"):
                            # 先頭の#を除去して追加
                            badges.append(badge_text[1:])

        # winnerから各プレイヤーのresultを計算
        if winner == "sente":
            sente_result = "win"
            gote_result = "lose"
        elif winner == "gote":
            sente_result = "lose"
            gote_result = "win"
        else:  # draw
            sente_result = "draw"
            gote_result = "draw"

        game_info = {
            "url": full_url,
            "game_id": game_id,
            "sente": {
                "name": sente,
                "class": sente_class,
                "result": sente_result
            },
            "gote": {
                "name": gote,
                "class": gote_class,
                "result": gote_result
            },
            "datetime": iso_datetime,
            "badges": badges
        }

        game_urls.append(game_info)

    # ページに対局が存在したかを返す
    has_games = total_games_on_page > 0
    return game_urls, has_games


def scrape_game_urls(
    driver,
    user: str,
    opponent: str,
    month: str = None,
    gtype: str = None,
    opponent_type: str = "normal",
    init_pos_type: str = "normal",
    limit: int = None
) -> List[Dict[str, str]]:
    """
    将棋ウォーズの対局履歴ページから特定の対戦相手との棋譜URLを抽出
    複数ページを自動的に巡回して全ての対局を取得

    Args:
        driver: Seleniumのwebdriver
        user: ユーザーID
        opponent: 対戦相手のID
        month: 対象月（YYYY-MM形式、Noneの場合は現在月）
        gtype: ゲームタイプ（None=10分切れ負け, s1=1手10秒, sb=3分切れ負け）
        opponent_type: 対戦相手タイプ（normal=ランク, friend=友達, etc.）
        init_pos_type: 初期配置タイプ（normal=通常, sprint=スプリント）
        limit: 最大ページ数（Noneの場合は全ページを取得）

    Returns:
        棋譜URLのリスト
    """
    # monthが指定されていない場合は現在月を使用
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    print(f"Fetching game history for {user} vs {opponent} in {month} (type: {opponent_type}, pos: {init_pos_type})...")

    all_game_urls = []
    page = 1

    while True:
        if limit is not None and page > limit:
            print(f"Reached limit: {limit}")
            break

        print(f"Fetching page {page}...")
        game_urls, has_games = scrape_page(driver, user, opponent, month, gtype, opponent_type, init_pos_type, page)

        # ページに対局が全く存在しない場合は終了
        if not has_games:
            print(f"No more games found at page {page}")
            break

        # フィルタリング後の結果を追加
        for game in game_urls:
            print(f"Found: {game['url']}")

        all_game_urls.extend(game_urls)

        # フィルタリング後が0件でも、ページに対局があれば次へ進む
        if not game_urls and opponent:
            print(f"No games with opponent '{opponent}' on page {page}, checking next page...")

        page += 1

    print(f"\nTotal games found: {len(all_game_urls)}")
    return all_game_urls


def save_to_json(data: List[Dict[str, str]], output_file: str, query_params: Dict[str, str]):
    """
    抽出したデータをJSONファイルに保存

    Args:
        data: 保存するデータ
        output_file: 出力ファイル名
        query_params: 検索に使用したパラメータ
    """
    output_data = {
        "params": query_params,
        "replays": data
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(data)} game URLs to {output_file}")


def main():
    """
    将棋ウォーズの棋譜URLを抽出してJSONに保存

    環境変数:
    - SHOGIWARS_USERNAME: ログインユーザー名
    - SHOGIWARS_PASSWORD: ログインパスワード
    - SHOGIWARS_HEADLESS: ヘッドレスモード true/false（デフォルト: false）
    - SHOGIWARS_MANUAL_CAPTCHA: 手動CAPTCHA待機 true/false（デフォルト: false）

    コマンドライン引数またはコード内設定でスクレイピングパラメータを指定できます
    """
    # 現在の年月を取得
    current_month = datetime.now().strftime("%Y-%m")

    # コマンドライン引数のパーサーを設定
    parser = argparse.ArgumentParser(
        description="将棋ウォーズの棋譜URLを抽出してJSONに保存"
    )
    parser.add_argument(
        "--opponent",
        default="",
        help="対戦相手のID（未指定の場合は全ての対局を取得）"
    )
    parser.add_argument(
        "--month",
        default=current_month,
        help=f"対象月 YYYY-MM形式 (default: {current_month})"
    )
    parser.add_argument(
        "--gtype",
        default=None,
        choices=["s1", "sb"],
        help="ゲームタイプ: s1=1手10秒, sb=3分切れ負け (default: 10分切れ負け)"
    )
    parser.add_argument(
        "--opponent-type",
        default="normal",
        choices=["normal", "friend", "coach", "closed_event", "learning"],
        help="対戦相手タイプ: normal=ランク, friend=友達, coach=指導, closed_event=大会, learning=ラーニング (default: normal)"
    )
    parser.add_argument(
        "--init-pos-type",
        default="normal",
        choices=["normal", "sprint"],
        help="初期配置タイプ: normal=通常, sprint=スプリント (default: normal)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="取得する最大ページ数 (default: 全ページ)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="出力ファイル名（未指定の場合は自動生成）"
    )

    args = parser.parse_args()

    # 引数から値を取得
    opponent = args.opponent
    month = args.month
    gtype = args.gtype
    opponent_type = args.opponent_type
    init_pos_type = args.init_pos_type
    limit = args.limit
    output_file = args.output

    # 環境変数から認証情報と実行オプションを取得
    login_username = os.environ.get("SHOGIWARS_USERNAME")
    login_password = os.environ.get("SHOGIWARS_PASSWORD")
    headless = os.environ.get("SHOGIWARS_HEADLESS", "").lower() in ("true", "1", "yes")
    manual_captcha = os.environ.get("SHOGIWARS_MANUAL_CAPTCHA", "").lower() in ("true", "1", "yes")

    # 認証情報が設定されていない場合は対話的に入力を求める
    if not login_username:
        login_username = input("将棋ウォーズのユーザー名を入力してください: ")
    if not login_password:
        login_password = getpass.getpass("将棋ウォーズのパスワードを入力してください: ")

    # WebDriverの初期化（undetected_chromedriverを使用）
    options = uc.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")

    # 基本的な設定
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = None
    try:
        print("Initializing Undetected Chrome WebDriver...")
        driver = uc.Chrome(options=options, version_main=None)

        # ログイン
        login_success, user = login_to_shogiwars(driver, login_username, login_password, manual_captcha=manual_captcha)
        if not login_success:
            print("ログインに失敗しました。")
            return

        if not user:
            print("エラー: ログインユーザーのIDを取得できませんでした。")
            return

        print(f"\n=== Scraping game history for user: {user} ===\n")

        # 出力ファイル名を生成（未指定の場合）
        if output_file is None:
            # resultディレクトリを作成（存在しない場合）
            result_dir = "result"
            os.makedirs(result_dir, exist_ok=True)

            # gtypeの文字列表現
            gtype_str = gtype if gtype else "10min"
            # ファイル名を生成
            if opponent:
                # 対戦相手が指定されている場合
                filename = f"game_replays_{gtype_str}_{month}_{user}_{opponent}.json"
            else:
                # 対戦相手が未指定（全検索）の場合
                filename = f"game_replays_{gtype_str}_{month}_{user}.json"

            output_filename = os.path.join(result_dir, filename)
            print(f"Output file: {output_filename}")
        else:
            output_filename = output_file

        # 棋譜URLを抽出
        game_urls = scrape_game_urls(
            driver=driver,
            user=user,
            opponent=opponent,
            month=month,
            gtype=gtype,
            opponent_type=opponent_type,
            init_pos_type=init_pos_type,
            limit=limit
        )

        if game_urls:
            # 検索パラメータを記録
            query_params = {
                "user": user,
                "opponent": opponent if opponent else "(all)",
                "month": month,
                "gtype": gtype if gtype else "10min",
                "opponent_type": opponent_type,
                "init_pos_type": init_pos_type,
                "limit": limit if limit else "(all)"
            }

            # JSONに保存
            save_to_json(game_urls, output_filename, query_params)
        else:
            print(f"\nNo games found with opponent: {opponent}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            print("Closing browser...")
            driver.quit()


if __name__ == "__main__":
    main()
