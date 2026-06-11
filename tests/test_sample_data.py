"""sample_data 모듈 검증."""
from __future__ import annotations

import pandas as pd

from src import config
from src.sample_data import build_from_processed
from src.storage import write_table


def test_build_from_processed_creates_quarter_samples(tmp_path, monkeypatch):
    processed_dir = tmp_path / "processed"
    sample_dir = tmp_path / "sample"
    monkeypatch.setattr(config, "PROCESSED_DIR", processed_dir)
    monkeypatch.setattr(config, "SAMPLE_DIR", sample_dir)
    monkeypatch.setattr(config, "SAMPLE_FILE", sample_dir / "seoul_market_final.csv")

    for quarter in ("20251", "20252"):
        write_table(
            pd.DataFrame(
                {
                    config.COLS.QUARTER: [quarter] * 5,
                    config.COLS.DISTRICT: ["강남구"] * 5,
                    config.COLS.STORE_CO: [1, 2, 3, 4, 5],
                    config.COLS.OPEN_CO: [1] * 5,
                    config.COLS.CLOSE_CO: [0] * 5,
                    config.COLS.LON: [126.98] * 5,
                    config.COLS.LAT: [37.57] * 5,
                }
            ),
            config.processed_quarter_path(quarter),
        )

    monkeypatch.setattr(config, "DEMO_QUARTERS", ("20251", "20252"))
    out = build_from_processed(rows_per_quarter=3, seed=1)
    assert out is not None
    assert (sample_dir / "seoul_market_20251.parquet").exists()
    assert (sample_dir / "seoul_market_20252.parquet").exists()
    assert (sample_dir / "seoul_market_final.parquet").exists()
