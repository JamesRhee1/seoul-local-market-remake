"""분석 지표 계산 (순수 함수)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from . import config

COLS = config.COLS


@dataclass(frozen=True)
class Kpi:
    total_stores: int
    total_open: int
    total_close: int


def filter_data(
    df: pd.DataFrame,
    industry: Optional[str] = None,
    districts: Optional[List[str]] = None,
) -> pd.DataFrame:
    """업종/자치구 조건으로 필터링한다 (조건이 없으면 전체)."""
    out = df
    if industry:
        out = out[out[COLS.INDUSTRY] == industry]
    if districts:
        out = out[out[COLS.DISTRICT].isin(districts)]
    return out


def compute_kpi(df: pd.DataFrame) -> Kpi:
    """총 점포/개업/폐업 합계를 계산한다."""
    if df.empty:
        return Kpi(0, 0, 0)
    return Kpi(
        total_stores=int(df[COLS.STORE_CO].sum()),
        total_open=int(df[COLS.OPEN_CO].sum()),
        total_close=int(df[COLS.CLOSE_CO].sum()),
    )


def aggregate_by_district(df: pd.DataFrame) -> pd.DataFrame:
    """자치구별 개업/폐업 합계를 집계한다."""
    if df.empty:
        return pd.DataFrame(columns=[COLS.DISTRICT, COLS.OPEN_CO, COLS.CLOSE_CO])
    return (
        df.groupby(COLS.DISTRICT)[[COLS.OPEN_CO, COLS.CLOSE_CO]]
        .sum()
        .reset_index()
        .sort_values(COLS.OPEN_CO, ascending=False)
    )


def industry_options(df: pd.DataFrame) -> List[str]:
    """선택 가능한 업종 목록(정렬)."""
    if COLS.INDUSTRY not in df.columns:
        return []
    return sorted(df[COLS.INDUSTRY].astype(str).unique().tolist())


def district_options(df: pd.DataFrame) -> List[str]:
    """선택 가능한 자치구 목록(정렬)."""
    if COLS.DISTRICT not in df.columns:
        return []
    return sorted(df[COLS.DISTRICT].astype(str).unique().tolist())
