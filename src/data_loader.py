"""대시보드용 데이터 로더.

가공된 데이터(data/processed)가 있으면 사용하고, 없으면 데모용 샘플
(data/sample)로 폴백한다. 덕분에 API 키 없이도 대시보드를 실행할 수 있다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd

from . import config
from .preprocessor import normalize_processed_dtypes
from .storage import list_quarter_snapshots, read_table, resolve_existing
from .utils import get_logger

COLS = config.COLS
logger = get_logger(__name__)


def _load_quarter_snapshots_from(directory: Path) -> pd.DataFrame:
    """디렉터리의 분기 스냅샷을 읽어 합친다."""
    quarter_files = list_quarter_snapshots(directory, config.QUARTER_FILE_PREFIX)
    if not quarter_files:
        return pd.DataFrame()
    return _normalize_loaded(
        pd.concat((read_table(p) for p in quarter_files), ignore_index=True)
    )


def resolve_data_path() -> Tuple[Path | None, str]:
    """사용할 데이터 경로와 출처 라벨을 반환한다 (Parquet 우선)."""
    processed = resolve_existing(config.PROCESSED_FILE)
    if processed is not None:
        return processed, "processed"
    for sample_path in (config.SAMPLE_FILE, config.SAMPLE_FILE_LEGACY):
        sample = resolve_existing(sample_path)
        if sample is not None:
            return sample, "sample"
    return None, "none"


def _normalize_loaded(df: pd.DataFrame) -> pd.DataFrame:
    """로드된 데이터프레임에 공통 방어적 정제를 적용한다."""
    out = normalize_processed_dtypes(df)
    if COLS.DISTRICT in out.columns:
        out[COLS.DISTRICT] = out[COLS.DISTRICT].fillna("Unknown")
    for col in config.NUMERIC_COLS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    return out


def _processed_final_path() -> Path | None:
    return resolve_existing(config.PROCESSED_FILE)


def _is_processed_final(path: Path) -> bool:
    final = _processed_final_path()
    if final is None:
        return False
    try:
        return path.resolve() == final.resolve()
    except OSError:
        return path == final


def _load_processed_snapshots_fallback() -> pd.DataFrame:
    """processed final 읽기 실패 시 분기 스냅샷 concat 폴백."""
    return _load_quarter_snapshots_from(config.PROCESSED_DIR)


def load_market_data(path: Path) -> pd.DataFrame:
    """Parquet/CSV 를 읽고 최소한의 방어적 정제를 적용한다.

    processed final 이 손상(truncated 등)된 경우 분기 스냅샷 concat 으로 폴백한다.
    """
    try:
        return _normalize_loaded(read_table(path))
    except Exception as exc:
        if not _is_processed_final(path):
            raise
        logger.warning(
            "processed final 로드 실패 (%s), 분기 스냅샷 concat 폴백 시도: %s",
            path.name,
            exc,
        )
        fallback = _load_processed_snapshots_fallback()
        if fallback.empty:
            raise
        logger.info("분기 스냅샷 폴백 로드 성공 (%d행)", len(fallback))
        return fallback


def load_quarter_trend_data() -> pd.DataFrame:
    """분기 스냅샷을 읽어 추이 분석용으로 합친다 (processed → sample 순)."""
    for directory in (config.PROCESSED_DIR, config.SAMPLE_DIR):
        trend = _load_quarter_snapshots_from(directory)
        if not trend.empty:
            return trend
    path, _ = resolve_data_path()
    if path is None:
        return pd.DataFrame()
    return load_market_data(path)
