"""데이터 파일 I/O (Parquet 우선, CSV 폴백)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def parquet_path(path: Path) -> Path:
    """논리 경로(.csv)에 대응하는 Parquet 경로."""
    return path.with_suffix(".parquet")


def resolve_existing(path: Path) -> Path | None:
    """존재하는 파일 경로를 반환한다 (Parquet 우선)."""
    pq = parquet_path(path)
    if pq.exists():
        return pq
    if path.exists():
        return path
    return None


def read_table(path: Path) -> pd.DataFrame:
    """Parquet 또는 CSV 를 읽는다."""
    resolved = resolve_existing(path)
    if resolved is None:
        raise FileNotFoundError(path)
    if resolved.suffix == ".parquet":
        return pd.read_parquet(resolved)
    return pd.read_csv(resolved, low_memory=False)


def write_table(df: pd.DataFrame, path: Path) -> Path:
    """Parquet 로 저장한다 (논리 경로는 .csv 기준)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    out = parquet_path(path)
    df.to_parquet(out, index=False)
    return out


def is_quarter_snapshot_code(quarter: str) -> bool:
    """5자리 숫자 분기 코드(예: 20254)만 스냅샷으로 인정한다."""
    return quarter.isdigit() and len(quarter) == 5


def list_quarter_snapshots(processed_dir: Path, prefix: str) -> list[Path]:
    """분기 스냅샷 파일 목록 (분기당 Parquet 우선)."""
    by_quarter: dict[str, Path] = {}
    for candidate in processed_dir.glob(f"{prefix}*"):
        if candidate.suffix not in {".csv", ".parquet"}:
            continue
        quarter = candidate.stem.removeprefix(prefix)
        if not is_quarter_snapshot_code(quarter):
            continue
        existing = by_quarter.get(quarter)
        if existing is None or (existing.suffix == ".csv" and candidate.suffix == ".parquet"):
            by_quarter[quarter] = candidate
    return [by_quarter[q] for q in sorted(by_quarter)]
