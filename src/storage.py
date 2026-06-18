"""데이터 파일 I/O (Parquet 우선, CSV 폴백)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .utils import get_logger

logger = get_logger(__name__)


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
    """Parquet 또는 CSV 를 읽는다.

    논리 경로(.csv 기준)뿐 아니라 이미 존재하는 실제 파일 경로도 그대로 받을 수 있다.
    """
    if path.is_file():
        if path.suffix == ".parquet":
            return pd.read_parquet(path)
        if path.suffix == ".csv":
            return pd.read_csv(path, low_memory=False)
    resolved = resolve_existing(path)
    if resolved is None:
        raise FileNotFoundError(path)
    if resolved.suffix == ".parquet":
        return pd.read_parquet(resolved)
    return pd.read_csv(resolved, low_memory=False)


def verify_parquet_file(path: Path, expected_rows: int | None = None) -> int:
    """Parquet 파일을 다시 읽어 무결성을 검증한다. 실제 행 수를 반환한다."""
    try:
        df = pd.read_parquet(path)
    except Exception as exc:
        raise ValueError(f"Parquet 검증 실패 (읽기 오류): {path} — {exc}") from exc
    actual = len(df)
    if expected_rows is not None and actual != expected_rows:
        raise ValueError(
            f"Parquet 검증 실패 (행수 불일치): {path} "
            f"expected={expected_rows}, actual={actual}"
        )
    return actual


def write_table(df: pd.DataFrame, path: Path) -> Path:
    """Parquet 로 저장한다 (논리 경로는 .csv 기준). 저장 직후 read-back 검증."""
    path.parent.mkdir(parents=True, exist_ok=True)
    out = parquet_path(path)
    expected = len(df)
    df.to_parquet(out, index=False)
    try:
        verify_parquet_file(out, expected_rows=expected)
    except ValueError as exc:
        logger.error("%s", exc)
        raise
    logger.debug("Parquet 검증 완료: %s (%d행)", out.name, expected)
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
