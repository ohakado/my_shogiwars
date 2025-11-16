#!/bin/bash
# Google Analytics修正をサーバーにデプロイするスクリプト
# 使い方: ./deploy_ga_fix.sh <lightsail-ip> <ssh-key-path>

set -e

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 使い方を表示
usage() {
    echo "使い方: $0 <lightsail-ip> <ssh-key-path>"
    echo ""
    echo "引数:"
    echo "  lightsail-ip   LightsailインスタンスのIPアドレス"
    echo "  ssh-key-path   SSH鍵ファイルのパス（例: ~/.ssh/lightsail_key.pem）"
    echo ""
    echo "例:"
    echo "  $0 13.123.45.67 ~/.ssh/lightsail_key.pem"
    exit 1
}

# 引数チェック
if [ $# -lt 2 ]; then
    usage
fi

LIGHTSAIL_IP=$1
SSH_KEY=$2
SSH_USER="ec2-user"
APP_DIR="my_shogiwars"

# SSH鍵ファイルの存在チェック
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}エラー: SSH鍵ファイルが見つかりません: ${SSH_KEY}${NC}"
    exit 1
fi

# SSH/SCPコマンドのオプション
SSH_OPTS="-i ${SSH_KEY} -o StrictHostKeyChecking=no"
SERVER="${SSH_USER}@${LIGHTSAIL_IP}"

echo -e "${GREEN}========================================"
echo -e "Google Analytics修正をデプロイ中..."
echo -e "サーバー: ${YELLOW}${SERVER}${NC}"
echo -e "========================================${NC}"
echo ""

# 変更されたファイルをサーバーにコピー
echo -e "${GREEN}[1/6] ファイルをアップロード中...${NC}"
scp ${SSH_OPTS} inject_ga.py start_streamlit.sh shogiwars_viewer.py streamlit.service README_GA.md ${SSH_USER}@${LIGHTSAIL_IP}:~/${APP_DIR}/

echo ""
echo -e "${GREEN}[2/6] サーバーに接続してセットアップ中...${NC}"

# サーバー上でサービスを更新して再起動
ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} << 'ENDSSH'
set -e

cd /home/ec2-user/my_shogiwars

echo "[3/6] 実行権限を付与..."
chmod +x inject_ga.py start_streamlit.sh

echo "[4/6] サービスファイルを更新..."
sudo cp streamlit.service /etc/systemd/system/

echo "[5/6] systemdをリロードしてサービスを再起動..."
sudo systemctl daemon-reload
sudo systemctl restart streamlit

# 少し待機
sleep 3

echo ""
echo "[6/6] ステータスを確認..."
sudo systemctl status streamlit --no-pager -l

echo ""
echo "========================================"
echo "ログファイルを確認..."
echo "========================================"
if [ -f /home/ec2-user/my_shogiwars/ga_inject.log ]; then
    echo ""
    echo "=== ga_inject.log の内容 ==="
    tail -20 /home/ec2-user/my_shogiwars/ga_inject.log
else
    echo "⚠ ga_inject.log がまだ作成されていません"
fi

echo ""
echo "========================================"
echo "最近のjournalログ..."
echo "========================================"
sudo journalctl -u streamlit -n 20 --no-pager

ENDSSH

echo ""
echo "========================================"
echo "✓ デプロイ完了！"
echo "========================================"
echo ""
echo "【動作確認手順】"
echo ""
echo "1. ブラウザで https://ohakado.com/ にアクセス"
echo "2. 開発者ツールを開く（F12キー）"
echo "3. Networkタブで 'gtag/js?id=G-ZQ4CEPL2PK' がロードされているか確認"
echo "4. Elementsタブで <head> 内にGoogleタグスクリプトがあるか確認"
echo "5. Consoleタブで 'window.dataLayer' と入力して undefined でないか確認"
echo ""
echo "【Google Analytics確認】"
echo "1. Google Analyticsにログイン"
echo "2. プロパティ「G-ZQ4CEPL2PK」を選択"
echo "3. 左メニューから「リアルタイム」を選択"
echo "4. サイトにアクセスしてアクティブユーザーが表示されるか確認（1-2分待機）"
echo ""
echo "【うまくいかない場合】"
echo "README_GA.md を確認してください"
echo ""
echo "Nginxを使った代替方法も用意しています："
echo "詳細は README_GA.md の「方法2」を参照してください"
echo "========================================"
