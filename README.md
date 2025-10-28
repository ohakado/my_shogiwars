# 将棋ウォーズ棋譜URLスクレイパー

将棋ウォーズの対局履歴ページから特定の対戦相手との棋譜URLを抽出してJSONファイルに保存するスクリプトです。

## インストール

```bash
pip install -r requirements.txt
```

## 使い方

### 基本的な使い方

```bash
python scrape_shogiwars.py
```

デフォルトでは以下の設定で実行されます:
- ユーザーID: `UtadaHikaru`
- 対戦相手: `Walk_Wikipedia`
- 対象月: 現在月（YYYY-MM形式で自動設定）
- ゲームタイプ: 無指定 (10分切れ負け)
- 出力ファイル: `game_replays.json`

### オプション指定

```bash
python scrape_shogiwars.py \
  --user-id your_user_id \
  --opponent opponent_id \
  --month 2025-10 \
  --gtype s1 \
  --output my_games.json
```

### パラメータ

- `--user-id`: あなたのユーザーID
- `--opponent`: 対戦相手のID
- `--month`: 対象月（YYYY-MM形式）
- `--gtype`: ゲームタイプ
  - 無指定: 10分切れ負け（デフォルト）
  - `s1`: 1手10秒
  - `sb`: 3分切れ負け
- `--max-pages`: 取得する最大ページ数（デフォルト: 全ページ）
- `--output`: 出力JSONファイル名

## 出力形式

JSONファイルには以下の形式でデータが保存されます:

```json
[
  {
    "url": "https://shogiwars.heroz.jp/games/UtadaHikaru-Walk_Wikipedia-20251028_220236",
    "game_id": "UtadaHikaru-Walk_Wikipedia-20251028_220236",
    "context": "対局の追加情報（あれば）"
  }
]
```

## 例

2025年10月の対局を全ページ抽出:

```bash
python scrape_shogiwars.py --month 2025-10
```

最初の3ページだけ取得:

```bash
python scrape_shogiwars.py --max-pages 3
```

別の対戦相手の対局を抽出:

```bash
python scrape_shogiwars.py --opponent other_player --output other_games.json
```

## 注意事項

- このスクリプトは公開されている対局履歴ページから情報を取得します
- 過度なアクセスはサーバーに負荷をかける可能性があるため、適切な間隔を空けて使用してください
- 将棋ウォーズのHTML構造が変更された場合、スクリプトの修正が必要になる可能性があります
