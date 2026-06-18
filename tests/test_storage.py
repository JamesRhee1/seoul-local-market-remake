"""storage 모듈 Parquet/CSV 폴백 검증."""
from __future__ import annotations

import pandas as pd
import pytest

from src.storage import (
    list_quarter_snapshots,
    read_table,
    resolve_existing,
    verify_parquet_file,
    write_table,
)


def test_write_and_read_parquet(tmp_path):
    path = tmp_path / "data.csv"
    df = pd.DataFrame({"a": [1, 2]})
    saved = write_table(df, path)
    assert saved.suffix == ".parquet"
    out = read_table(path)
    assert out["a"].tolist() == [1, 2]


def test_read_table_accepts_resolved_parquet_path(tmp_path):
    path = tmp_path / "direct.parquet"
    pd.DataFrame({"c": [7]}).to_parquet(path, index=False)
    assert read_table(path)["c"].tolist() == [7]


def test_read_table_falls_back_to_csv(tmp_path):
    path = tmp_path / "legacy.csv"
    pd.DataFrame({"b": [3]}).to_csv(path, index=False)
    assert resolve_existing(path) == path
    assert read_table(path)["b"].tolist() == [3]


def test_list_quarter_snapshots_prefers_parquet(tmp_path):
    prefix = "seoul_market_"
    pd.DataFrame({"q": [1]}).to_csv(tmp_path / f"{prefix}20254.csv", index=False)
    write_table(pd.DataFrame({"q": [2]}), tmp_path / f"{prefix}20254.csv")
    files = list_quarter_snapshots(tmp_path, prefix)
    assert len(files) == 1
    assert files[0].suffix == ".parquet"


def test_list_quarter_snapshots_ignores_final_and_non_quarter_files(tmp_path):
    prefix = "seoul_market_"
    write_table(pd.DataFrame({"q": [1]}), tmp_path / f"{prefix}20251.csv")
    write_table(pd.DataFrame({"q": [2]}), tmp_path / f"{prefix}20252.csv")
    write_table(pd.DataFrame({"all": [99]}), tmp_path / f"{prefix}final.csv")
    pd.DataFrame({"bak": [0]}).to_parquet(tmp_path / "seoul_market_backup.parquet")
    files = list_quarter_snapshots(tmp_path, prefix)
    assert len(files) == 2
    quarters = {f.stem.removeprefix(prefix) for f in files}
    assert quarters == {"20251", "20252"}


def test_verify_parquet_file_row_count(tmp_path):
    path = tmp_path / "data.parquet"
    pd.DataFrame({"a": [1, 2, 3]}).to_parquet(path, index=False)
    assert verify_parquet_file(path, expected_rows=3) == 3


def test_verify_parquet_file_detects_truncated(tmp_path):
    path = tmp_path / "bad.parquet"
    path.write_bytes(b"PAR1" + b"\x00" * 20)
    with pytest.raises(ValueError, match="읽기 오류"):
        verify_parquet_file(path)


def test_write_table_verifies_after_save(tmp_path):
    path = tmp_path / "data.csv"
    df = pd.DataFrame({"a": [1, 2]})
    saved = write_table(df, path)
    assert verify_parquet_file(saved, expected_rows=2) == 2
