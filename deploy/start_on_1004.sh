#!/usr/bin/env bash
# bigsoft: Streamlit 0.0.0.0:8501 기동 → iptime 외부 1004 포워딩
set -euo pipefail

if [[ -d "$HOME/projects/data-analysis/seoul-local-market-remake" ]]; then
  APP_DIR="$HOME/projects/data-analysis/seoul-local-market-remake"
elif [[ -d /mnt/data/hsri20/projects/data-analysis/seoul-local-market-remake ]]; then
  APP_DIR=/mnt/data/hsri20/projects/data-analysis/seoul-local-market-remake
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
cat > .streamlit/config.toml << 'EOF'
[server]
headless = true
address = "0.0.0.0"
port = 18080
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
EOF

echo "==> 기존 streamlit 프로세스 종료"
pkill -f "[s]treamlit run app.py" 2>/dev/null || true
sleep 1

echo "==> Streamlit 시작 (0.0.0.0:18080)"
mkdir -p logs
nohup streamlit run app.py --server.address 0.0.0.0 --server.port 18080 > logs/streamlit.log 2>&1 &
sleep 3

echo "==> listen 확인"
if ! ss -tlnp | grep 18080; then
  echo "FAIL: 18080 포트 listen 실패. logs/streamlit.log:"
  tail -30 logs/streamlit.log
  exit 1
fi

CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18080/ || echo "000")
echo "==> curl 127.0.0.1:18080 → HTTP $CODE"
echo ""
echo "접속 URL: http://bigsoft.iptime.org:18080/"
echo "LAN 테스트: http://192.168.0.51:18080"
