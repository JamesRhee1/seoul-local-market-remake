"""분석 지표 계산 (순수 함수)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pandas as pd

from . import config

COLS = config.COLS


def format_quarter_label(quarter: str) -> str:
    """분기 코드(예: 20254)를 읽기 쉬운 라벨(예: 2025-4분기)로 변환한다."""
    code = str(quarter)
    if len(code) >= 5 and code[:4].isdigit() and code[4].isdigit():
        return f"{code[:4]}-{code[4]}분기"
    return code


def format_quarter_short_label(quarter: str) -> str:
    """분기 코드(예: 20254)를 짧은 라벨(예: 4분기)로 변환한다."""
    code = str(quarter)
    if len(code) >= 5 and code[:4].isdigit() and code[4].isdigit():
        return f"{code[4]}분기"
    return code


def quarter_year(quarter: str) -> str:
    """분기 코드에서 연도(예: 2025)를 추출한다."""
    code = str(quarter)
    if len(code) >= 4 and code[:4].isdigit():
        return code[:4]
    return code


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
    """자치구별 개업/폐업 합계를 집계하고 순증감(개업−폐업) 내림차순으로 정렬한다."""
    if df.empty:
        return pd.DataFrame(columns=[COLS.DISTRICT, COLS.OPEN_CO, COLS.CLOSE_CO])
    agg = (
        df.groupby(COLS.DISTRICT)[[COLS.OPEN_CO, COLS.CLOSE_CO]]
        .sum()
        .reset_index()
    )
    return sort_districts_by_net_change(agg)


def sort_districts_by_net_change(district_df: pd.DataFrame) -> pd.DataFrame:
    """자치구 집계표를 순증감(개업−폐업) 내림차순으로 정렬한다."""
    if district_df.empty:
        return district_df
    out = district_df.copy()
    net = out[COLS.OPEN_CO] - out[COLS.CLOSE_CO]
    return (
        out.assign(_net=net)
        .sort_values("_net", ascending=False)
        .drop(columns="_net")
        .reset_index(drop=True)
    )


def total_store_fluctuation_caption(trend_df: pd.DataFrame) -> str:
    """총 점포 추이 패널용 변동폭 맥락 문구 (순수 함수)."""
    if trend_df.empty or len(trend_df) < 2:
        return ""
    stores = trend_df[COLS.STORE_CO].astype(float)
    delta = int(round(stores.max() - stores.min()))
    base = float(stores.min())
    if base <= 0:
        return f"총 점포 변동폭 약 {delta:,}개"
    pct = delta / base * 100.0
    return f"총 점포 변동폭 약 {delta:,}개 / {pct:.1f}%"


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


def quarter_options(df: pd.DataFrame) -> List[str]:
    """선택 가능한 분기 코드 목록(정렬)."""
    if COLS.QUARTER not in df.columns:
        return []
    return sorted(df[COLS.QUARTER].astype(str).dropna().unique().tolist())


def filter_latest_quarter(df: pd.DataFrame) -> pd.DataFrame:
    """여러 분기가 섞여 있으면 최신 분기만 남긴다 (순수 함수)."""
    quarters = quarter_options(df)
    if not quarters:
        return df
    latest = quarters[-1]
    return filter_by_quarter(df, latest)


def filter_by_quarter(df: pd.DataFrame, quarter: str) -> pd.DataFrame:
    """주어진 분기 코드와 일치하는 행만 반환한다 (순수 함수)."""
    if COLS.QUARTER not in df.columns:
        return df
    return df[df[COLS.QUARTER].astype(str) == str(quarter)].copy()


def sort_by_quarter(df: pd.DataFrame) -> pd.DataFrame:
    """분기 코드(20251, 20252, …) 오름차순으로 행을 정렬한다 (순수 함수)."""
    if df.empty or COLS.QUARTER not in df.columns:
        return df
    return (
        df.assign(_quarter_sort=df[COLS.QUARTER].astype(str))
        .sort_values("_quarter_sort")
        .drop(columns="_quarter_sort")
        .reset_index(drop=True)
    )


def aggregate_for_map(
    df: pd.DataFrame,
    industry: Optional[str] = None,
    districts: Optional[List[str]] = None,
) -> pd.DataFrame:
    """상권 단위 점포 밀도 집계 (지도용 좌표 포함)."""
    filtered = filter_data(df, industry=industry, districts=districts)
    required = [COLS.TRDAR_CD, COLS.LAT, COLS.LON, COLS.STORE_CO]
    if filtered.empty or any(c not in filtered.columns for c in required):
        return pd.DataFrame(
            columns=[
                COLS.TRDAR_CD,
                COLS.TRDAR_CD_NM,
                COLS.DISTRICT,
                COLS.LAT,
                COLS.LON,
                COLS.STORE_CO,
            ]
        )
    group_cols = [COLS.TRDAR_CD, COLS.LAT, COLS.LON]
    if COLS.TRDAR_CD_NM in filtered.columns:
        group_cols.insert(1, COLS.TRDAR_CD_NM)
    if COLS.DISTRICT in filtered.columns:
        group_cols.append(COLS.DISTRICT)
    return (
        filtered.groupby(group_cols, as_index=False)[COLS.STORE_CO]
        .sum()
        .sort_values(COLS.STORE_CO, ascending=False)
    )


def aggregate_industry_by_quarter(
    df: pd.DataFrame,
    industry: Optional[str] = None,
    districts: Optional[List[str]] = None,
) -> pd.DataFrame:
    """업종·자치구 조건으로 필터링한 뒤 분기별 점포/개업/폐업 합계를 집계한다."""
    filtered = filter_data(df, industry=industry, districts=districts)
    if filtered.empty or COLS.QUARTER not in filtered.columns:
        return pd.DataFrame(
            columns=[COLS.QUARTER, COLS.STORE_CO, COLS.OPEN_CO, COLS.CLOSE_CO]
        )
    return (
        filtered.groupby(filtered[COLS.QUARTER].astype(str))[
            [COLS.STORE_CO, COLS.OPEN_CO, COLS.CLOSE_CO]
        ]
        .sum()
        .reset_index()
        .pipe(sort_by_quarter)
    )
