# 将棋ウォーズ棋譜ツール

将棋ウォーズの対局履歴を取得・表示するツールです。

## 機能

1. **棋譜URLスクレイパー** (`shogiwars_scraper.py`)
   - 将棋ウォーズの対局履歴ページから棋譜URLを抽出してJSONファイルに保存
   - ログイン認証に対応

2. **棋譜ビューア** (`shogiwars_viewer.py`)
   - Streamlitを使用したWebアプリケーション
   - JSONファイルから対局データを読み込んで表示
   - フィルタリング、統計表示機能

## 必要要件

- Python 3.9以降（Python 3.13推奨）
- Google Chrome（ChromeDriverは自動的にインストールされます）

## インストール

Python 3.9以降では外部管理環境のため、仮想環境を使用します：

```bash
# 仮想環境を作成（Python 3.9以降が必要）
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# pipのアップグレード
pip install --upgrade pip

# パッケージをインストール
pip install -r requirements.txt
```

**注意:** macOSやローカル環境では`python3`コマンドが使用されますが、Python 3.9以降であることを確認してください：
```bash
python3 --version  # Python 3.9以降であることを確認
```

## 使い方

### ログイン認証の設定

このスクリプトは将棋ウォーズへのログインが必要です。認証情報は以下の2つの方法で設定できます：

#### 1. 環境変数を使用（推奨）

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
python shogiwars_scraper.py
```

#### 2. 対話的に入力

認証情報を指定せずに実行すると、プロンプトでユーザー名とパスワードの入力を求められます：

```bash
python shogiwars_scraper.py
```

### 基本的な使い方

```bash
# 仮想環境を使用している場合は先に有効化
source venv/bin/activate

# 環境変数を設定
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"

# スクリプトを実行
python shogiwars_scraper.py
```

デフォルトでは以下の設定で実行されます:
- ユーザーID: ログインユーザー（自動検出）
- 対戦相手: 未指定（全ての対局を取得）
- 対象月: 現在月（YYYY-MM形式で自動設定）
- ゲームタイプ: 無指定 (10分切れ負け)
- 出力ファイル: `result/game_replays_[gtype]_[month]_[user].json` 形式で自動生成

### パラメータ設定

#### 環境変数（認証情報と実行オプション）

**必須の環境変数:**
- `SHOGIWARS_USERNAME`: 将棋ウォーズのログインユーザー名
- `SHOGIWARS_PASSWORD`: 将棋ウォーズのログインパスワード

**オプションの環境変数:**
- `SHOGIWARS_HEADLESS`: ヘッドレスモードで実行（`true`/`false`、デフォルト: `false`）
- `SHOGIWARS_MANUAL_CAPTCHA`: CAPTCHAを手動で完了するモード（`true`/`false`、デフォルト: `false`）

#### コマンドライン引数（スクレイピングパラメータ）

スクレイピングパラメータはコマンドライン引数で指定します：

```bash
python shogiwars_scraper.py --gtype s1 --month 2024-10 --limit 100 --opponent "odakaho"
```

**利用可能な引数:**
- `--opponent`: 対戦相手のID（未指定の場合は全対局を取得）
- `--month`: 対象月（YYYY-MM形式、デフォルト: 現在月）
- `--gtype`: ゲームタイプ（`s1`=1手10秒、`sb`=3分切れ負け、未指定=10分切れ負け）
- `--limit`: 取得する最大ページ数（未指定の場合は全ページ）
- `--output`: 出力ファイル名（未指定の場合は自動生成）

**ファイル名の自動生成ルール:**
- デフォルトでは `result/` ディレクトリに保存されます
- 対戦相手未指定: `result/game_replays_[gtype]_[month]_[user].json`
  - 例: `result/game_replays_s1_2024-10_ohakado.json`
- 対戦相手指定: `result/game_replays_[gtype]_[month]_[user]_[opponent].json`
  - 例: `result/game_replays_s1_2024-10_ohakado_odakaho.json`

**注意:**
- ユーザーIDは、ログイン後に自動的に検出されます

## ディレクトリ構造

```
workspace2/crawler/
├── shogiwars_scraper.py      # 棋譜URLスクレイパー
├── shogiwars_viewer.py      # 棋譜ビューア（Streamlit）
├── requirements.txt
├── README.md
├── .gitignore
├── result/                  # JSONファイルの出力先
│   └── game_replays_*.json
└── tmp/                     # スクリーンショットなど一時ファイルの保存先
    └── login_*.png
```

## 出力形式

JSONファイルには以下の形式でデータが保存されます:

```json
{
  "params": {
    "user": "ohakado",
    "opponent": "(all)",
    "month": "2024-10",
    "gtype": "s1",
    "limit": 1
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
  - `user`: 検索対象ユーザーID
  - `opponent`: 対戦相手（未指定の場合は "(all)"）
  - `month`: 対象月
  - `gtype`: ゲームタイプ（未指定の場合は "10min"）
  - `limit`: 取得したページ数（全ページの場合は "(all)"）
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

### デフォルト設定で実行

認証情報のみ設定して実行（全対局、現在月、10分切れ負け）：

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
python shogiwars_scraper.py
# 出力: result/game_replays_10min_2025-11_ohakado.json
```

### 2024年10月の全対局を抽出（1手10秒）

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
python shogiwars_scraper.py --gtype s1 --month 2024-10
# 出力: result/game_replays_s1_2024-10_ohakado.json
```

### 最初の100ページだけ取得

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
python shogiwars_scraper.py --gtype s1 --limit 100
# 出力: result/game_replays_s1_2025-11_ohakado.json
```

### 特定の対戦相手との対局を抽出

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
python shogiwars_scraper.py --opponent "odakaho" --gtype s1
# 出力: result/game_replays_s1_2025-11_ohakado_odakaho.json
```

### すべての引数を指定

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
python shogiwars_scraper.py --gtype s1 --month 2024-10 --limit 100 --opponent "odakaho"
# 出力: result/game_replays_s1_2024-10_ohakado_odakaho.json
```

### カスタムファイル名を指定

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
python shogiwars_scraper.py --opponent "odakaho" --output my_games.json
# 出力: my_games.json (カレントディレクトリ)
```

### ヘッドレスモードで実行

ブラウザを表示せずに実行：

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
export SHOGIWARS_HEADLESS="true"
python shogiwars_scraper.py
```

### ブラウザを表示してデバッグ

ログインプロセスを確認したい場合は、`SHOGIWARS_HEADLESS` を設定せずに実行してください（デフォルトでブラウザが表示されます）：

```bash
export SHOGIWARS_USERNAME="your_username"
export SHOGIWARS_PASSWORD="your_password"
python shogiwars_scraper.py
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

### 利用目的と範囲

- **このツールは、自分自身の棋譜を個人で鑑賞する目的で作成されています**
- 将棋ウォーズのサーバに負荷をかけないよう、自分の対局履歴一覧ページのみをスクレイピングする設計となっています

### 改造に関する注意

⚠️ **以下のような改造を行った場合、将棋ウォーズのサーバに過度な負荷をかける可能性が高まります：**

- 他ユーザーを含めた大量の棋譜を取得する機能の追加
- リンク先の個別対局ページから詳細な情報を自動取得する機能の追加
- リクエスト間隔の短縮や並列化を行う改造

このような改造を行う場合は、サーバへの影響を十分に考慮し、責任を持って使用してください。

### 技術的な注意事項

- このスクリプトは認証が必要な対局履歴ページから情報を取得します
- 過度なアクセスはサーバーに負荷をかける可能性があるため、適切な間隔を空けて使用してください
- 将棋ウォーズのHTML構造が変更された場合、スクリプトの修正が必要になる可能性があります

---

## Webアプリケーション（棋譜ビューア）

スクレイピングで取得したJSONファイルを表示するWebアプリケーションです。

### 起動方法

```bash
# 仮想環境を有効化
source venv/bin/activate

# Streamlitアプリケーションを起動
streamlit run shogiwars_viewer.py
```

ブラウザで `http://localhost:8501` が自動的に開きます。

### 機能

1. **JSONファイルの自動読み込み**
   - `result/` ディレクトリ内のすべてのJSONファイルを自動的に読み込み
   - 複数ファイルの棋譜を統合して表示（重複は許容）
   - 最初のJSONファイルから自動的にユーザー名を取得

2. **対局一覧の表示**
   - 日時、手番、勝敗、対戦相手、段位、バッジを表形式で表示
   - 棋譜URLへのリンク

3. **フィルタリング機能**
   - 勝敗でフィルター（勝ち/負け/引き分け）
   - 対戦相手でフィルター
   - バッジでフィルター

4. **統計表示**
   - 総対局数
   - 勝率
   - 勝ち/負け/引き分けの件数

### スクリーンショット

アプリケーションを起動すると、以下のような画面が表示されます：

- サイドバー: JSONファイルの選択
- メインエリア: 検索パラメータ、対局一覧、統計情報

---

## Lightsail (Amazon Linux 2023) へのデプロイ

### 前提条件

- AWS Lightsailインスタンスが起動していること
- SSHでインスタンスにアクセスできること
- **注意**: Lightsail Distributionを使用する場合、ポート80はファイアウォールで閉じてください（Distribution経由のアクセスのみ許可）

### アーキテクチャ

```
[ユーザー]
    ↓ (HTTP/HTTPS)
[Lightsail Distribution (CDN)] ※オプション
    ↓ (HTTP:80)
[Nginx (リバースプロキシ)]
    ↓ (localhost:8501)
[Streamlit アプリケーション]
```

- **Nginx**: ポート80でリクエストを受け、Streamlitにプロキシ
- **Streamlit**: ポート8501で内部的に動作
- **Lightsail Distribution**: CDN、HTTPS、カスタムドメインを提供（オプション）

### デプロイスクリプトを使用する方法（推奨）

ローカル環境から`deploy.sh`スクリプトを使用すると、デプロイを自動化できます：

```bash
# スクリプトに実行権限を付与
chmod +x deploy.sh

# 初回デプロイ（SSH鍵のパスを指定）
./deploy.sh <your-lightsail-ip> ~/.ssh/lightsail_key.pem --setup

# コードの更新
./deploy.sh <your-lightsail-ip> ~/.ssh/lightsail_key.pem --update

# JSONファイルのアップロード
./deploy.sh <your-lightsail-ip> ~/.ssh/lightsail_key.pem --upload-json
```

**必要なもの:**
- LightsailのSSH鍵ファイル（`.pem`形式）
- SSH鍵ファイルの権限を正しく設定: `chmod 400 ~/.ssh/lightsail_key.pem`

**動作:**
- デプロイスクリプトはローカルのファイル（`shogiwars_viewer.py`、`requirements.txt`等）をサーバーに直接アップロードします
- Git pullは使用しないため、サーバー側でGitリポジトリを設定する必要はありません

### 手動デプロイ手順

デプロイスクリプトを使用しない場合は、以下の手順で手動デプロイできます：

#### 1. Lightsailインスタンスに接続

```bash
# SSH鍵を使用して接続
ssh -i ~/.ssh/lightsail_key.pem ec2-user@<your-lightsail-ip>
```

**注意:** SSH鍵ファイルの権限が正しく設定されている必要があります:
```bash
chmod 400 ~/.ssh/lightsail_key.pem
```

#### 2. 必要なパッケージをインストール

```bash
# システムパッケージの更新
sudo dnf update -y

# Python 3.13とNginxのインストール
sudo dnf install -y python3.13 python3.13-pip nginx

# 開発ツールのインストール（pyarrow等のビルドに必要）
sudo dnf groupinstall -y "Development Tools"
```

#### 3. アプリケーションディレクトリを作成

```bash
mkdir -p ~/my_shogiwars
cd ~/my_shogiwars
```

#### 4. ローカルからファイルをアップロード

ローカル端末で以下を実行してファイルをアップロード：

```bash
# 必要なファイルをアップロード
scp -i ~/.ssh/lightsail_key.pem requirements.txt ec2-user@<your-lightsail-ip>:~/my_shogiwars/
scp -i ~/.ssh/lightsail_key.pem shogiwars_viewer.py ec2-user@<your-lightsail-ip>:~/my_shogiwars/
scp -i ~/.ssh/lightsail_key.pem streamlit.service ec2-user@<your-lightsail-ip>:~/my_shogiwars/
scp -i ~/.ssh/lightsail_key.pem nginx-shogiwars.conf ec2-user@<your-lightsail-ip>:~/my_shogiwars/
```

#### 5. 仮想環境を作成してパッケージをインストール

```bash
# 仮想環境の作成（Python 3.13を使用）
python3.13 -m venv venv

# 仮想環境の有効化
source venv/bin/activate

# pipのアップグレード
pip install --upgrade pip

# パッケージのインストール
pip install -r requirements.txt
```

#### 6. resultディレクトリを作成してJSONファイルを配置

```bash
# サーバー側でresultディレクトリを作成
mkdir -p result

# ローカルからJSONファイルをアップロード（ローカル端末で実行）
scp -i ~/.ssh/lightsail_key.pem result/*.json ec2-user@<your-lightsail-ip>:~/my_shogiwars/result/
```

#### 7. Nginxを設定

```bash
# Nginx設定ファイルをコピー
sudo cp nginx-shogiwars.conf /etc/nginx/conf.d/

# 設定ファイルの構文チェック
sudo nginx -t

# Nginxを有効化して起動
sudo systemctl enable nginx
sudo systemctl start nginx

# Nginxの状態を確認
sudo systemctl status nginx
```

#### 8. systemdサービスを設定

```bash
# サービスファイルをsystemdディレクトリにコピー
sudo cp streamlit.service /etc/systemd/system/

# systemdの設定を再読み込み
sudo systemctl daemon-reload

# サービスを有効化（起動時に自動起動）
sudo systemctl enable streamlit

# サービスを開始
sudo systemctl start streamlit

# サービスの状態を確認
sudo systemctl status streamlit
```

#### 9. ファイアウォールの設定

**Lightsail Distributionを使用する場合:**
- ポート80は**開放しない**（ファイアウォールで閉じたまま）
- DistributionはAWS内部ネットワークを通じてインスタンスにアクセスします
- これにより、直接IPアクセスを防ぎ、Distribution経由のアクセスのみを許可できます

**Distributionを使用せず、直接アクセスする場合:**
- Lightsailコンソールのネットワーキングタブでポート80を開放
  - アプリケーション: HTTP
  - プロトコル: TCP
  - ポート: 80

#### 10. ブラウザでアクセス

**Distributionを使用しない場合:**
```
http://<your-lightsail-ip>
```

**Distributionを使用する場合:**
- 直接IPアクセスは不可（ファイアウォールで保護）
- Distribution経由でのみアクセス可能（後述の設定を参照）

### サービスの管理

```bash
# Streamlitサービスの管理
sudo systemctl status streamlit   # 状態確認
sudo systemctl stop streamlit      # 停止
sudo systemctl restart streamlit   # 再起動
sudo journalctl -u streamlit -f    # ログ確認

# Nginxサービスの管理
sudo systemctl status nginx        # 状態確認
sudo systemctl stop nginx          # 停止
sudo systemctl restart nginx       # 再起動
sudo systemctl reload nginx        # 設定リロード（接続を切らない）
sudo tail -f /var/log/nginx/shogiwars_access.log  # アクセスログ
sudo tail -f /var/log/nginx/shogiwars_error.log   # エラーログ
```

### 更新手順

コードを更新した場合は、デプロイスクリプトの`--update`モードを使用するのが最も簡単です：

```bash
# ローカル端末で実行
./deploy.sh <your-lightsail-ip> ~/.ssh/lightsail_key.pem --update
```

手動で更新する場合：

```bash
# ローカル端末でファイルをアップロード
scp -i ~/.ssh/lightsail_key.pem requirements.txt ec2-user@<your-lightsail-ip>:~/my_shogiwars/
scp -i ~/.ssh/lightsail_key.pem shogiwars_viewer.py ec2-user@<your-lightsail-ip>:~/my_shogiwars/
scp -i ~/.ssh/lightsail_key.pem nginx-shogiwars.conf ec2-user@<your-lightsail-ip>:~/my_shogiwars/

# サーバーで実行
ssh -i ~/.ssh/lightsail_key.pem ec2-user@<your-lightsail-ip>

cd ~/my_shogiwars
source venv/bin/activate
pip install -r requirements.txt

# Nginx設定を更新
sudo cp nginx-shogiwars.conf /etc/nginx/conf.d/
sudo nginx -t
sudo systemctl reload nginx

# Streamlitを再起動
sudo systemctl restart streamlit
```

### トラブルシューティング

#### ポート80にアクセスできない場合

1. Lightsailのファイアウォール設定を確認
   ```bash
   # Lightsailコンソールでポート80が開放されているか確認
   ```

2. Nginxが起動しているか確認
   ```bash
   sudo systemctl status nginx
   sudo ss -tlnp | grep :80
   ```

3. Nginx設定を確認
   ```bash
   sudo nginx -t
   sudo tail -f /var/log/nginx/shogiwars_error.log
   ```

#### Streamlitサービスが起動しない場合

```bash
# ログを確認
sudo journalctl -u streamlit -n 50

# 手動で実行してエラーを確認
cd ~/my_shogiwars
source venv/bin/activate
streamlit run shogiwars_viewer.py --server.port=8501 --server.address=0.0.0.0
```

#### 502 Bad Gateway エラーが出る場合

Nginxは動いているがStreamlitに接続できない状態です：

```bash
# Streamlitが動作しているか確認
sudo systemctl status streamlit
sudo ss -tlnp | grep 8501

# Streamlitを再起動
sudo systemctl restart streamlit
```

#### 直接IPアクセスとCloudFrontデフォルトドメインのリダイレクト

**方法1: ファイアウォールで完全にブロック（推奨）**

Lightsail Distributionを使用する場合、ファイアウォールでポート80を閉じてください。

```bash
# Lightsailコンソールで設定
# ネットワーキング → ファイアウォール
# ポート80のルールを削除（または追加しない）
```

これにより：
- 直接IPアクセス: `http://<ip>` → タイムアウト（接続できない）
- Distribution経由: `https://<distribution>` → 正常にアクセス可能

**方法2: Nginxでカスタムドメインにリダイレクト**

ポート80を開放した状態で、IPアドレスやCloudFrontデフォルトドメインでのアクセスを正規ドメインにリダイレクトできます。

`nginx-shogiwars.conf` には以下の設定が含まれています：
```nginx
# IPアドレスでのアクセス → https://ohakado.com/ にリダイレクト
if ($host ~* "^(\d+\.){3}\d+$") {
    return 301 https://ohakado.com$request_uri;
}

# CloudFrontデフォルトドメイン → https://ohakado.com/ にリダイレクト
if ($host = "d24bfdpv20ukl6.cloudfront.net") {
    return 301 https://ohakado.com$request_uri;
}
```

**注意**: CloudFrontドメインをカスタムドメインに変更する場合は、`nginx-shogiwars.conf` の17行目のドメイン名を変更してください。

### Lightsail Distribution（CDN）の設定

HTTPSとカスタムドメインを使用したい場合、Lightsail Distributionを設定します：

#### 重要: 直接IPアクセスの防止

Lightsail Distributionを使用する場合は、**インスタンスのファイアウォールでポート80を閉じてください**。

1. Lightsailコンソール → インスタンス → ネットワーキング → ファイアウォール
2. ポート80のルールを削除（または追加しない）
3. SSHポート（22）は開けたままにする

Lightsail DistributionはAWS内部ネットワーク経由でインスタンスにアクセスするため、パブリックにポート80を開放する必要はありません。

#### 1. Distributionの作成

Lightsailコンソールで：
1. **ネットワーキング** → **ディストリビューションを作成**
2. **オリジンを選択**: Lightsailインスタンスを選択
3. **オリジンプロトコルポリシー**: HTTP only
4. **デフォルトの動作**:
   - キャッシュ動作: Best for dynamic content
   - 許可される HTTP メソッド: GET, HEAD, OPTIONS, PUT, POST, PATCH, DELETE
5. **プランを選択**: 適切なプランを選択
6. **ディストリビューションを作成**

#### 2. カスタムドメインの設定（オプション）

1. Distributionの詳細ページで**カスタムドメイン**タブを開く
2. **証明書を作成**をクリック
3. ドメイン名を入力（例: `shogiwars.example.com`）
4. DNS検証用のCNAMEレコードを追加
5. 証明書が検証されたら、カスタムドメインを有効化
6. DNSでCNAMEレコードを追加（カスタムドメイン → Distributionドメイン）

#### 3. アクセス

- **Distribution経由**: `https://<distribution-domain>`
- **カスタムドメイン**: `https://shogiwars.example.com`
- **直接IPアクセス**: `http://<lightsail-ip>` → 接続タイムアウト（ファイアウォールでブロック）

**注意**:
- Distributionはキャッシュを行うため、更新が反映されるまで数分かかる場合があります
- キャッシュをクリアしたい場合は、Distributionの詳細ページで**すべてのキャッシュをクリア**を実行してください
- ファイアウォールでポート80を閉じることで、直接IPアクセスを防ぎ、Distribution経由のアクセスのみを許可します

#### 4. セキュリティの確認

ファイアウォール設定が正しく機能しているか確認：

```bash
# 直接IPアクセス（タイムアウトするはず）
curl -I --max-time 10 http://<your-lightsail-ip>
# → curl: (28) Connection timed out

# Distribution経由（200 OKが返るはず）
curl -I https://<distribution-domain>
# → HTTP/2 200
```
