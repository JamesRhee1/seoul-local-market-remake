#!/usr/bin/env bash
# bigsoft: Streamlit 0.0.0.0:8501 기동 → iptime 외부 1004 포워딩
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
cat > .streamlit/config.toml << 'EOF'
[server]
headless = true
address = "0.0.0.0"
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
EOF

echo "==> 기존 streamlit 프로세스 종료"
pkill -f "[s]treamlit run app.py" 2>/dev/null || true
sleep 1

echo "==> Streamlit 시작 (0.0.0.0:8501)"
nohup streamlit run app.py > streamlit.log 2>&1 &
sleep 3

echo "==> listen 확인"
if ! ss -tlnp | grep 8501; then
  echo "FAIL: 8501 포트 listen 실패. streamlit.log:"
  tail -30 streamlit.log
  exit 1
fi

CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8501/ || echo "000")
echo "==> curl 127.0.0.1:8501 → HTTP $CODE"
echo ""
echo "iptime 설정 (필수):"
echo "  1) 원격관리 포트 1004 → 8443 으로 변경 (또는 끄기)"
echo "  2) 포트포워드: 외부 1004 → 192.168.0.51:8501 (TCP)"
echo "  3) 접속: http://bigsoft.iptime.org:1004/"
echo ""
echo "LAN 테스트: http://192.168.0.51:8501"
