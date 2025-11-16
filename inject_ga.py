"""
Google Analytics injection script for Streamlit
This script injects GA code into Streamlit's index.html before the app starts
"""
from pathlib import Path
import os
import sys
import glob

# ログファイルのパス
LOG_FILE = "/home/ec2-user/my_shogiwars/ga_inject.log"

def log(message):
    """ログをファイルと標準出力に書き込む"""
    print(message)
    try:
        with open(LOG_FILE, 'a') as f:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass

log("=" * 60)
log("Google Analytics injection script started")
log("=" * 60)

GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "")
log(f"GA_MEASUREMENT_ID: {GA_MEASUREMENT_ID if GA_MEASUREMENT_ID else 'NOT SET'}")

if not GA_MEASUREMENT_ID:
    log("⚠ WARNING: GA_MEASUREMENT_ID not set, skipping Google Analytics injection.")
    sys.exit(0)

try:
    # Streamlitのインストールパスを検索
    venv_path = Path("/home/ec2-user/my_shogiwars/venv")
    streamlit_paths = list(venv_path.glob("lib/python*/site-packages/streamlit/static/index.html"))

    if not streamlit_paths:
        log("✗ ERROR: Streamlit index.html not found in venv")
        sys.exit(1)

    # 最新のPythonバージョンを使用
    index_path = sorted(streamlit_paths)[-1]
    log(f"Found Streamlit index.html: {index_path}")

    streamlit_path = index_path.parent.parent
    log(f"Streamlit installation path: {streamlit_path}")

    # ファイルの存在確認
    if not index_path.exists():
        log(f"✗ ERROR: index.html not found at {index_path}")
        sys.exit(1)

    log(f"✓ index.html found")

    # ファイルの読み取り
    with open(index_path, 'r', encoding='utf-8') as f:
        html = f.read()

    log(f"✓ Successfully read index.html ({len(html)} bytes)")

    # Google Analyticsコード
    ga_code = f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_MEASUREMENT_ID}');
    </script>
    """

    # 既に注入済みかチェック
    if GA_MEASUREMENT_ID in html:
        log(f"✓ Google Analytics {GA_MEASUREMENT_ID} already injected")
        log("=" * 60)
        sys.exit(0)

    # </head>タグの存在確認
    if '</head>' not in html:
        log("✗ ERROR: </head> tag not found in index.html")
        sys.exit(1)

    # GAコードを注入
    html = html.replace('</head>', ga_code + '</head>')

    # ファイルに書き込み
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)

    log(f"✓ Successfully injected Google Analytics {GA_MEASUREMENT_ID}")
    log(f"✓ Updated index.html ({len(html)} bytes)")

    # 確認のため再読み込み
    with open(index_path, 'r', encoding='utf-8') as f:
        verification = f.read()

    if GA_MEASUREMENT_ID in verification:
        log("✓ Verification successful: GA code is present in index.html")
    else:
        log("✗ WARNING: Verification failed: GA code not found after injection")

    log("=" * 60)

except Exception as e:
    log(f"✗ EXCEPTION: {type(e).__name__}: {e}")
    import traceback
    log(traceback.format_exc())
    sys.exit(1)
