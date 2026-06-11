"""전처리 파이프라인 통합 검증 (멱등성·실데이터 유사 스키마)."""
from __future__ import annotations

import pandas as pd

from src import config
from src.preprocessor import run as preprocessor_run
from src.storage import read_table, write_table

COLS = config.COLS


def _write_raw_fixtures(raw_dir) -> None:
    store = pd.DataFrame(
        {
            COLS.TRDAR_CD: [1001, 1001, 1002, 1002],
            COLS.TRDAR_CD_NM: ["상권A", "상권A", "상권B", "상권B"],
            COLS.INDUSTRY: ["커피-음료", "한식음식점", "커피-음료", "한식음식점"],
            COLS.STORE_CO: [10, 5, 8, 3],
            COLS.OPEN_CO: [2, 1, 1, 0],
            COLS.CLOSE_CO: [1, 0, 0, 1],
            COLS.QUARTER: ["20251", "20251", "20252", "20252"],
        }
    )
    location = pd.DataFrame(
        {
            COLS.TRDAR_CD: [1001, 1002],
            COLS.TRDAR_CD_NM: ["위치상권A", "위치상권B"],
            COLS.DISTRICT: ["중구", "강남구"],
            COLS.TM_X: [197093, 202454],
            COLS.TM_Y: [453418, 444235],
        }
    )
    write_table(store, raw_dir / "seoul_market_store.csv")
    write_table(location, raw_dir / "seoul_market_location.csv")


def test_preprocessor_run_is_idempotent(tmp_path, monkeypatch):
    """run() 을 연속 2회 실행해도 final 합본 행수가 변하지 않아야 한다."""
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()

    monkeypatch.setattr(config, "RAW_DIR", raw_dir)
    monkeypatch.setattr(config, "PROCESSED_DIR", processed_dir)
    monkeypatch.setattr(config, "RAW_STORE_FILE", raw_dir / "seoul_market_store.csv")
    monkeypatch.setattr(config, "RAW_LOCATION_FILE", raw_dir / "seoul_market_location.csv")
    monkeypatch.setattr(config, "PROCESSED_FILE", processed_dir / "seoul_market_final.csv")

    _write_raw_fixtures(raw_dir)

    assert preprocessor_run() is not None
    first = read_table(processed_dir / "seoul_market_final.parquet")
    first_rows = len(first)

    assert preprocessor_run() is not None
    second = read_table(processed_dir / "seoul_market_final.parquet")

    assert len(second) == first_rows
    assert COLS.TRDAR_CD_NM in second.columns
    assert not any(str(c).endswith("_x") or str(c).endswith("_y") for c in second.columns)
