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
import matplotlib.pyplot as plt

# ページ設定
st.set_page_config(
    page_title="将棋ウォーズ棋譜ビューア",
    page_icon="♟️",
    layout="wide"
)

st.title("♟️ 将棋ウォーズ棋譜ビューア")

# セッションステートの初期化
if 'selected_opponent' not in st.session_state:
    st.session_state.selected_opponent = None

# 段位をソート用の数値に変換する関数
def rank_to_sort_key(rank):
    """段位を数値に変換してソート用のキーとする"""
    if not rank:
        return 999  # 不明な段位は最後に

    # 段の場合
    if "段" in rank:
        try:
            dan_map = {"初段": 0, "二段": -1, "三段": -2, "四段": -3, "五段": -4,
                      "六段": -5, "七段": -6, "八段": -7, "九段": -8}
            return dan_map.get(rank, 999)
        except:
            return 999

    # 級の場合
    if "級" in rank:
        try:
            kyu_num = int(rank.replace("級", ""))
            return kyu_num
        except:
            return 999

    return 999

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
                replays = file_data.get("replays", [])
                all_replays.extend(replays)
                loaded_files.append(json_file.name)

                # 最初のファイルからユーザー名を取得
                if user_name is None:
                    params = file_data.get("params", {})
                    user_name = params.get("user", "")
        except Exception as e:
            st.sidebar.warning(f"⚠️ {json_file.name} の読み込みに失敗: {e}")

    if loaded_files:
        st.sidebar.success(f"✅ {len(loaded_files)}個のファイルから{len(all_replays)}件の棋譜を読み込みました")
        st.sidebar.info("読み込んだファイル:\n" + "\n".join([f"- {f}" for f in loaded_files]))
        if user_name:
            st.sidebar.info(f"ユーザー: {user_name}")
    else:
        st.sidebar.warning("result/ディレクトリにJSONファイルがありません")
else:
    st.sidebar.warning("result/ディレクトリが見つかりません")

# データ表示
if all_replays:
    # 対局データ
    replays = all_replays

    if not replays:
        st.warning("対局データがありません")
    else:
        st.header(f"🎮 対局一覧 ({len(replays)}件)")

        # フィルター
        st.subheader("フィルター")

        # 日付範囲の取得（全対局から）
        all_dates = []
        for replay in replays:
            dt_str = replay.get("datetime", "")
            if dt_str:
                try:
                    dt = datetime.fromisoformat(dt_str)
                    all_dates.append(dt.date())
                except:
                    pass

        # 日付範囲フィルター
        if all_dates:
            min_date = min(all_dates)
            max_date = max(all_dates)

            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_date = st.date_input(
                    "開始日",
                    value=min_date,
                    min_value=min_date,
                    max_value=max_date
                )
            with col_date2:
                end_date = st.date_input(
                    "終了日",
                    value=max_date,
                    min_value=min_date,
                    max_value=max_date
                )
        else:
            start_date = None
            end_date = None

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            # 勝敗フィルター
            result_filter = st.selectbox(
                "勝敗",
                ["すべて", "勝ち", "負け", "引き分け"]
            )

        with col2:
            # 手番フィルター
            teban_filter = st.selectbox(
                "手番",
                ["すべて", "先手", "後手"]
            )

        with col3:
            # 対戦相手フィルター
            all_opponents = set()
            if user_name:
                for replay in replays:
                    sente_name = replay.get("sente", {}).get("name", "")
                    gote_name = replay.get("gote", {}).get("name", "")
                    if sente_name != user_name and sente_name:
                        all_opponents.add(sente_name)
                    if gote_name != user_name and gote_name:
                        all_opponents.add(gote_name)

            opponent_options = ["すべて"] + sorted(list(all_opponents))

            # セッションステートから対戦相手が指定されている場合、そのインデックスを取得
            default_index = 0
            if st.session_state.selected_opponent and st.session_state.selected_opponent in opponent_options:
                default_index = opponent_options.index(st.session_state.selected_opponent)

            opponent_filter = st.selectbox(
                "対戦相手",
                opponent_options,
                index=default_index,
                key="opponent_selectbox"
            )

            # セレクトボックスが変更されたら、セッションステートを更新
            if opponent_filter != st.session_state.selected_opponent:
                st.session_state.selected_opponent = opponent_filter if opponent_filter != "すべて" else None

        with col4:
            # 相手段位フィルター
            all_classes = set()
            if user_name:
                for replay in replays:
                    sente = replay.get("sente", {})
                    gote = replay.get("gote", {})
                    if sente.get("name") == user_name:
                        opponent_class = gote.get("class", "")
                    else:
                        opponent_class = sente.get("class", "")
                    if opponent_class:
                        all_classes.add(opponent_class)

            # 段位をカスタムソート
            sorted_classes = sorted(list(all_classes), key=rank_to_sort_key)

            class_filter = st.selectbox(
                "相手段位",
                ["すべて"] + sorted_classes
            )

        with col5:
            # 戦型フィルター
            all_badges = set()
            for replay in replays:
                badges = replay.get("badges", [])
                all_badges.update(badges)

            badge_filter = st.selectbox(
                "戦型",
                ["すべて", "戦型なし"] + sorted(list(all_badges))
            )

        # データフィルタリング
        filtered_replays = []

        if not user_name:
            st.warning("ユーザー名が取得できませんでした")
        else:
            for replay in replays:
                sente = replay.get("sente", {})
                gote = replay.get("gote", {})

                # ユーザーの手番を判定
                if sente.get("name") == user_name:
                    user_result = sente.get("result", "")
                    opponent_name = gote.get("name", "")
                    opponent_class = gote.get("class", "")
                    user_side = "先手"
                elif gote.get("name") == user_name:
                    user_result = gote.get("result", "")
                    opponent_name = sente.get("name", "")
                    opponent_class = sente.get("class", "")
                    user_side = "後手"
                else:
                    # ユーザーが参加していない対局はスキップ
                    continue

                # 日付フィルター
                if start_date and end_date:
                    dt_str = replay.get("datetime", "")
                    if dt_str:
                        try:
                            replay_date = datetime.fromisoformat(dt_str).date()
                            if not (start_date <= replay_date <= end_date):
                                continue
                        except:
                            continue
                    else:
                        continue

                # 勝敗フィルター
                if result_filter != "すべて":
                    filter_map = {"勝ち": "win", "負け": "lose", "引き分け": "draw"}
                    if user_result != filter_map.get(result_filter):
                        continue

                # 手番フィルター
                if teban_filter != "すべて" and user_side != teban_filter:
                    continue

                # 対戦相手フィルター
                if opponent_filter != "すべて" and opponent_name != opponent_filter:
                    continue

                # 相手段位フィルター
                if class_filter != "すべて" and opponent_class != class_filter:
                    continue

                # 戦型フィルター
                if badge_filter != "すべて":
                    badges = replay.get("badges", [])
                    if badge_filter == "戦型なし":
                        # 戦型が空でない場合はスキップ
                        if badges:
                            continue
                    else:
                        # 特定の戦型が含まれていない場合はスキップ
                        if badge_filter not in badges:
                            continue

                filtered_replays.append(replay)

        # 統計情報（フィルタリング後のデータで計算）
        if user_name and filtered_replays:
            # 勝敗カウント用のデータを先に作成
            temp_stats = []
            graph_data = []

            for replay in filtered_replays:
                sente = replay.get("sente", {})
                gote = replay.get("gote", {})

                if sente.get("name") == user_name:
                    user_result = sente.get("result", "")
                else:
                    user_result = gote.get("result", "")

                result_icon = {"win": "勝ち", "lose": "負け", "draw": "引き分け"}
                temp_stats.append(result_icon.get(user_result, ""))

                # グラフ用データ（日時と勝敗の数値）
                dt_str = replay.get("datetime", "")
                if dt_str:
                    try:
                        dt = datetime.fromisoformat(dt_str)
                        result_value = {"win": 1, "lose": -1, "draw": 0}.get(user_result, 0)
                        graph_data.append({"日時": dt, "勝敗": result_value})
                    except:
                        pass

            st.divider()
            st.subheader("📈 統計")

            col1, col2, col3, col4 = st.columns(4)

            win_count = sum(1 for r in temp_stats if r == "勝ち")
            lose_count = sum(1 for r in temp_stats if r == "負け")
            draw_count = sum(1 for r in temp_stats if r == "引き分け")
            total = len(temp_stats)

            with col1:
                st.metric("総対局数", total)
            with col2:
                win_rate = (win_count / total * 100) if total > 0 else 0
                st.metric("勝ち", f"{win_count} ({win_rate:.1f}%)")
            with col3:
                lose_rate = (lose_count / total * 100) if total > 0 else 0
                st.metric("負け", f"{lose_count} ({lose_rate:.1f}%)")
            with col4:
                draw_rate = (draw_count / total * 100) if total > 0 else 0
                st.metric("引き分け", f"{draw_count} ({draw_rate:.1f}%)")

            # 勝敗推移グラフ
            if graph_data:
                st.subheader("勝敗推移")
                graph_df = pd.DataFrame(graph_data)
                graph_df = graph_df.sort_values(by="日時")

                # matplotlibでグラフを描画
                # 日本語フォント設定
                plt.rcParams['font.family'] = 'Hiragino Sans'

                fig, ax = plt.subplots(figsize=(10, 2.0))
                ax.plot(graph_df["日時"], graph_df["勝敗"], marker='o', linestyle='-', linewidth=1, markersize=3)
                ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
                ax.set_ylim(-1.5, 1.5)
                ax.set_yticks([-1, 0, 1])
                ax.set_yticklabels(["負け", "引き分け", "勝ち"])
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()

                st.pyplot(fig)
                plt.close()

            st.divider()

        # テーブル表示用のデータ作成
        table_data = []
        if user_name:
            st.info(f"表示件数: {len(filtered_replays)} / {len(replays)} 件")

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

                # 戦型
                badges = replay.get("badges", [])
                badges_display = " ".join(badges) if badges else ""

                table_data.append({
                    "日時": dt_display,
                    "勝敗": result_display,
                    "手番": user_side,
                    "対戦相手": opponent_name,
                    "相手段位": opponent_class,
                    "戦型": badges_display,
                    "URL": replay.get("url", ""),
                    "game_id": replay.get("game_id", "")
                })

        # DataFrame作成
        if table_data:
            df = pd.DataFrame(table_data)

            # game_idは非表示
            df_display = df.drop(columns=["game_id"])

            # 日時で降順ソート（新しい順）
            df_display = df_display.sort_values(by="日時", ascending=False).reset_index(drop=True)

            # st.dataframeで表示（ソート機能付き）
            st.dataframe(
                df_display,
                column_config={
                    "日時": st.column_config.TextColumn("日時", width="medium"),
                    "勝敗": st.column_config.TextColumn("勝敗", width="small"),
                    "手番": st.column_config.TextColumn("手番", width="small"),
                    "対戦相手": st.column_config.TextColumn("対戦相手", width="medium"),
                    "相手段位": st.column_config.TextColumn("相手段位", width="small"),
                    "戦型": st.column_config.TextColumn("戦型", width="large"),
                    "URL": st.column_config.LinkColumn(
                        "棋譜",
                        display_text="棋譜を見る"
                    ),
                },
                hide_index=True,
                width='stretch',
                height=600
            )
        else:
            st.warning("表示する対局がありません")
else:
    st.info("result/ディレクトリにJSONファイルがありません")

    # 使い方
    st.markdown("""
    ## 使い方

    1. `result/` ディレクトリにJSONファイルを配置してください
    2. アプリを起動すると、すべてのJSONファイルが自動的に読み込まれます
    3. 対局一覧が表示されます
    4. フィルターを使って対局を絞り込むことができます

    ## JSONファイルの生成

    JSONファイルは `shogiwars_scraper.py` で生成できます：

    ```bash
    export SHOGIWARS_USERNAME="your_username"
    export SHOGIWARS_PASSWORD="your_password"
    python shogiwars_scraper.py --gtype s1 --month 2024-10
    ```

    生成されたファイルは `result/` ディレクトリに保存されます。
    """)
