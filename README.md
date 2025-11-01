# 将棋ウォーズ棋譜URLスクレイパー

将棋ウォーズの対局履歴ページから特定の対戦相手との棋譜URLを抽出してJSONファイルに保存するスクリプトです。

**ログイン認証に対応しています。**

## 必要要件

- Python 3.14以降
- Google Chrome（ChromeDriverは自動的にインストールされます）

## インストール

Python 3.14以降では外部管理環境のため、仮想環境を使用します：

```bash
# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# パッケージをインストール
pip install -r requirements.txt
```

## 使い方

### ログイン認証の設定

このスクリプトは将棋ウォーズへのログインが必要です。認証情報は以下の2つの方法で設定できます：

#### 1. 環境変数を使用（推奨）

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
python scrape_shogiwars.py
```

#### 2. 対話的に入力

認証情報を指定せずに実行すると、プロンプトでユーザー名とパスワードの入力を求められます：

```bash
python scrape_shogiwars.py
```

### 基本的な使い方

```bash
# 仮想環境を使用している場合は先に有効化
source venv/bin/activate

# 環境変数を設定
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"

# スクリプトを実行
python scrape_shogiwars.py
```

デフォルトでは以下の設定で実行されます:
- ユーザーID: ログインユーザー（自動検出）
- 対戦相手: 未指定（全ての対局を取得）
- 対象月: 現在月（YYYY-MM形式で自動設定）
- ゲームタイプ: 無指定 (10分切れ負け)
- 出力ファイル: `result/game_replays_[gtype]_[month]_[user_id].json` 形式で自動生成

### 環境変数での設定

すべての設定は環境変数で行います。

#### 必須の環境変数
- `SHOGIWARS_USERNAME`: 将棋ウォーズのログインユーザー名
- `SHOGIWARS_PASSWORD`: 将棋ウォーズのログインパスワード

#### オプションの環境変数
- `SHOGIWARS_OPPONENT`: 対戦相手のID（デフォルト: ""=全ての対局を取得）
- `SHOGIWARS_MONTH`: 対象月（YYYY-MM形式、デフォルト: 現在月）
- `SHOGIWARS_GTYPE`: ゲームタイプ（デフォルト: 未指定=10分切れ負け）
  - 未指定: 10分切れ負け
  - `s1`: 1手10秒
  - `sb`: 3分切れ負け
- `SHOGIWARS_MAX_PAGES`: 取得する最大ページ数（デフォルト: 全ページ）
- `SHOGIWARS_OUTPUT`: 出力JSONファイル名（デフォルト: 自動生成）
- `SHOGIWARS_HEADLESS`: ヘッドレスモードで実行（`true`/`false`、デフォルト: `false`）
- `SHOGIWARS_MANUAL_CAPTCHA`: CAPTCHAを手動で完了するモード（`true`/`false`、デフォルト: `false`）

**ファイル名の自動生成ルール**:
- デフォルトでは `result/` ディレクトリに保存されます
- 対戦相手未指定: `result/game_replays_[gtype]_[month]_[user_id].json`
  - 例: `result/game_replays_s1_2024-10_ohakado.json`
- 対戦相手指定: `result/game_replays_[gtype]_[month]_[user_id]_[opponent].json`
  - 例: `result/game_replays_s1_2024-10_ohakado_Walprgis.json`

**注意**:
- ユーザーIDは、ログイン後に自動的に検出されます

## ディレクトリ構造

```
workspace2/crawler/
├── scrape_shogiwars.py
├── requirements.txt
├── README.md
├── .gitignore
├── result/          # JSONファイルの出力先
│   └── game_replays_*.json
└── tmp/             # スクリーンショットなど一時ファイルの保存先
    └── login_*.png
```

## 出力形式

JSONファイルには以下の形式でデータが保存されます:

```json
{
  "params": {
    "user_id": "ohakado",
    "opponent": "(all)",
    "month": "2024-10",
    "gtype": "s1",
    "max_pages": 1
  },
  "replays": [
    {
      "url": "https://shogiwars.heroz.jp/games/ohakado-Crazystone-20241031_232343?locale=ja",
      "game_id": "ohakado-Crazystone-20241031_232343",
      "sente": {
        "name": "ohakado",
        "class": "五段",
        "result": "win"
      },
      "gote": {
        "name": "Crazystone",
        "class": "四段",
        "result": "lose"
      },
      "datetime": "2024-10-31T23:23:43",
      "badges": ["#角換わり", "#角換わり棒銀"]
    },
    {
      "url": "https://shogiwars.heroz.jp/games/saitouraizi-ohakado-20241031_232003?locale=ja",
      "game_id": "saitouraizi-ohakado-20241031_232003",
      "sente": {
        "name": "saitouraizi",
        "class": "六段",
        "result": "lose"
      },
      "gote": {
        "name": "ohakado",
        "class": "五段",
        "result": "win"
      },
      "datetime": "2024-10-31T23:20:03",
      "badges": []
    }
  ]
}
```

- `params`: 検索に使用したパラメータ
  - `user_id`: 検索対象ユーザーID
  - `opponent`: 対戦相手（未指定の場合は "(all)"）
  - `month`: 対象月
  - `gtype`: ゲームタイプ（未指定の場合は "10min"）
  - `max_pages`: 取得したページ数（全ページの場合は "(all)"）
- `replays`: 棋譜URLのリスト
  - `url`: 棋譜ページのURL（クエリパラメータ付き）
  - `game_id`: 対局ID（クエリパラメータなし）
  - `sente`: 先手プレイヤー情報（オブジェクト）
    - `name`: 先手プレイヤーのユーザーID
    - `class`: 先手プレイヤーの段位（例: "五段"）
    - `result`: 先手プレイヤーの勝敗結果（`"win"`: 勝ち、`"lose"`: 負け、`"draw"`: 引き分け）
  - `gote`: 後手プレイヤー情報（オブジェクト）
    - `name`: 後手プレイヤーのユーザーID
    - `class`: 後手プレイヤーの段位（例: "四段"）
    - `result`: 後手プレイヤーの勝敗結果（`"win"`: 勝ち、`"lose"`: 負け、`"draw"`: 引き分け）
  - `datetime`: 対局日時（ISO 8601形式、日本時間）
  - `badges`: 棋譜に付けられたバッジのリスト（例: `["#角換わり", "#船囲い"]`）

## 使用例

### ヘッドレスモードで実行

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
export SHOGIWARS_HEADLESS="true"
python scrape_shogiwars.py
# 出力: result/game_replays_10min_2025-11_ohakado.json
```

### 2024年10月の全対局を抽出（1手10秒）

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
export SHOGIWARS_MONTH="2024-10"
export SHOGIWARS_GTYPE="s1"
python scrape_shogiwars.py
# 出力: result/game_replays_s1_2024-10_ohakado.json
```

### 最初の3ページだけ取得

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
export SHOGIWARS_MAX_PAGES="3"
export SHOGIWARS_GTYPE="s1"
python scrape_shogiwars.py
# 出力: result/game_replays_s1_2025-11_ohakado.json
```

### 特定の対戦相手との対局を抽出

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
export SHOGIWARS_OPPONENT="Walprgis"
export SHOGIWARS_GTYPE="s1"
python scrape_shogiwars.py
# 出力: result/game_replays_s1_2025-11_ohakado_Walprgis.json
```

### カスタムファイル名を指定

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
export SHOGIWARS_OPPONENT="Walprgis"
export SHOGIWARS_OUTPUT="my_games.json"
python scrape_shogiwars.py
# 出力: my_games.json (カレントディレクトリ)
```

### ブラウザを表示してデバッグ

ログインプロセスを確認したい場合は、`SHOGIWARS_HEADLESS` を設定せずに実行してください（デフォルトでブラウザが表示されます）：

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
python scrape_shogiwars.py
```

## トラブルシューティング

### ChromeDriverが見つからない

Seleniumは自動的にChromeDriverをダウンロードしようとしますが、うまくいかない場合は手動でインストールしてください：

```bash
pip install webdriver-manager
```

### ログインに失敗する

1. ユーザー名とパスワードが正しいか確認してください
2. ブラウザを表示して確認：`SHOGIWARS_HEADLESS` を設定せずに実行（デフォルトでブラウザが表示されます）
3. 将棋ウォーズのログインページの構造が変更されている可能性があります。その場合は `login_to_shogiwars` 関数を更新する必要があります

### ページが見つからない

将棋ウォーズのHTML構造が変更された場合、スクリプトの修正が必要になる可能性があります。

## 注意事項

- このスクリプトは認証が必要な対局履歴ページから情報を取得します
- 過度なアクセスはサーバーに負荷をかける可能性があるため、適切な間隔を空けて使用してください
- 将棋ウォーズのHTML構造が変更された場合、スクリプトの修正が必要になる可能性があります
- ログイン情報は環境変数で管理することをお勧めします（セキュリティのため）
- このツールは個人的な利用を想定しています。商用利用や過度な負荷をかける使い方は避けてください
