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


def validate_schema(df: pd.DataFrame, required_cols, name: str) -> None:
    """필수 컬럼 존재를 검증한다 (순수 함수).

    컬럼이 빠진 채 병합/집계로 흘러가면 KeyError 나 전부-Unknown 같은
    해석하기 어려운 증상이 되므로, 입력 초입에서 명시적으로 실패시킨다.
    """
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"{name} 데이터에 필수 컬럼이 없습니다: {missing}")


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


def split_by_quarter(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """분기 컬럼 기준으로 데이터프레임을 분할한다 (순수 함수)."""
    if COLS.QUARTER not in df.columns:
        return {}
    out: dict[str, pd.DataFrame] = {}
    for quarter, grp in df.groupby(df[COLS.QUARTER].astype(str)):
        out[str(quarter)] = grp.reset_index(drop=True)
    return out


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

    validate_schema(store_df, config.REQUIRED_STORE_COLS, "점포(store)")
    validate_schema(location_df, config.REQUIRED_LOCATION_COLS, "위치(location)")

    merged = merge_market_data(store_df, location_df)

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for quarter, qdf in split_by_quarter(merged).items():
        qpath = config.processed_quarter_path(quarter)
        qdf.to_csv(qpath, index=False, encoding="utf-8-sig")
        logger.info("분기 스냅샷 저장: %s (%d행)", qpath.name, len(qdf))

    quarter_files = sorted(
        config.PROCESSED_DIR.glob(f"{config.QUARTER_FILE_PREFIX}*.csv")
    )
    if quarter_files:
        combined = pd.concat(
            (pd.read_csv(p, low_memory=False) for p in quarter_files),
            ignore_index=True,
        )
        combined.to_csv(config.PROCESSED_FILE, index=False, encoding="utf-8-sig")
        logger.info(
            "전처리 완료: %s (%d행, 분기 %d개)",
            config.PROCESSED_FILE,
            len(combined),
            len(quarter_files),
        )
    else:
        merged.to_csv(config.PROCESSED_FILE, index=False, encoding="utf-8-sig")
        logger.info("전처리 완료: %s (%d행)", config.PROCESSED_FILE, len(merged))

    # README 인사이트 갱신은 run_pipeline.py 오케스트레이터가 담당한다.
    # (전처리 모듈이 report 에 의존하면 단계 간 결합이 생기므로 분리)
    return config.PROCESSED_FILE


if __name__ == "__main__":
    run()
