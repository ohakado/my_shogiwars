#!/usr/bin/env python3
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
    user_id: str,
    opponent: str,
    month: str,
    gtype: str,
    page: int
) -> List[Dict[str, str]]:
    """
    1ページ分の棋譜URLを抽出

    Args:
        driver: Seleniumのwebdriver
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
        return []

    soup = BeautifulSoup(page_source, "html.parser")

    # 棋譜URLを抽出
    game_urls = []

    # 対局履歴のリンクを探す
    # パターン: https://shogiwars.heroz.jp/games/ohakado-guranola_oisi-20251028_220236
    game_links = soup.find_all("a", href=re.compile(r"/games/[^/]+"))

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

        # 対戦相手が指定されている場合はフィルタリング
        if opponent and opponent.lower() not in game_id.lower():
            continue

        # game_idから情報を抽出
        # 形式: user1-user2-YYYYMMDD_HHMMSS
        parts = game_id.split("-")
        if len(parts) >= 3:
            player1 = parts[0]
            player2 = parts[1]
            timestamp_str = parts[2]

            # 対戦相手を特定（user_idではない方）
            game_opponent = player2 if player1.lower() == user_id.lower() else player1

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
            game_opponent = None
            iso_datetime = None

        game_info = {
            "url": full_url,
            "game_id": game_id,
            "opponent": game_opponent,
            "datetime": iso_datetime
        }

        game_urls.append(game_info)

    return game_urls


def scrape_game_urls(
    driver,
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
        driver: Seleniumのwebdriver
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
        game_urls = scrape_page(driver, user_id, opponent, month, gtype, page)

        if not game_urls:
            print(f"No more games found at page {page}")
            break

        for game in game_urls:
            print(f"Found: {game['url']}")

        all_game_urls.extend(game_urls)
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
    # 現在の年月を取得
    current_month = datetime.now().strftime("%Y-%m")

    parser = argparse.ArgumentParser(
        description="将棋ウォーズの棋譜URLを抽出してJSONに保存（ログイン対応版）"
    )
    parser.add_argument(
        "--login-user",
        help="将棋ウォーズのログインユーザー名（環境変数 SHOGIWARS_USERNAME からも取得可能）"
    )
    parser.add_argument(
        "--login-password",
        help="将棋ウォーズのログインパスワード（環境変数 SHOGIWARS_PASSWORD からも取得可能）"
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
        default=None,
        help="出力ファイル名（未指定の場合は game_replays_[gtype]_[month]_[user_id]_[opponent].json）"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="ヘッドレスモードで実行（ブラウザを表示しない）"
    )
    parser.add_argument(
        "--manual-captcha",
        action="store_true",
        help="CAPTCHAを手動で完了できるように待機する（推奨）"
    )

    args = parser.parse_args()

    # ログイン認証情報を取得
    login_username = args.login_user or os.environ.get("SHOGIWARS_USERNAME")
    login_password = args.login_password or os.environ.get("SHOGIWARS_PASSWORD")

    # 認証情報が設定されていない場合は対話的に入力を求める
    if not login_username:
        login_username = input("将棋ウォーズのユーザー名を入力してください: ")
    if not login_password:
        login_password = getpass.getpass("将棋ウォーズのパスワードを入力してください: ")

    # WebDriverの初期化（undetected_chromedriverを使用）
    options = uc.ChromeOptions()
    if args.headless:
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
        login_success, user_id = login_to_shogiwars(driver, login_username, login_password, manual_captcha=args.manual_captcha)
        if not login_success:
            print("ログインに失敗しました。")
            return

        if not user_id:
            print("エラー: ログインユーザーのIDを取得できませんでした。")
            return

        print(f"\n=== Scraping game history for user: {user_id} ===\n")

        # 出力ファイル名を生成（未指定の場合）
        if args.output is None:
            # resultディレクトリを作成（存在しない場合）
            result_dir = "result"
            os.makedirs(result_dir, exist_ok=True)

            # gtypeの文字列表現
            gtype_str = args.gtype if args.gtype else "10min"
            # ファイル名を生成
            if args.opponent:
                # 対戦相手が指定されている場合
                filename = f"game_replays_{gtype_str}_{args.month}_{user_id}_{args.opponent}.json"
            else:
                # 対戦相手が未指定（全検索）の場合
                filename = f"game_replays_{gtype_str}_{args.month}_{user_id}.json"

            output_filename = os.path.join(result_dir, filename)
            print(f"Output file: {output_filename}")
        else:
            output_filename = args.output

        # 棋譜URLを抽出
        game_urls = scrape_game_urls(
            driver=driver,
            user_id=user_id,
            opponent=args.opponent,
            month=args.month,
            gtype=args.gtype,
            max_pages=args.max_pages
        )

        if game_urls:
            # 検索パラメータを記録
            query_params = {
                "user_id": user_id,
                "opponent": args.opponent if args.opponent else "(all)",
                "month": args.month,
                "gtype": args.gtype if args.gtype else "10min",
                "max_pages": args.max_pages if args.max_pages else "(all)"
            }

            # JSONに保存
            save_to_json(game_urls, output_filename, query_params)
        else:
            print(f"\nNo games found with opponent: {args.opponent}")

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
