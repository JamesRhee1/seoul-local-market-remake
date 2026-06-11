"""원천 데이터 전처리.

핵심 변환은 순수 함수(clean_numeric/build_dimension/merge_market_data)로 분리해
파일 I/O 없이도 테스트할 수 있도록 한다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config
from .geo import seoul_tm_to_wgs84
from .storage import list_quarter_snapshots, read_table, resolve_existing, write_table
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
    """위치 원천에서 상권코드별 차원 테이블(자치구·좌표)을 만든다.

    상권코드당 1행을 보장해 Left Join 시 행 증식(fan-out)을 방지한다.
    TRDAR_CD_NM 은 점포(Fact)가 이미 보유하므로 차원에 넣지 않는다(병합 시 _x/_y 분리 방지).
    """
    cols = [COLS.TRDAR_CD, COLS.DISTRICT]
    for optional in (COLS.TM_X, COLS.TM_Y):
        if optional in location_df.columns:
            cols.append(optional)
    dim = location_df[cols].copy()
    dim[COLS.TRDAR_CD] = normalize_key(dim[COLS.TRDAR_CD])
    dim = dim.drop_duplicates(subset=[COLS.TRDAR_CD], keep="first")

    if COLS.TM_X in dim.columns and COLS.TM_Y in dim.columns:
        coords = dim.apply(
            lambda row: seoul_tm_to_wgs84(row[COLS.TM_X], row[COLS.TM_Y]),
            axis=1,
            result_type="expand",
        )
        dim[COLS.LON] = coords[0]
        dim[COLS.LAT] = coords[1]
    return dim


def normalize_processed_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Parquet 병합 시 분기·좌표·수치 컬럼 dtype 을 통일한다 (순수 함수)."""
    out = df.copy()
    if COLS.TRDAR_CD in out.columns:
        out[COLS.TRDAR_CD] = normalize_key(out[COLS.TRDAR_CD])
    if COLS.QUARTER in out.columns:
        out[COLS.QUARTER] = out[COLS.QUARTER].astype(str)
    for col in (COLS.TM_X, COLS.TM_Y, COLS.LON, COLS.LAT, *config.NUMERIC_COLS):
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


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
    if (
        resolve_existing(config.RAW_STORE_FILE) is None
        or resolve_existing(config.RAW_LOCATION_FILE) is None
    ):
        logger.error(
            "원천 데이터가 없습니다. collector 를 먼저 실행하세요 (%s, %s)",
            config.RAW_STORE_FILE.name, config.RAW_LOCATION_FILE.name,
        )
        return None

    store_df = read_table(config.RAW_STORE_FILE)
    location_df = read_table(config.RAW_LOCATION_FILE)
    logger.info("로드 완료: 점포 %d행, 위치 %d행", len(store_df), len(location_df))

    validate_schema(store_df, config.REQUIRED_STORE_COLS, "점포(store)")
    validate_schema(location_df, config.REQUIRED_LOCATION_COLS, "위치(location)")

    merged = normalize_processed_dtypes(merge_market_data(store_df, location_df))

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for quarter, qdf in split_by_quarter(merged).items():
        qpath = config.processed_quarter_path(quarter)
        saved = write_table(qdf, qpath)
        logger.info("분기 스냅샷 저장: %s (%d행)", saved.name, len(qdf))

    quarter_files = list_quarter_snapshots(config.PROCESSED_DIR, config.QUARTER_FILE_PREFIX)
    if quarter_files:
        combined = pd.concat(
            (read_table(p.with_suffix(".csv")) for p in quarter_files),
            ignore_index=True,
        )
        combined = normalize_processed_dtypes(combined)
        final = write_table(combined, config.PROCESSED_FILE)
        logger.info(
            "전처리 완료: %s (%d행, 분기 %d개)",
            final,
            len(combined),
            len(quarter_files),
        )
    else:
        final = write_table(merged, config.PROCESSED_FILE)
        logger.info("전처리 완료: %s (%d행)", final, len(merged))

    # README 인사이트 갱신은 run_pipeline.py 오케스트레이터가 담당한다.
    # (전처리 모듈이 report 에 의존하면 단계 간 결합이 생기므로 분리)
    return config.PROCESSED_FILE


if __name__ == "__main__":
    run()
