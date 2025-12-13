#!/bin/bash
# デプロイスクリプト for Lightsail Amazon Linux 2023
# スクレイピング用JSONファイルのアップロード専用

set -e

# 色の定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 使い方を表示
usage() {
    echo "使い方: $0 <lightsail-ip> <ssh-key-path> --upload-json"
    echo ""
    echo "引数:"
    echo "  lightsail-ip   LightsailインスタンスのIPアドレス"
    echo "  ssh-key-path   SSH鍵ファイルのパス（例: ~/.ssh/lightsail_key.pem）"
    echo ""
    echo "オプション:"
    echo "  --upload-json ローカルのresult/*.jsonをアップロード"
    echo ""
    echo "例:"
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

echo -e "${GREEN}=== Lightsail JSONアップロードスクリプト ===${NC}"
echo -e "対象サーバー: ${YELLOW}${SSH_USER}@${LIGHTSAIL_IP}${NC}"
echo ""

# JSONファイルのアップロード
if [ "$MODE" == "--upload-json" ]; then
    if [ ! -d "result" ] || [ -z "$(ls -A result/*.json 2>/dev/null)" ]; then
        echo -e "${RED}エラー: result/ ディレクトリにJSONファイルがありません${NC}"
        exit 1
    fi

    echo -e "${GREEN}JSONファイルをアップロード中...${NC}"
    scp ${SSH_OPTS} result/*.json ${SSH_USER}@${LIGHTSAIL_IP}:~/${APP_DIR}/result/

    echo ""
    echo -e "${GREEN}✅ JSONファイルのアップロードが完了しました！${NC}"

else
    echo -e "${RED}エラー: 不明なオプション: ${MODE}${NC}"
    usage
fi
