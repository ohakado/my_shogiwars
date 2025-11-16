#!/bin/bash
# Streamlit起動スクリプト（Google Analytics注入機能付き）

set -e

# 作業ディレクトリ
cd /home/ec2-user/my_shogiwars

# 環境変数を設定
export GA_MEASUREMENT_ID="G-ZQ4CEPL2PK"

# Google Analyticsコードを注入
echo "Injecting Google Analytics..."
/home/ec2-user/my_shogiwars/venv/bin/python /home/ec2-user/my_shogiwars/inject_ga.py

# Streamlitを起動
echo "Starting Streamlit..."
exec /home/ec2-user/my_shogiwars/venv/bin/streamlit run shogiwars_viewer.py --server.port=8501 --server.address=0.0.0.0
