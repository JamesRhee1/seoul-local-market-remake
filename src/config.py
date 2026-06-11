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

# 분기별 스냅샷 파일명 접두사 (예: seoul_market_20261.csv)
QUARTER_FILE_PREFIX = "seoul_market_"


def processed_quarter_path(quarter: str) -> Path:
    """분기 코드에 대응하는 processed 스냅샷 경로."""
    return PROCESSED_DIR / f"{QUARTER_FILE_PREFIX}{quarter}.csv"

# -----------------------------------------------------------------------------
# 서울 열린데이터 광장 API
# -----------------------------------------------------------------------------
# TODO(보안): 2026-06 기준 openapi.seoul.go.kr 은 HTTPS 를 지원하지 않는다
# (8088 포트는 평문 HTTP 전용, 443 포트는 응답 없음 — curl 로 확인).
# 공식적으로 HTTPS 엔드포인트가 열리면 https 로 전환할 것.
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
    QUARTER: str = "STDR_YYQU_CD"             # 기준 년분기 코드 (예: 20261)
    TM_X: str = "XCNTS_VALUE"                 # TM 좌표 X (위치 API)
    TM_Y: str = "YDNTS_VALUE"                 # TM 좌표 Y (위치 API)
    LON: str = "lon"                          # WGS84 경도 (전처리 시 생성)
    LAT: str = "lat"                          # WGS84 위도 (전처리 시 생성)


COLS = Columns()

# 분석에 필요한 수치형 컬럼 (전처리 시 형변환 대상)
NUMERIC_COLS = (COLS.STORE_CO, COLS.OPEN_CO, COLS.CLOSE_CO)

# 전처리 입력 검증용 필수 컬럼 (없으면 병합/집계가 조용히 깨지므로 초입에서 실패시킨다)
REQUIRED_STORE_COLS = (COLS.TRDAR_CD, COLS.INDUSTRY, *NUMERIC_COLS)
REQUIRED_LOCATION_COLS = (COLS.TRDAR_CD, COLS.DISTRICT)

# 대시보드 기본 선택/리포트 대표 업종을 고르는 키워드 (업종명에 포함되면 우선 선택)
DEFAULT_INDUSTRY_KEYWORD = "커피"
