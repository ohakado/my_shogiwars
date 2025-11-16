# Google Analytics設定ガイド

## 問題の原因

Streamlitの`components.html()`はiframe内で実行されるため、ページ全体のGoogle Analyticsトラッキングができません。

## 解決策

2つの方法を用意しました：

### 方法1: 起動スクリプトでindex.htmlを書き換える（推奨）

この方法は、Streamlit起動前にindex.htmlに直接GAコードを注入します。

**メリット:**
- Nginxの設定変更不要
- シンプルな実装

**デメリット:**
- Streamlitアップデート時に再注入が必要
- 書き込み権限が必要

**デプロイ手順:**

```bash
# 1. ファイルをサーバーにアップロード
scp inject_ga.py start_streamlit.sh streamlit.service ec2-user@your-server:/home/ec2-user/my_shogiwars/

# 2. サーバーに接続
ssh ec2-user@your-server

# 3. 権限設定
cd /home/ec2-user/my_shogiwars
chmod +x inject_ga.py start_streamlit.sh

# 4. サービス更新
sudo cp streamlit.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart streamlit

# 5. ログ確認
cat /home/ec2-user/my_shogiwars/ga_inject.log
sudo journalctl -u streamlit -n 50
```

### 方法2: Nginxでレスポンスを書き換える（最も確実）

この方法は、NginxのSub Filterモジュールを使ってHTMLレスポンスにGAコードを注入します。

**メリット:**
- 最も確実に動作
- Streamlitアップデートの影響を受けない
- index.htmlへの書き込み権限不要

**デメリット:**
- Nginxの設定が必要
- Nginxを経由する必要がある

**デプロイ手順:**

```bash
# 1. Nginxがインストールされているか確認
nginx -v

# 2. sub_filterモジュールが有効か確認
nginx -V 2>&1 | grep -o with-http_sub_module

# 3. 設定ファイルをアップロード
scp nginx_ga_inject.conf ec2-user@your-server:/tmp/

# 4. サーバーに接続
ssh ec2-user@your-server

# 5. 既存のNginx設定を確認
sudo ls -la /etc/nginx/conf.d/
sudo cat /etc/nginx/nginx.conf

# 6. 設定ファイルを配置（既存の設定に合わせて編集）
sudo cp /tmp/nginx_ga_inject.conf /etc/nginx/conf.d/ohakado.conf

# 7. SSL証明書のパスを確認して設定ファイルを編集
sudo nano /etc/nginx/conf.d/ohakado.conf

# 8. 設定をテスト
sudo nginx -t

# 9. Nginxを再起動
sudo systemctl restart nginx

# 10. 確認
sudo systemctl status nginx
```

## 動作確認

### 1. ブラウザで確認

1. https://ohakado.com/ にアクセス
2. 開発者ツールを開く（F12）
3. **Networkタブ**:
   - `gtag/js?id=G-ZQ4CEPL2PK` がロードされているか確認
   - ステータスが200 OKか確認
4. **Consoleタブ**:
   - エラーがないか確認
   - `window.dataLayer` がundefinedでないか確認（Console で `window.dataLayer` と入力）
5. **Elementsタブ**:
   - `<head>` 内にGoogleタグスクリプトがあるか確認

### 2. Google Analytics リアルタイムレポート

1. Google Analyticsにログイン
2. プロパティ「G-ZQ4CEPL2PK」を選択
3. 左メニューから「リアルタイム」を選択
4. サイトにアクセスしてアクティブユーザーが表示されるか確認（通常1-2分で反映）

### 3. Google Tag Assistant（Chrome拡張機能）

1. [Google Tag Assistant](https://chrome.google.com/webstore/detail/tag-assistant-legacy-by-g/kejbdjndbnbjgmefkgdddjlbokphdefk) をインストール
2. サイトにアクセスしてTag Assistantアイコンをクリック
3. Google Analytics タグが検出されているか確認

## トラブルシューティング

### GAコードが注入されていない場合

**方法1の場合:**
```bash
# ログを確認
cat /home/ec2-user/my_shogiwars/ga_inject.log

# サービスログを確認
sudo journalctl -u streamlit -n 100

# 手動でスクリプトを実行して確認
cd /home/ec2-user/my_shogiwars
export GA_MEASUREMENT_ID="G-ZQ4CEPL2PK"
./venv/bin/python inject_ga.py
```

**方法2の場合:**
```bash
# Nginxのエラーログを確認
sudo tail -f /var/log/nginx/error.log

# sub_filterが効いているか確認
curl -s https://ohakado.com/ | grep "gtag"
```

### リアルタイムレポートにデータが表示されない場合

1. **キャッシュをクリア**: ブラウザのキャッシュとCookieをクリア
2. **シークレットモードで確認**: プライベートウィンドウで確認
3. **広告ブロッカーを無効化**: 広告ブロック拡張機能を無効化
4. **測定IDを確認**: Google Analyticsで正しい測定IDか確認
5. **データストリームを確認**: GA4のデータストリームが有効か確認

## 既知の問題

- **Streamlitの動的読み込み**: Streamlitは一部のコンテンツを動的に読み込むため、初回ページビューのみカウントされ、アプリ内遷移はカウントされない可能性があります
- **WebSocketによる通信**: Streamlitの大部分の通信はWebSocketで行われるため、通常のページビューとは異なる動作をします

## 推奨設定

より詳細なトラッキングが必要な場合は、GA4のイベントトラッキングを追加することをお勧めします：

```javascript
// カスタムイベントの例
gtag('event', 'button_click', {
  'event_category': 'engagement',
  'event_label': '対戦相手選択'
});
```

Streamlitのコールバック関数内でJavaScriptを実行してイベントを送信できます。
