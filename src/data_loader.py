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


def load_market_data(path: Path) -> pd.DataFrame:
    """CSV 를 읽고 최소한의 방어적 정제를 적용한다."""
    df = pd.read_csv(path)
    if COLS.DISTRICT in df.columns:
        df[COLS.DISTRICT] = df[COLS.DISTRICT].fillna("Unknown")
    for col in config.NUMERIC_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df
