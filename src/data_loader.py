"""대시보드용 데이터 로더.

가공된 데이터(data/processed)가 있으면 사용하고, 없으면 데모용 샘플
(data/sample)로 폴백한다. 덕분에 API 키 없이도 대시보드를 실행할 수 있다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd

from . import config
from .storage import list_quarter_snapshots, read_table, resolve_existing

COLS = config.COLS


def _load_quarter_snapshots_from(directory: Path) -> pd.DataFrame:
    """디렉터리의 분기 스냅샷을 읽어 합친다."""
    quarter_files = list_quarter_snapshots(directory, config.QUARTER_FILE_PREFIX)
    if not quarter_files:
        return pd.DataFrame()
    return _normalize_loaded(
        pd.concat(
            (
                pd.read_parquet(p) if p.suffix == ".parquet" else pd.read_csv(p)
                for p in quarter_files
            ),
            ignore_index=True,
        )
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
    if COLS.DISTRICT in df.columns:
        df[COLS.DISTRICT] = df[COLS.DISTRICT].fillna("Unknown")
    for col in config.NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def load_market_data(path: Path) -> pd.DataFrame:
    """Parquet/CSV 를 읽고 최소한의 방어적 정제를 적용한다."""
    if path.suffix == ".parquet":
        return _normalize_loaded(pd.read_parquet(path))
    return _normalize_loaded(read_table(path))


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
