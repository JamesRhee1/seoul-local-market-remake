#!/usr/bin/env bash
# bigsoft 등 자체 서버 최초 설치 스크립트 (hsri20 계정 홈에서 실행)
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/JamesRhee1/seoul-local-market-remake.git}"
APP_DIR="${APP_DIR:-$HOME/seoul-local-market-remake}"

echo "==> Clone or update repo: $APP_DIR"
if [[ -d "$APP_DIR/.git" ]]; then
  git -C "$APP_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

echo "==> Python venv"
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

echo "==> Sample data check"
if compgen -G "data/sample/*.parquet" > /dev/null; then
  echo "    sample parquet OK"
else
  echo "    WARNING: data/sample/*.parquet 없음 — git clone에 포함되어야 합니다."
fi

echo "==> 앱 기동 (포트 1004)"
echo "    bash deploy/start_on_1004.sh"
echo ""
echo "==> systemd 등록 (선택, sudo 필요)"
echo "    sudo cp deploy/seoul-market-streamlit.service /etc/systemd/system/"
echo "    sudo systemctl daemon-reload"
echo "    sudo systemctl enable --now seoul-market-streamlit"
echo "    sudo systemctl status seoul-market-streamlit"
echo ""
echo "==> 공유기 포트포워딩 (iptime)"
echo "    1) 원격관리 포트 1004 → 8443 등으로 변경 (충돌 해제)"
echo "    2) 외부 1004 → 이 서버 LAN IP:1004 (TCP)"
echo "    접속 URL: http://bigsoft.iptime.org:1004/"
