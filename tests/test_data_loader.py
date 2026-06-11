"""data_loader 의 폴백 우선순위(processed > sample > none) 검증.

실제 data/ 디렉토리를 건드리지 않도록 tmp_path 로 경로 상수를 갈아끼운다.
"""
from __future__ import annotations

import pandas as pd
import pytest

from src import config, data_loader

COLS = config.COLS


@pytest.fixture()
def fake_paths(tmp_path, monkeypatch):
    """config 의 데이터 파일 경로를 임시 디렉토리로 치환한다."""
    processed = tmp_path / "processed" / "final.csv"
    sample = tmp_path / "sample" / "sample.csv"
    monkeypatch.setattr(config, "PROCESSED_FILE", processed)
    monkeypatch.setattr(config, "SAMPLE_FILE", sample)
    return processed, sample


def _write_csv(path, n_rows: int = 2):
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            COLS.DISTRICT: ["강남구"] * n_rows,
            COLS.STORE_CO: ["10"] * n_rows,  # 문자열 → 수치 정제 대상
        }
    ).to_csv(path, index=False)


def test_resolve_prefers_processed(fake_paths):
    processed, sample = fake_paths
    _write_csv(processed)
    _write_csv(sample)
    path, source = data_loader.resolve_data_path()
    assert path == processed
    assert source == "processed"


def test_resolve_falls_back_to_sample(fake_paths):
    _, sample = fake_paths
    _write_csv(sample)  # processed 없음
    path, source = data_loader.resolve_data_path()
    assert path == sample
    assert source == "sample"


def test_resolve_returns_none_without_any_data(fake_paths):
    path, source = data_loader.resolve_data_path()
    assert path is None
    assert source == "none"


def test_load_market_data_applies_defensive_cleaning(fake_paths):
    processed, _ = fake_paths
    processed.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            COLS.DISTRICT: ["강남구", None],
            COLS.STORE_CO: ["10", "bad"],
        }
    ).to_csv(processed, index=False)

    df = data_loader.load_market_data(processed)
    assert df[COLS.DISTRICT].tolist() == ["강남구", "Unknown"]
    assert df[COLS.STORE_CO].tolist() == [10.0, 0.0]
