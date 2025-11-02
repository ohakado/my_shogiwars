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
    echo "使い方: $0 <lightsail-ip> [options]"
    echo ""
    echo "オプション:"
    echo "  --setup       初回セットアップ（パッケージのインストール等）"
    echo "  --update      コードの更新のみ（git pull & restart）"
    echo "  --upload-json ローカルのresult/*.jsonをアップロード"
    echo ""
    echo "例:"
    echo "  $0 13.123.45.67 --setup         # 初回デプロイ"
    echo "  $0 13.123.45.67 --update        # コード更新"
    echo "  $0 13.123.45.67 --upload-json   # JSONファイルのアップロード"
    exit 1
}

# 引数チェック
if [ $# -lt 2 ]; then
    usage
fi

LIGHTSAIL_IP=$1
MODE=$2
SSH_USER="ec2-user"
APP_DIR="my_shogiwars"

echo -e "${GREEN}=== Lightsail デプロイスクリプト ===${NC}"
echo -e "対象サーバー: ${YELLOW}${SSH_USER}@${LIGHTSAIL_IP}${NC}"
echo ""

# 初回セットアップ
if [ "$MODE" == "--setup" ]; then
    echo -e "${GREEN}[1/7] システムパッケージの更新...${NC}"
    ssh ${SSH_USER}@${LIGHTSAIL_IP} "sudo dnf update -y"

    echo -e "${GREEN}[2/7] 必要なパッケージのインストール...${NC}"
    ssh ${SSH_USER}@${LIGHTSAIL_IP} "sudo dnf install -y python3.13 python3.13-pip git && sudo dnf groupinstall -y 'Development Tools'"

    echo -e "${GREEN}[3/7] リポジトリのクローン...${NC}"
    echo -e "${YELLOW}注意: リポジトリURLを確認してください${NC}"
    read -p "GitリポジトリのURL（空でスキップ）: " REPO_URL
    if [ -n "$REPO_URL" ]; then
        ssh ${SSH_USER}@${LIGHTSAIL_IP} "cd ~ && git clone ${REPO_URL} ${APP_DIR} || (cd ${APP_DIR} && git pull)"
    else
        echo -e "${YELLOW}リポジトリのクローンをスキップします。手動でコードをアップロードしてください。${NC}"
        exit 0
    fi

    echo -e "${GREEN}[4/7] 仮想環境の作成とパッケージインストール...${NC}"
    ssh ${SSH_USER}@${LIGHTSAIL_IP} "cd ~/${APP_DIR} && python3.13 -m venv venv && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"

    echo -e "${GREEN}[5/7] resultディレクトリの作成...${NC}"
    ssh ${SSH_USER}@${LIGHTSAIL_IP} "mkdir -p ~/${APP_DIR}/result"

    echo -e "${GREEN}[6/7] systemdサービスの設定...${NC}"
    ssh ${SSH_USER}@${LIGHTSAIL_IP} "cd ~/${APP_DIR} && sudo cp streamlit.service /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable streamlit && sudo systemctl start streamlit"

    echo -e "${GREEN}[7/7] サービスの状態確認...${NC}"
    ssh ${SSH_USER}@${LIGHTSAIL_IP} "sudo systemctl status streamlit --no-pager"

    echo ""
    echo -e "${GREEN}✅ セットアップが完了しました！${NC}"
    echo -e "ブラウザで ${YELLOW}http://${LIGHTSAIL_IP}:8501${NC} にアクセスしてください"
    echo ""
    echo -e "${YELLOW}⚠️  Lightsailのファイアウォールでポート8501を開放してください${NC}"

# コード更新
elif [ "$MODE" == "--update" ]; then
    echo -e "${GREEN}[1/4] コードの更新 (git pull)...${NC}"
    ssh ${SSH_USER}@${LIGHTSAIL_IP} "cd ~/${APP_DIR} && git pull"

    echo -e "${GREEN}[2/4] パッケージの更新...${NC}"
    ssh ${SSH_USER}@${LIGHTSAIL_IP} "cd ~/${APP_DIR} && source venv/bin/activate && pip install -r requirements.txt"

    echo -e "${GREEN}[3/4] サービスの再起動...${NC}"
    ssh ${SSH_USER}@${LIGHTSAIL_IP} "sudo systemctl restart streamlit"

    echo -e "${GREEN}[4/4] サービスの状態確認...${NC}"
    ssh ${SSH_USER}@${LIGHTSAIL_IP} "sudo systemctl status streamlit --no-pager"

    echo ""
    echo -e "${GREEN}✅ 更新が完了しました！${NC}"
    echo -e "ブラウザで ${YELLOW}http://${LIGHTSAIL_IP}:8501${NC} にアクセスしてください"

# JSONファイルのアップロード
elif [ "$MODE" == "--upload-json" ]; then
    if [ ! -d "result" ] || [ -z "$(ls -A result/*.json 2>/dev/null)" ]; then
        echo -e "${RED}エラー: result/ ディレクトリにJSONファイルがありません${NC}"
        exit 1
    fi

    echo -e "${GREEN}JSONファイルをアップロード中...${NC}"
    scp result/*.json ${SSH_USER}@${LIGHTSAIL_IP}:~/${APP_DIR}/result/

    echo -e "${GREEN}サービスを再起動中...${NC}"
    ssh ${SSH_USER}@${LIGHTSAIL_IP} "sudo systemctl restart streamlit"

    echo ""
    echo -e "${GREEN}✅ JSONファイルのアップロードが完了しました！${NC}"

else
    echo -e "${RED}エラー: 不明なオプション: ${MODE}${NC}"
    usage
fi
