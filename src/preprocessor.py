"""원천 데이터 전처리.

핵심 변환은 순수 함수(clean_numeric/build_dimension/merge_market_data)로 분리해
파일 I/O 없이도 테스트할 수 있도록 한다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config
from .utils import get_logger

logger = get_logger(__name__)

COLS = config.COLS


def clean_numeric(df: pd.DataFrame, columns=config.NUMERIC_COLS) -> pd.DataFrame:
    """지정한 컬럼을 숫자형으로 강제 변환하고 결측은 0으로 채운다."""
    out = df.copy()
    for col in columns:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    return out


def normalize_key(series: pd.Series) -> pd.Series:
    """상권코드를 일관된 문자열 키로 정규화한다.

    컬럼에 결측이 섞여 float 로 읽히면 astype(str) 가 "3130327.0" 처럼 변해
    조인이 전부 깨진다. 정수로 캐스팅한 뒤 문자열화해 ".0" 혼선을 막는다.
    유효하지 않은 값은 "<NA>" 가 되어 자연스럽게 매칭 실패(Unknown) 처리된다.
    """
    return pd.to_numeric(series, errors="coerce").astype("Int64").astype(str)


def build_dimension(location_df: pd.DataFrame) -> pd.DataFrame:
    """위치 원천에서 (상권코드 → 자치구명) 차원 테이블을 만든다.

    상권코드당 자치구를 1개로 보장해 Left Join 시 행 증식(fan-out)을 방지한다.
    """
    dim = location_df[[COLS.TRDAR_CD, COLS.DISTRICT]].copy()
    dim[COLS.TRDAR_CD] = normalize_key(dim[COLS.TRDAR_CD])
    return dim.drop_duplicates(subset=[COLS.TRDAR_CD], keep="first")


def merge_market_data(store_df: pd.DataFrame, location_df: pd.DataFrame) -> pd.DataFrame:
    """점포(Fact)에 위치 차원을 Left Join 하고 수치형을 정제한다."""
    fact = store_df.copy()
    fact[COLS.TRDAR_CD] = normalize_key(fact[COLS.TRDAR_CD])

    dim = build_dimension(location_df)
    before = len(fact)
    merged = pd.merge(fact, dim, on=COLS.TRDAR_CD, how="left")
    if len(merged) != before:  # fan-out 방어 (이론상 발생하지 않아야 함)
        logger.warning("병합 후 행수 변화: %d → %d", before, len(merged))
    merged[COLS.DISTRICT] = merged[COLS.DISTRICT].fillna("Unknown")

    merged = clean_numeric(merged)

    missing = (merged[COLS.DISTRICT] == "Unknown").sum()
    if missing:
        logger.warning(
            "자치구 매칭 실패: %d건 / %d건 (%.1f%%, Unknown 처리)",
            missing, len(merged), missing / len(merged) * 100,
        )
    return merged


def run() -> Path | None:
    """raw CSV 두 개를 읽어 전처리 후 data/processed 에 저장."""
    if not config.RAW_STORE_FILE.exists() or not config.RAW_LOCATION_FILE.exists():
        logger.error(
            "원천 데이터가 없습니다. collector 를 먼저 실행하세요 (%s, %s)",
            config.RAW_STORE_FILE.name, config.RAW_LOCATION_FILE.name,
        )
        return None

    store_df = pd.read_csv(config.RAW_STORE_FILE, low_memory=False)
    location_df = pd.read_csv(config.RAW_LOCATION_FILE, low_memory=False)
    logger.info("로드 완료: 점포 %d행, 위치 %d행", len(store_df), len(location_df))

    merged = merge_market_data(store_df, location_df)

    config.PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(config.PROCESSED_FILE, index=False, encoding="utf-8-sig")
    logger.info("전처리 완료: %s (%d행)", config.PROCESSED_FILE, len(merged))

    # 데이터가 바뀌었으니 README 인사이트도 자동 갱신 (실패해도 전처리는 성공으로 둔다)
    try:
        from . import report
        report.update_readme(df=merged)
    except Exception as exc:  # noqa: BLE001
        logger.warning("README 자동 갱신 실패(무시): %s", exc)

    return config.PROCESSED_FILE


if __name__ == "__main__":
    run()
