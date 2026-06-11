"""processed 데이터에서 데모용 분기별 샘플을 생성한다.

`data/sample/seoul_market_{분기}.parquet` 4개와 합본 final 을 만든다.
좌표(lon/lat)가 포함된 processed 스냅샷이 있어야 지도 데모도 동작한다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import config
from .preprocessor import normalize_processed_dtypes
from .storage import list_quarter_snapshots, read_table, resolve_existing, write_table
from .utils import get_logger

logger = get_logger(__name__)


def build_from_processed(
    rows_per_quarter: int = 250,
    seed: int = 42,
) -> Path | None:
    """DEMO_QUARTERS 각각에서 샘플을 추출해 data/sample 에 저장한다."""
    config.SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    saved_any = False

    for quarter in config.DEMO_QUARTERS:
        src = config.processed_quarter_path(quarter)
        if resolve_existing(src) is None:
            logger.error("processed 분기 스냅샷이 없습니다: %s", src.name)
            return None

        df = read_table(src)
        n = min(rows_per_quarter, len(df))
        sample = df.sample(n=n, random_state=seed).reset_index(drop=True)
        sample = normalize_processed_dtypes(sample)
        out = write_table(sample, config.sample_quarter_path(quarter))
        logger.info("샘플 저장: %s (%d행)", out.name, len(sample))
        saved_any = True

    if not saved_any:
        return None

    quarter_files = list_quarter_snapshots(config.SAMPLE_DIR, config.QUARTER_FILE_PREFIX)
    combined = normalize_processed_dtypes(
        pd.concat(
            (read_table(p) for p in quarter_files),
            ignore_index=True,
        )
    )
    final = write_table(combined, config.SAMPLE_FILE)
    logger.info(
        "샘플 합본 저장: %s (%d행, 분기 %d개)",
        final,
        len(combined),
        len(quarter_files),
    )
    return final


if __name__ == "__main__":
    build_from_processed()
