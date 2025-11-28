#!/usr/bin/env python3
"""
読み込みログページ（認証が必要）
"""

import streamlit as st
import json
from pathlib import Path
import os

# ページ設定
st.set_page_config(
    page_title="読み込みログ - 将棋ウォーズ棋譜ビューア",
    page_icon="📋",
    layout="wide"
)

st.title("📋 読み込みログ")

# セッションステートの初期化
if 'is_authenticated' not in st.session_state:
    st.session_state.is_authenticated = False

# パスワードを環境変数から取得（デフォルト: "admin"）
logs_password = os.getenv("LOGS_PASSWORD", "admin")

# 認証済みの場合
if st.session_state.is_authenticated:
    col_log1, col_log2 = st.columns([6, 1])
    with col_log2:
        if st.button("ログアウト", key="logout_btn"):
            st.session_state.is_authenticated = False
            st.rerun()

    with col_log1:
        st.info("🔓 認証済み")

    st.divider()

    # result/ディレクトリ内のすべてのJSONファイルを読み込み
    result_dir = Path("result")
    all_replays = []
    loaded_files = []
    user_name = None

    if result_dir.exists():
        json_files = sorted(result_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

        for json_file in json_files:
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                    params = file_data.get("params", {})
                    replays = file_data.get("replays", [])

                    # 各replayにparamsの情報を付与
                    for replay in replays:
                        replay["_opponent_type"] = params.get("opponent_type", "normal")
                        replay["_init_pos_type"] = params.get("init_pos_type", "normal")
                        replay["_gtype"] = params.get("gtype", "10min")

                    all_replays.extend(replays)
                    loaded_files.append(json_file.name)

                    # 最初のファイルからユーザー名を取得
                    if user_name is None:
                        user_name = params.get("user", "")
            except Exception as e:
                st.warning(f"⚠️ {json_file.name} の読み込みに失敗: {e}")

    # 読み込みログの表示
    if loaded_files:
        st.success(f"✅ {len(loaded_files)}個のファイルから{len(all_replays)}件の棋譜を読み込みました")
        if user_name:
            st.info(f"**ユーザー:** {user_name}")

        st.markdown("**読み込んだファイル:**")
        for f in loaded_files:
            st.text(f"  • {f}")

        # 詳細情報を表形式で表示
        st.divider()
        st.subheader("ファイル詳細")

        file_details = []
        for json_file in sorted(result_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                    params = file_data.get("params", {})
                    replays = file_data.get("replays", [])

                    opponent_type_label = {
                        "normal": "ランク",
                        "friend": "友達",
                        "coach": "指導",
                        "closed_event": "大会",
                        "learning": "ラーニング"
                    }.get(params.get("opponent_type", "normal"), "不明")

                    init_pos_type_label = {
                        "normal": "通常",
                        "sprint": "スプリント"
                    }.get(params.get("init_pos_type", "normal"), "不明")

                    gtype_label = {
                        "s1": "10秒",
                        "sb": "3分",
                        "10min": "10分"
                    }.get(params.get("gtype", "10min"), "不明")

                    file_details.append({
                        "ファイル名": json_file.name,
                        "対局数": len(replays),
                        "対局相手タイプ": opponent_type_label,
                        "初期配置": init_pos_type_label,
                        "持ち時間": gtype_label,
                        "取得対象月": params.get("month", "不明")
                    })
            except Exception as e:
                file_details.append({
                    "ファイル名": json_file.name,
                    "対局数": "エラー",
                    "対局相手タイプ": "-",
                    "初期配置": "-",
                    "持ち時間": "-",
                    "取得対象月": f"読み込み失敗: {e}"
                })

        if file_details:
            import pandas as pd
            df = pd.DataFrame(file_details)
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("result/ディレクトリにJSONファイルがありません")

        st.markdown("""
        ## JSONファイルの生成方法

        JSONファイルは `shogiwars_scraper.py` で生成できます：

        ```bash
        export SHOGIWARS_USERNAME="your_username"
        export SHOGIWARS_PASSWORD="your_password"
        python shogiwars_scraper.py --gtype s1 --month 2024-10
        ```

        生成されたファイルは `result/` ディレクトリに保存されます。
        """)

else:
    # 未認証の場合、ログインフォームを表示
    st.warning("🔒 読み込みログを表示するには認証が必要です")

    with st.form("login_form"):
        password_input = st.text_input("パスワード", type="password", key="password_input")
        submit_button = st.form_submit_button("ログイン")

        if submit_button:
            if password_input == logs_password:
                st.session_state.is_authenticated = True
                st.rerun()
            else:
                st.error("❌ パスワードが正しくありません")

    st.info(f"💡 ヒント: 環境変数 `LOGS_PASSWORD` でパスワードを設定できます（デフォルト: admin）")

    st.divider()

    st.markdown("""
    ## このページについて

    このページでは以下の情報を確認できます：
    - 読み込まれたJSONファイルの一覧
    - 各ファイルの対局数と設定情報
    - ユーザー名などのメタ情報

    セキュリティのため、パスワード認証が必要です。
    """)
