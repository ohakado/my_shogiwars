#!/usr/bin/env python3
"""
将棋ウォーズ棋譜ビューア (Streamlit)
JSONファイルから棋譜データを読み込んで表示します
"""

import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="将棋ウォーズ棋譜ビューア",
    page_icon="♟️",
    layout="wide"
)

st.title("♟️ 将棋ウォーズ棋譜ビューア")

# サイドバー: ファイル選択
st.sidebar.header("JSONファイル選択")

# result/ディレクトリ内のJSONファイルを取得
result_dir = Path("result")
if result_dir.exists():
    json_files = sorted(result_dir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    file_names = [f.name for f in json_files]

    if file_names:
        selected_file = st.sidebar.selectbox(
            "保存済みファイル",
            ["選択してください"] + file_names
        )
    else:
        selected_file = None
        st.sidebar.info("result/ディレクトリにJSONファイルがありません")
else:
    selected_file = None
    st.sidebar.warning("result/ディレクトリが見つかりません")

# ファイルアップロード
uploaded_file = st.sidebar.file_uploader(
    "または、ファイルをアップロード",
    type="json"
)

# データ読み込み
data = None
if uploaded_file is not None:
    data = json.load(uploaded_file)
    st.sidebar.success(f"✅ {uploaded_file.name} を読み込みました")
elif selected_file and selected_file != "選択してください":
    file_path = result_dir / selected_file
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    st.sidebar.success(f"✅ {selected_file} を読み込みました")

# データ表示
if data:
    # パラメータ表示
    st.header("📊 検索パラメータ")
    params = data.get("params", {})

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("ユーザー", params.get("user", "N/A"))
    with col2:
        st.metric("対戦相手", params.get("opponent", "(all)"))
    with col3:
        st.metric("対象月", params.get("month", "N/A"))
    with col4:
        st.metric("ゲームタイプ", params.get("gtype", "10min"))
    with col5:
        st.metric("取得ページ数", params.get("limit", "(all)"))

    st.divider()

    # 対局データ
    replays = data.get("replays", [])

    if not replays:
        st.warning("対局データがありません")
    else:
        st.header(f"🎮 対局一覧 ({len(replays)}件)")

        # フィルター
        st.subheader("フィルター")
        col1, col2, col3 = st.columns(3)

        with col1:
            # ユーザー名を取得
            user_name = params.get("user", "")

            # 勝敗フィルター
            result_filter = st.selectbox(
                "勝敗",
                ["すべて", "勝ち", "負け", "引き分け"]
            )

        with col2:
            # 対戦相手フィルター
            all_opponents = set()
            for replay in replays:
                sente_name = replay.get("sente", {}).get("name", "")
                gote_name = replay.get("gote", {}).get("name", "")
                if sente_name != user_name:
                    all_opponents.add(sente_name)
                if gote_name != user_name:
                    all_opponents.add(gote_name)

            opponent_filter = st.selectbox(
                "対戦相手",
                ["すべて"] + sorted(list(all_opponents))
            )

        with col3:
            # バッジフィルター
            all_badges = set()
            for replay in replays:
                badges = replay.get("badges", [])
                all_badges.update(badges)

            badge_filter = st.selectbox(
                "バッジ",
                ["すべて"] + sorted(list(all_badges))
            )

        # データフィルタリング
        filtered_replays = []
        for replay in replays:
            sente = replay.get("sente", {})
            gote = replay.get("gote", {})

            # ユーザーの手番を判定
            if sente.get("name") == user_name:
                user_result = sente.get("result", "")
                opponent_name = gote.get("name", "")
            else:
                user_result = gote.get("result", "")
                opponent_name = sente.get("name", "")

            # 勝敗フィルター
            if result_filter != "すべて":
                filter_map = {"勝ち": "win", "負け": "lose", "引き分け": "draw"}
                if user_result != filter_map.get(result_filter):
                    continue

            # 対戦相手フィルター
            if opponent_filter != "すべて" and opponent_name != opponent_filter:
                continue

            # バッジフィルター
            if badge_filter != "すべて":
                badges = replay.get("badges", [])
                if badge_filter not in badges:
                    continue

            filtered_replays.append(replay)

        st.info(f"表示件数: {len(filtered_replays)} / {len(replays)} 件")

        # テーブル表示用のデータ作成
        table_data = []
        for replay in filtered_replays:
            sente = replay.get("sente", {})
            gote = replay.get("gote", {})

            # ユーザーの手番を判定
            if sente.get("name") == user_name:
                user_side = "先手"
                user_result = sente.get("result", "")
                opponent_name = gote.get("name", "")
                opponent_class = gote.get("class", "")
            else:
                user_side = "後手"
                user_result = gote.get("result", "")
                opponent_name = sente.get("name", "")
                opponent_class = sente.get("class", "")

            # 勝敗アイコン
            result_icon = {"win": "🟢 勝ち", "lose": "🔴 負け", "draw": "⚪ 引き分け"}
            result_display = result_icon.get(user_result, user_result)

            # 日時
            dt_str = replay.get("datetime", "")
            if dt_str:
                try:
                    dt = datetime.fromisoformat(dt_str)
                    dt_display = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    dt_display = dt_str
            else:
                dt_display = "N/A"

            # バッジ
            badges = replay.get("badges", [])
            badges_display = " ".join(badges) if badges else ""

            table_data.append({
                "日時": dt_display,
                "手番": user_side,
                "勝敗": result_display,
                "対戦相手": opponent_name,
                "相手段位": opponent_class,
                "バッジ": badges_display,
                "URL": replay.get("url", ""),
                "game_id": replay.get("game_id", "")
            })

        # DataFrame作成
        if table_data:
            df = pd.DataFrame(table_data)

            # URLをクリック可能なリンクに変換
            df_display = df.copy()
            df_display = df_display.drop(columns=["game_id"])  # game_idは非表示

            # データフレーム表示
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn("棋譜リンク")
                }
            )

            # 統計情報
            st.divider()
            st.subheader("📈 統計")

            col1, col2, col3, col4 = st.columns(4)

            # 勝敗統計
            win_count = sum(1 for item in table_data if "勝ち" in item["勝敗"])
            lose_count = sum(1 for item in table_data if "負け" in item["勝敗"])
            draw_count = sum(1 for item in table_data if "引き分け" in item["勝敗"])
            total = len(table_data)

            with col1:
                st.metric("総対局数", total)
            with col2:
                win_rate = (win_count / total * 100) if total > 0 else 0
                st.metric("勝ち", f"{win_count} ({win_rate:.1f}%)")
            with col3:
                st.metric("負け", f"{lose_count}")
            with col4:
                st.metric("引き分け", f"{draw_count}")
        else:
            st.warning("表示する対局がありません")
else:
    st.info("👈 サイドバーからJSONファイルを選択してください")

    # 使い方
    st.markdown("""
    ## 使い方

    1. サイドバーから既存のJSONファイルを選択、またはファイルをアップロードしてください
    2. 対局一覧が表示されます
    3. フィルターを使って対局を絞り込むことができます

    ## JSONファイルの生成

    JSONファイルは `scrape_shogiwars.py` で生成できます：

    ```bash
    export SHOGIWARS_USERNAME="your_username"
    export SHOGIWARS_PASSWORD="your_password"
    python scrape_shogiwars.py --gtype s1 --month 2024-10
    ```

    生成されたファイルは `result/` ディレクトリに保存されます。
    """)
