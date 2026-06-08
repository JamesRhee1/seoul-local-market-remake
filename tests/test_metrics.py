import pandas as pd

from src import config
from src.metrics import (
    aggregate_by_district,
    compute_kpi,
    district_options,
    filter_data,
    industry_options,
)

COLS = config.COLS


def _df():
    return pd.DataFrame(
        {
            COLS.INDUSTRY: ["커피-음료", "커피-음료", "한식음식점"],
            COLS.DISTRICT: ["중구", "강남구", "중구"],
            COLS.TRDAR_CD_NM: ["A", "B", "C"],
            COLS.STORE_CO: [10, 20, 5],
            COLS.OPEN_CO: [2, 4, 1],
            COLS.CLOSE_CO: [1, 2, 0],
        }
    )


def test_filter_by_industry():
    out = filter_data(_df(), industry="커피-음료")
    assert len(out) == 2
    assert set(out[COLS.INDUSTRY]) == {"커피-음료"}


def test_filter_by_districts():
    out = filter_data(_df(), districts=["중구"])
    assert len(out) == 2


def test_compute_kpi():
    kpi = compute_kpi(_df())
    assert kpi.total_stores == 35
    assert kpi.total_open == 7
    assert kpi.total_close == 3


def test_compute_kpi_empty():
    kpi = compute_kpi(_df().iloc[0:0])
    assert (kpi.total_stores, kpi.total_open, kpi.total_close) == (0, 0, 0)


def test_aggregate_by_district():
    agg = aggregate_by_district(filter_data(_df(), industry="커피-음료"))
    assert set(agg[COLS.DISTRICT]) == {"중구", "강남구"}
    assert agg[COLS.OPEN_CO].sum() == 6


def test_options_sorted_unique():
    assert industry_options(_df()) == sorted(["커피-음료", "한식음식점"])
    assert district_options(_df()) == sorted(["강남구", "중구"])
