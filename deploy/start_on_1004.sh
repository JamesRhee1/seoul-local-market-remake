#!/usr/bin/env bash
# bigsoft 서버에서 Streamlit을 0.0.0.0:1004 로 기동 (SSH 세션에서 실행)
set -euo pipefail

if [[ -d /mnt/data/hsri20/seoul-local-market-remake ]]; then
  APP_DIR=/mnt/data/hsri20/seoul-local-market-remake
elif [[ -d "$HOME/seoul-local-market-remake" ]]; then
  APP_DIR="$HOME/seoul-local-market-remake"
else
  echo "ERROR: seoul-local-market-remake 디렉터리를 찾을 수 없습니다." >&2
  exit 1
fi

cd "$APP_DIR"
echo "==> APP_DIR: $APP_DIR"

if [[ -d .git ]]; then
  git pull --ff-only || true
fi

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -U pip
  pip install -r requirements.txt
else
  source .venv/bin/activate
fi

mkdir -p .streamlit
if [[ ! -f .streamlit/config.toml ]] || ! grep -q 'port = 1004' .streamlit/config.toml 2>/dev/null; then
  cat > .streamlit/config.toml << 'EOF'
[server]
headless = true
address = "0.0.0.0"
port = 1004
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
EOF
fi

echo "==> 기존 streamlit 프로세스 종료"
pkill -f "[s]treamlit run app.py" 2>/dev/null || true
sleep 1

echo "==> Streamlit 시작 (0.0.0.0:1004)"
nohup streamlit run app.py > streamlit.log 2>&1 &
sleep 3

echo "==> listen 확인"
ss -tlnp | grep 1004 || { echo "FAIL: 1004 포트가 listen 하지 않습니다. streamlit.log:"; tail -20 streamlit.log; exit 1; }

CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:1004/ || echo "000")
echo "==> curl 127.0.0.1:1004 → HTTP $CODE"
echo ""
echo "다음: iptime에서"
echo "  1) 원격관리 포트 1004 → 8443 등으로 변경 (또는 끄기)"
echo "  2) 포트포워드: 외부 1004 → 192.168.0.51:1004 (TCP)"
echo "  3) 브라우저: http://bigsoft.iptime.org:1004/"
