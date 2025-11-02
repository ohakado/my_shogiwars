#!/bin/bash
# デプロイスクリプト for Lightsail Amazon Linux 2023

set -e

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 使い方を表示
usage() {
    echo "使い方: $0 <lightsail-ip> <ssh-key-path> [options]"
    echo ""
    echo "引数:"
    echo "  lightsail-ip   LightsailインスタンスのIPアドレス"
    echo "  ssh-key-path   SSH鍵ファイルのパス（例: ~/.ssh/lightsail_key.pem）"
    echo ""
    echo "オプション:"
    echo "  --setup       初回セットアップ（パッケージのインストール等）"
    echo "  --update      コードの更新のみ（git pull & restart）"
    echo "  --upload-json ローカルのresult/*.jsonをアップロード"
    echo ""
    echo "例:"
    echo "  $0 13.123.45.67 ~/.ssh/lightsail_key.pem --setup         # 初回デプロイ"
    echo "  $0 13.123.45.67 ~/.ssh/lightsail_key.pem --update        # コード更新"
    echo "  $0 13.123.45.67 ~/.ssh/lightsail_key.pem --upload-json   # JSONファイルのアップロード"
    exit 1
}

# 引数チェック
if [ $# -lt 3 ]; then
    usage
fi

LIGHTSAIL_IP=$1
SSH_KEY=$2
MODE=$3
SSH_USER="ec2-user"
APP_DIR="my_shogiwars"

# SSH鍵ファイルの存在チェック
if [ ! -f "$SSH_KEY" ]; then
    echo -e "${RED}エラー: SSH鍵ファイルが見つかりません: ${SSH_KEY}${NC}"
    exit 1
fi

# SSH/SCPコマンドのオプション
SSH_OPTS="-i ${SSH_KEY} -o StrictHostKeyChecking=no"

echo -e "${GREEN}=== Lightsail デプロイスクリプト ===${NC}"
echo -e "対象サーバー: ${YELLOW}${SSH_USER}@${LIGHTSAIL_IP}${NC}"
echo ""

# 初回セットアップ
if [ "$MODE" == "--setup" ]; then
    echo -e "${GREEN}[1/8] システムパッケージの更新...${NC}"
    ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} "sudo dnf update -y"

    echo -e "${GREEN}[2/8] 必要なパッケージのインストール...${NC}"
    ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} "sudo dnf install -y python3.13 python3.13-pip nginx && sudo dnf groupinstall -y 'Development Tools'"

    echo -e "${GREEN}[3/8] アプリケーションコードのアップロード...${NC}"
    echo -e "${YELLOW}ローカルのファイルをサーバーにアップロードします${NC}"

    # ディレクトリの作成
    ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} "mkdir -p ~/${APP_DIR}"

    # 必要なファイルをアップロード
    echo "  - requirements.txt をアップロード中..."
    scp ${SSH_OPTS} requirements.txt ${SSH_USER}@${LIGHTSAIL_IP}:~/${APP_DIR}/

    echo "  - shogiwars_viewer.py をアップロード中..."
    scp ${SSH_OPTS} shogiwars_viewer.py ${SSH_USER}@${LIGHTSAIL_IP}:~/${APP_DIR}/

    echo "  - streamlit.service をアップロード中..."
    scp ${SSH_OPTS} streamlit.service ${SSH_USER}@${LIGHTSAIL_IP}:~/${APP_DIR}/

    echo "  - nginx-shogiwars.conf をアップロード中..."
    scp ${SSH_OPTS} nginx-shogiwars.conf ${SSH_USER}@${LIGHTSAIL_IP}:~/${APP_DIR}/

    echo -e "${GREEN}[4/8] 仮想環境の作成とパッケージインストール...${NC}"
    ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} "cd ~/${APP_DIR} && python3.13 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

    echo -e "${GREEN}[5/8] resultディレクトリの作成...${NC}"
    ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} "mkdir -p ~/${APP_DIR}/result"

    echo -e "${GREEN}[6/8] Nginxの設定...${NC}"
    ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} "cd ~/${APP_DIR} && sudo cp nginx-shogiwars.conf /etc/nginx/conf.d/ && sudo nginx -t && sudo systemctl enable nginx && sudo systemctl start nginx"

    echo -e "${GREEN}[7/8] systemdサービスの設定...${NC}"
    ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} "cd ~/${APP_DIR} && sudo cp streamlit.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable streamlit && sudo systemctl start streamlit"

    echo -e "${GREEN}[8/8] サービスの状態確認...${NC}"
    ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} "sudo systemctl status streamlit --no-pager && sudo systemctl status nginx --no-pager"

    echo ""
    echo -e "${GREEN}✅ セットアップが完了しました！${NC}"
    echo ""
    echo -e "${YELLOW}次のステップ:${NC}"
    echo ""
    echo -e "【Lightsail Distributionを使用する場合（推奨）】"
    echo -e "  1. Lightsailコンソールでポート80を開放しない（閉じたまま）"
    echo -e "  2. Lightsail Distributionを作成してインスタンスをオリジンとして設定"
    echo -e "  3. Distribution経由でアクセス: https://<distribution-domain>"
    echo -e "  → 直接IPアクセスは不可（ファイアウォールで保護）"
    echo ""
    echo -e "【直接IPアクセスする場合】"
    echo -e "  1. Lightsailコンソールでポート80（HTTP）を開放"
    echo -e "  2. ブラウザでアクセス: ${YELLOW}http://${LIGHTSAIL_IP}${NC}"
    echo -e "  → セキュリティ上、Distributionの使用を推奨します"

# コード更新
elif [ "$MODE" == "--update" ]; then
    echo -e "${GREEN}[1/5] アプリケーションコードのアップロード...${NC}"

    echo "  - requirements.txt をアップロード中..."
    scp ${SSH_OPTS} requirements.txt ${SSH_USER}@${LIGHTSAIL_IP}:~/${APP_DIR}/

    echo "  - shogiwars_viewer.py をアップロード中..."
    scp ${SSH_OPTS} shogiwars_viewer.py ${SSH_USER}@${LIGHTSAIL_IP}:~/${APP_DIR}/

    echo "  - streamlit.service をアップロード中..."
    scp ${SSH_OPTS} streamlit.service ${SSH_USER}@${LIGHTSAIL_IP}:~/${APP_DIR}/

    echo "  - nginx-shogiwars.conf をアップロード中..."
    scp ${SSH_OPTS} nginx-shogiwars.conf ${SSH_USER}@${LIGHTSAIL_IP}:~/${APP_DIR}/

    echo -e "${GREEN}[2/5] パッケージの更新...${NC}"
    ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} "cd ~/${APP_DIR} && source venv/bin/activate && pip install -r requirements.txt"

    echo -e "${GREEN}[3/5] Nginx設定の更新...${NC}"
    ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} "cd ~/${APP_DIR} && sudo cp nginx-shogiwars.conf /etc/nginx/conf.d/ && sudo nginx -t && sudo systemctl reload nginx"

    echo -e "${GREEN}[4/5] Streamlitサービスの再起動...${NC}"
    ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} "sudo systemctl restart streamlit"

    echo -e "${GREEN}[5/5] サービスの状態確認...${NC}"
    ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} "sudo systemctl status streamlit --no-pager && sudo systemctl status nginx --no-pager"

    echo ""
    echo -e "${GREEN}✅ 更新が完了しました！${NC}"
    echo -e "ブラウザで ${YELLOW}http://${LIGHTSAIL_IP}${NC} にアクセスしてください"

# JSONファイルのアップロード
elif [ "$MODE" == "--upload-json" ]; then
    if [ ! -d "result" ] || [ -z "$(ls -A result/*.json 2>/dev/null)" ]; then
        echo -e "${RED}エラー: result/ ディレクトリにJSONファイルがありません${NC}"
        exit 1
    fi

    echo -e "${GREEN}JSONファイルをアップロード中...${NC}"
    scp ${SSH_OPTS} result/*.json ${SSH_USER}@${LIGHTSAIL_IP}:~/${APP_DIR}/result/

    echo -e "${GREEN}サービスを再起動中...${NC}"
    ssh ${SSH_OPTS} ${SSH_USER}@${LIGHTSAIL_IP} "sudo systemctl restart streamlit"

    echo ""
    echo -e "${GREEN}✅ JSONファイルのアップロードが完了しました！${NC}"

else
    echo -e "${RED}エラー: 不明なオプション: ${MODE}${NC}"
    usage
fi
