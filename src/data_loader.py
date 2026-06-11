"""대시보드용 데이터 로더.

가공된 데이터(data/processed)가 있으면 사용하고, 없으면 데모용 샘플
(data/sample)로 폴백한다. 덕분에 API 키 없이도 대시보드를 실행할 수 있다.
"""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd

from . import config

COLS = config.COLS


def resolve_data_path() -> Tuple[Path | None, str]:
    """사용할 데이터 경로와 출처 라벨을 반환한다."""
    if config.PROCESSED_FILE.exists():
        return config.PROCESSED_FILE, "processed"
    if config.SAMPLE_FILE.exists():
        return config.SAMPLE_FILE, "sample"
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
    """CSV 를 읽고 최소한의 방어적 정제를 적용한다."""
    return _normalize_loaded(pd.read_csv(path))


def load_quarter_trend_data() -> pd.DataFrame:
    """processed 디렉터리의 분기 스냅샷을 모두 읽어 추이 분석용으로 합친다."""
    quarter_files = sorted(
        config.PROCESSED_DIR.glob(f"{config.QUARTER_FILE_PREFIX}*.csv")
    )
    if quarter_files:
        return _normalize_loaded(
            pd.concat(
                (pd.read_csv(p) for p in quarter_files),
                ignore_index=True,
            )
        )
    path, _ = resolve_data_path()
    if path is None:
        return pd.DataFrame()
    return load_market_data(path)
