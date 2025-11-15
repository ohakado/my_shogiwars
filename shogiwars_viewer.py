#!/usr/bin/env python3
"""
将棋ウォーズ棋譜ビューア (Streamlit)
JSONファイルから棋譜データを読み込んで表示します
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

# ページ設定
st.set_page_config(
    page_title="将棋ウォーズ棋譜ビューア",
    page_icon="♟️",
    layout="wide"
)

# Google Analytics
GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "")

if GA_MEASUREMENT_ID:
    components.html(f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_MEASUREMENT_ID}');
    </script>
    """, height=0)

st.title("♟️ 将棋ウォーズ棋譜ビューア")

# セッションステートの初期化
if 'selected_opponent' not in st.session_state:
    st.session_state.selected_opponent = None
if 'selected_badge' not in st.session_state:
    st.session_state.selected_badge = None
if 'grid_key_counter' not in st.session_state:
    st.session_state.grid_key_counter = 0

# 段位をソート用の数値に変換する関数
def rank_to_sort_key(rank):
    """段位を数値に変換してソート用のキーとする
    降順（大→小）: 九段(109) → ... → 初段(101) → 1級(99) → 2級(98) → ... → 30級(70)
    昇順（小→大）: 30級(70) → ... → 2級(98) → 1級(99) → 初段(101) → ... → 九段(109)
    """
    if not rank:
        return 0  # 不明な段位は最初に

    # 段の場合（100より大きい数で、数字が大きいほど強い）
    if "段" in rank:
        try:
            dan_map = {"初段": 101, "二段": 102, "三段": 103, "四段": 104, "五段": 105,
                      "六段": 106, "七段": 107, "八段": 108, "九段": 109, "十段": 110}
            return dan_map.get(rank, 0)
        except:
            return 0

    # 級の場合（100 - 級数で、数字が小さいほど強い: 1級=99 > 2級=98 > 3級=97...）
    if "級" in rank:
        try:
            kyu_num = int(rank.replace("級", ""))
            return 100 - kyu_num  # 1級=99, 2級=98, ..., 30級=70
        except:
            return 0

    return 0

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
            st.sidebar.warning(f"⚠️ {json_file.name} の読み込みに失敗: {e}")

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
        st.info("💡 棋譜リストの対戦相手名や戦型（青色のリンク）をクリックすると絞り込めます")

        # 対局相手タイプ、初期配置タイプ、持ち時間フィルター
        col_type1, col_type2, col_type3 = st.columns(3)

        with col_type1:
            opponent_type_filter = st.selectbox(
                "対局相手タイプ",
                ["normal", "friend", "coach", "closed_event", "learning"],
                format_func=lambda x: {
                    "normal": "ランク",
                    "friend": "友達",
                    "coach": "指導",
                    "closed_event": "大会",
                    "learning": "ラーニング"
                }[x],
                index=0  # デフォルト: ランク
            )

        with col_type2:
            init_pos_type_filter = st.selectbox(
                "初期配置タイプ",
                ["normal", "sprint"],
                format_func=lambda x: {
                    "normal": "通常",
                    "sprint": "スプリント"
                }[x],
                index=0  # デフォルト: 通常
            )

        with col_type3:
            gtype_filter = st.selectbox(
                "持ち時間",
                ["s1", "sb", "10min"],
                format_func=lambda x: {
                    "s1": "10秒",
                    "sb": "3分",
                    "10min": "10分"
                }[x],
                index=0  # デフォルト: 10秒
            )

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
            if st.session_state.selected_opponent and st.session_state.selected_opponent in opponent_options:
                default_index = opponent_options.index(st.session_state.selected_opponent)
            else:
                default_index = 0

            opponent_filter = st.selectbox(
                "対戦相手",
                opponent_options,
                index=default_index
            )

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

            # 段位をカスタムソート（降順：九段→...→初段→1級→...→30級）
            sorted_classes = sorted(list(all_classes), key=rank_to_sort_key, reverse=True)

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

            badge_options = ["すべて", "戦型なし"] + sorted(list(all_badges))

            # セッションステートから戦型が指定されている場合、そのインデックスを取得
            if st.session_state.selected_badge and st.session_state.selected_badge in badge_options:
                badge_default_index = badge_options.index(st.session_state.selected_badge)
            else:
                badge_default_index = 0

            badge_filter = st.selectbox(
                "戦型",
                badge_options,
                index=badge_default_index
            )

        # データフィルタリング
        filtered_replays = []

        if not user_name:
            st.warning("ユーザー名が取得できませんでした")
        else:
            for replay in replays:
                # 対局相手タイプ、初期配置タイプ、持ち時間でフィルター
                if replay.get("_opponent_type") != opponent_type_filter:
                    continue
                if replay.get("_init_pos_type") != init_pos_type_filter:
                    continue
                if replay.get("_gtype") != gtype_filter:
                    continue

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

            # フィルター条件を日本語に変換
            opponent_type_label = {
                "normal": "ランク",
                "friend": "友達",
                "coach": "指導",
                "closed_event": "大会",
                "learning": "ラーニング"
            }[opponent_type_filter]

            init_pos_type_label = {
                "normal": "通常",
                "sprint": "スプリント"
            }[init_pos_type_filter]

            gtype_label = {
                "s1": "10秒",
                "sb": "3分",
                "10min": "10分"
            }[gtype_filter]

            # 日付範囲のフォーマット
            date_range_str = f"{start_date} - {end_date}" if start_date and end_date else ""

            st.subheader(f"📈 統計 ({opponent_type_label} / {init_pos_type_label} / {gtype_label} / {date_range_str})")

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

                # ソートキーを保持
                sort_key = rank_to_sort_key(opponent_class)

                table_data.append({
                    "日時": dt_display,
                    "勝敗": result_display,
                    "手番": user_side,
                    "対戦相手": opponent_name,
                    "相手段位": opponent_class,
                    "相手段位ソートキー": sort_key,
                    "戦型": badges_display,
                    "戦型リスト": badges,  # JavaScriptで使用するため配列で保持
                    "clicked_badge": "",  # クリックされたバッジを保持
                    "URL": replay.get("url", ""),
                    "game_id": replay.get("game_id", "")
                })

        # DataFrame作成
        if table_data:
            df = pd.DataFrame(table_data)

            # 日時で降順ソート（新しい順）
            df = df.sort_values(by="日時", ascending=False).reset_index(drop=True)

            # 戦型リストをJSON文字列に変換（JavaScriptで使用するため）
            df['戦型リスト'] = df['戦型リスト'].apply(lambda x: json.dumps(x, ensure_ascii=False))

            # 表示用のDataFrame（game_idは非表示、その他は保持）
            df_display = df.drop(columns=["game_id"])

            # AgGridの設定
            gb = GridOptionsBuilder.from_dataframe(df_display)

            # 全列の基本設定
            gb.configure_default_column(
                filterable=False,
                sortable=True,
                resizable=True
            )

            # 各列の設定
            gb.configure_column("日時", width=150)
            gb.configure_column("勝敗", width=100)
            gb.configure_column("手番", width=80)

            # 対戦相手列をクリック可能にする（クリックで行を選択）
            opponent_renderer = JsCode("""
            class OpponentCellRenderer {
                init(params) {
                    this.eGui = document.createElement('span');
                    if (params.value) {
                        this.eGui.innerText = params.value;
                        this.eGui.style.color = '#0066cc';
                        this.eGui.style.cursor = 'pointer';
                        this.eGui.style.textDecoration = 'underline';
                        this.eGui.title = 'クリックしてこの対戦相手で絞り込み';

                        // クリックイベントで行を選択
                        this.eGui.addEventListener('click', () => {
                            params.node.setSelected(true, true);
                        });
                    }
                }
                getGui() {
                    return this.eGui;
                }
            }
            """)
            gb.configure_column("対戦相手", width=150, cellRenderer=opponent_renderer)

            # ソートキー列を非表示にする
            gb.configure_column("相手段位ソートキー", hide=True)

            # 相手段位列にカスタムソートを設定（JsCodeを使用）
            rank_comparator = JsCode("""
            function(valueA, valueB, nodeA, nodeB, isInverted) {
                var sortKeyA = nodeA.data['相手段位ソートキー'];
                var sortKeyB = nodeB.data['相手段位ソートキー'];
                return sortKeyA - sortKeyB;
            }
            """)
            gb.configure_column("相手段位", width=100, comparator=rank_comparator)

            # 戦型列を各バッジをクリック可能にする
            badge_renderer = JsCode("""
            class BadgeCellRenderer {
                init(params) {
                    this.eGui = document.createElement('div');
                    const badgesJson = params.data['戦型リスト'];

                    // JSON文字列をパース
                    let badges = [];
                    try {
                        badges = JSON.parse(badgesJson);
                    } catch (e) {
                        // パースに失敗した場合は空配列
                        badges = [];
                    }

                    if (badges && badges.length > 0) {
                        badges.forEach((badge, index) => {
                            const span = document.createElement('span');
                            span.innerText = badge;
                            span.style.color = '#0066cc';
                            span.style.cursor = 'pointer';
                            span.style.textDecoration = 'underline';
                            span.style.marginRight = '8px';
                            span.title = 'クリックしてこの戦型で絞り込み';

                            // クリックイベント
                            span.addEventListener('click', () => {
                                // クリックされたバッジを記録
                                params.data['clicked_badge'] = badge;
                                // 行を選択
                                params.node.setSelected(true, true);
                            });

                            this.eGui.appendChild(span);
                        });
                    }
                }
                getGui() {
                    return this.eGui;
                }
            }
            """)

            # 戦型リストと clicked_badge 列を非表示にする
            gb.configure_column("戦型リスト", hide=True)
            gb.configure_column("clicked_badge", hide=True)
            gb.configure_column("戦型", width=250, cellRenderer=badge_renderer)

            # URL列をリンクとして表示（JsCodeを使用）
            url_renderer = JsCode("""
            class UrlCellRenderer {
                init(params) {
                    this.eGui = document.createElement('a');
                    if (params.value) {
                        this.eGui.href = params.value;
                        this.eGui.target = '_blank';
                        this.eGui.innerText = '棋譜を見る';
                        this.eGui.style.color = '#0066cc';
                    }
                }
                getGui() {
                    return this.eGui;
                }
            }
            """)
            gb.configure_column("URL", headerName="棋譜", width=100, cellRenderer=url_renderer)

            # グリッドオプション
            gb.configure_pagination(enabled=False)
            gb.configure_side_bar()

            # 行選択を有効にする
            gb.configure_selection(selection_mode='single', use_checkbox=False, rowMultiSelectWithClick=False)

            gridOptions = gb.build()

            # AgGridで表示（キーを動的に変更して選択状態をリセット）
            grid_response = AgGrid(
                df_display,
                gridOptions=gridOptions,
                height=600,
                theme='streamlit',
                update_mode=GridUpdateMode.SELECTION_CHANGED,  # 選択変更時に更新
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                allow_unsafe_jscode=True,  # カスタムJavaScriptを許可
                enable_enterprise_modules=False,
                key=f"games_grid_{st.session_state.grid_key_counter}",  # 動的キーで選択をリセット
                custom_css={
                    "#gridToolBar": {"padding-bottom": "0px !important"}
                }
            )

            # 選択された行があれば、対戦相手または戦型でフィルタリング
            if grid_response['selected_rows'] is not None and len(grid_response['selected_rows']) > 0:
                selected_row = grid_response['selected_rows'].iloc[0]
                clicked_badge = selected_row.get('clicked_badge', '')

                # バッジがクリックされた場合は戦型フィルターを設定
                if clicked_badge:
                    current_badge_filter = st.session_state.get('selected_badge', None)

                    if current_badge_filter != clicked_badge:
                        # 戦型フィルターを更新
                        st.session_state.selected_badge = clicked_badge
                        # グリッドキーをインクリメントして選択状態をリセット
                        st.session_state.grid_key_counter += 1
                        st.rerun()
                else:
                    # 対戦相手がクリックされた場合
                    selected_opponent = selected_row['対戦相手']
                    current_opponent_filter = st.session_state.get('selected_opponent', None)

                    if current_opponent_filter != selected_opponent:
                        # 対戦相手フィルターを更新
                        st.session_state.selected_opponent = selected_opponent
                        # グリッドキーをインクリメントして選択状態をリセット
                        st.session_state.grid_key_counter += 1
                        st.rerun()
        else:
            st.warning("表示する対局がありません")

        # 読み込みログ（折りたたみ表示、初期状態は閉じる）
        with st.expander("📋 読み込みログ", expanded=False):
            if loaded_files:
                st.success(f"✅ {len(loaded_files)}個のファイルから{len(all_replays)}件の棋譜を読み込みました")
                if user_name:
                    st.info(f"**ユーザー:** {user_name}")
                st.markdown("**読み込んだファイル:**")
                for f in loaded_files:
                    st.text(f"  • {f}")
            else:
                st.warning("result/ディレクトリにJSONファイルがありません")
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
