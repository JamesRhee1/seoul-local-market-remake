"""프로젝트 전역 설정.

API 키는 .env 에서 로드하며, 경로/서비스명/컬럼명 등 매직값을 한곳에 모은다.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트 = 이 파일(src/config.py)의 부모의 부모
ROOT_DIR = Path(__file__).resolve().parent.parent

# .env 로드 (없어도 조용히 통과 → 샘플 데이터 데모는 키 없이 동작)
load_dotenv(ROOT_DIR / ".env")

# -----------------------------------------------------------------------------
# 경로
# -----------------------------------------------------------------------------
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLE_DIR = DATA_DIR / "sample"

RAW_STORE_FILE = RAW_DIR / "seoul_market_store.csv"
RAW_LOCATION_FILE = RAW_DIR / "seoul_market_location.csv"
PROCESSED_FILE = PROCESSED_DIR / "seoul_market_final.csv"
SAMPLE_FILE = SAMPLE_DIR / "seoul_market_sample.csv"

# -----------------------------------------------------------------------------
# 서울 열린데이터 광장 API
# -----------------------------------------------------------------------------
API_BASE_URL = "http://openapi.seoul.go.kr:8088"
SERVICE_STORE = "VwsmTrdarStorQq"   # 상권-점포 (Fact)
SERVICE_LOCATION = "TbgisTrdarRelm"  # 상권 영역 (Dimension)

BATCH_SIZE = 1000
REQUEST_TIMEOUT = 15        # 초
MAX_RETRIES = 3
RETRY_BACKOFF = 1.5         # 초 (지수 백오프 기준값)


def _read_int_env(key: str, default: int) -> int:
    raw = os.getenv(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


SEOUL_API_KEY = os.getenv("SEOUL_API_KEY", "").strip()
COLLECT_LIMIT = _read_int_env("COLLECT_LIMIT", 20000)
# 기준 년분기 코드 (예: 20261 = 2026년 1분기). 비우면 전체 분기 수집.
TARGET_QUARTER = os.getenv("TARGET_QUARTER", "").strip()

# 키가 없거나 플레이스홀더면 미설정으로 간주
_PLACEHOLDERS = {"", "YOUR_ACCESS_KEY_HERE", "여기에_인증키를_입력하세요"}


def has_valid_api_key() -> bool:
    """수집에 사용할 수 있는 유효한 키가 설정되었는지 여부."""
    return SEOUL_API_KEY not in _PLACEHOLDERS


# -----------------------------------------------------------------------------
# 컬럼명 (데이터 스키마)
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class Columns:
    TRDAR_CD: str = "TRDAR_CD"                # 상권 코드 (조인 키)
    TRDAR_CD_NM: str = "TRDAR_CD_NM"          # 상권명
    DISTRICT: str = "SIGNGU_CD_NM"            # 자치구명
    INDUSTRY: str = "SVC_INDUTY_CD_NM"        # 업종명
    STORE_CO: str = "STOR_CO"                 # 점포 수
    OPEN_CO: str = "OPBIZ_STOR_CO"            # 개업 점포 수
    CLOSE_CO: str = "CLSBIZ_STOR_CO"          # 폐업 점포 수


COLS = Columns()

# 분석에 필요한 수치형 컬럼 (전처리 시 형변환 대상)
NUMERIC_COLS = (COLS.STORE_CO, COLS.OPEN_CO, COLS.CLOSE_CO)
