# 変更履歴

## 2025-11-02

### 新機能: Streamlit Webアプリケーション
- JSONファイルから棋譜データを表示するWebアプリケーションを追加
- ファイル: `app.py`
- 主な機能:
  - `result/`ディレクトリ内のJSONファイル選択、またはファイルアップロード
  - 対局一覧の表形式表示（日時、手番、勝敗、対戦相手、段位、バッジ）
  - クリック可能な棋譜URLリンク
  - フィルタリング機能（勝敗/対戦相手/バッジ）
  - 統計表示（総対局数、勝率、勝ち/負け/引き分けの件数）

### スクレイパーの改善
- パラメータ名の変更: `user_id` → `user`, `max_pages` → `limit`
- コマンドライン引数のサポート:
  - `--opponent`: 対戦相手のID
  - `--month`: 対象月（YYYY-MM形式）
  - `--gtype`: ゲームタイプ（s1/sb）
  - `--limit`: 取得する最大ページ数
  - `--output`: 出力ファイル名
- 環境変数は認証情報のみに限定（`SHOGIWARS_USERNAME`, `SHOGIWARS_PASSWORD`）

### ドキュメントの改善
- README.mdの構成を改善:
  - タイトルを「将棋ウォーズ棋譜ツール」に変更
  - 機能セクションを追加（スクレイパーとビューアの両方を説明）
  - Webアプリケーションのセクションを追加
- 注意事項の整理:
  - 利用目的と範囲を明確化
  - 改造に関する注意を追加
  - 個人名を作者のアカウント名に変更
  - 不要な記述を削除（商用利用、環境変数管理の推奨など）

### 技術的な改善
- Python 3.14対応:
  - pyarrowのビルド問題を回避（HTMLテーブル表示を使用）
  - requirements.txtにStreamlitとpandasを追加
- .gitignoreに`.streamlit/`ディレクトリを追加

### 使用方法

#### スクレイパー
```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
python scrape_shogiwars.py --gtype s1 --month 2024-10 --limit 100 --opponent "odakaho"
```

#### Webアプリケーション
```bash
source venv/bin/activate
streamlit run app.py
```

ブラウザで `http://localhost:8501` が開きます。

### コミット履歴
- Remove command-line arguments, use environment variables only
- Rename parameters: user_id → user, max_pages → limit
- Remove environment variables for scraping parameters
- Replace personal name in README examples with author's account
- Add command-line arguments for scraping parameters
- Update README notes section with usage purpose and cautions
- Remove commercial use mention from README notes
- Update caution wording about bulk game fetching
- Update caution wording about fetching from individual game pages
- Update caution to include parallel requests
- Remove environment variable security note
- Add Streamlit web application for game replay viewer
- Fix pyarrow dependency issue by using HTML table display
- Fix HTML table rendering issue
