import pandas as pd

from src import config
from src.metrics import (
    aggregate_by_district,
    aggregate_for_map,
    aggregate_industry_by_quarter,
    compute_kpi,
    district_options,
    filter_by_quarter,
    filter_data,
    filter_latest_quarter,
    format_quarter_label,
    format_quarter_short_label,
    industry_options,
    quarter_options,
    quarter_year,
    sort_by_quarter,
    sort_districts_by_net_change,
    total_store_fluctuation_caption,
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


def test_sort_districts_by_net_change():
    df = pd.DataFrame(
        {
            COLS.DISTRICT: ["마포구", "강남구", "중구"],
            COLS.OPEN_CO: [5, 10, 8],
            COLS.CLOSE_CO: [7, 3, 1],
        }
    )
    sorted_df = sort_districts_by_net_change(df)
    assert sorted_df[COLS.DISTRICT].tolist() == ["강남구", "중구", "마포구"]


def test_total_store_fluctuation_caption():
    df = pd.DataFrame(
        {
            COLS.QUARTER: ["20251", "20252"],
            COLS.STORE_CO: [10000, 10150],
            COLS.OPEN_CO: [1, 1],
            COLS.CLOSE_CO: [0, 0],
        }
    )
    caption = total_store_fluctuation_caption(df)
    assert caption == "총 점포 변동폭 약 150개 / 1.5%"


def test_options_sorted_unique():
    assert industry_options(_df()) == sorted(["커피-음료", "한식음식점"])
    assert district_options(_df()) == sorted(["강남구", "중구"])


def _quarter_df():
    return pd.DataFrame(
        {
            COLS.QUARTER: ["20253", "20253", "20254", "20254"],
            COLS.INDUSTRY: ["커피-음료", "한식음식점", "커피-음료", "커피-음료"],
            COLS.DISTRICT: ["중구", "중구", "강남구", "강남구"],
            COLS.STORE_CO: [10, 5, 20, 15],
            COLS.OPEN_CO: [2, 1, 4, 3],
            COLS.CLOSE_CO: [1, 0, 2, 1],
        }
    )


def test_format_quarter_label():
    assert format_quarter_label("20254") == "2025-4분기"
    assert format_quarter_label("20251") == "2025-1분기"


def test_format_quarter_short_label():
    assert format_quarter_short_label("20254") == "4분기"
    assert format_quarter_short_label("20251") == "1분기"


def test_quarter_year():
    assert quarter_year("20254") == "2025"


def test_quarter_options_sorted():
    assert quarter_options(_quarter_df()) == ["20253", "20254"]


def test_filter_latest_quarter_keeps_newest():
    out = filter_latest_quarter(_quarter_df())
    assert set(out[COLS.QUARTER].astype(str)) == {"20254"}
    assert len(out) == 2


def test_filter_by_quarter_keeps_matching():
    out = filter_by_quarter(_quarter_df(), "20253")
    assert len(out) == 2
    assert set(out[COLS.QUARTER].astype(str)) == {"20253"}


def test_filter_by_quarter_empty_for_missing():
    out = filter_by_quarter(_quarter_df(), "20251")
    assert out.empty


def test_filter_by_quarter_no_quarter_column_returns_original():
    df = _df()
    out = filter_by_quarter(df, "20251")
    assert len(out) == len(df)


def test_sort_by_quarter_orders_ascending():
    shuffled = _quarter_df().sample(frac=1, random_state=0)
    out = sort_by_quarter(shuffled)
    assert out[COLS.QUARTER].astype(str).tolist() == ["20253", "20253", "20254", "20254"]


def test_aggregate_for_map_sums_by_trdar():
    df = pd.DataFrame(
        {
            COLS.TRDAR_CD: ["1001", "1001", "1002"],
            COLS.TRDAR_CD_NM: ["A", "A", "B"],
            COLS.DISTRICT: ["중구", "중구", "강남구"],
            COLS.LAT: [37.57, 37.57, 37.50],
            COLS.LON: [126.98, 126.98, 127.03],
            COLS.INDUSTRY: ["커피-음료", "커피-음료", "커피-음료"],
            COLS.STORE_CO: [5, 3, 10],
        }
    )
    out = aggregate_for_map(df, industry="커피-음료")
    assert len(out) == 2
    assert out.loc[out[COLS.TRDAR_CD] == "1001", COLS.STORE_CO].iloc[0] == 8


def test_aggregate_industry_by_quarter():
    agg = aggregate_industry_by_quarter(_quarter_df(), industry="커피-음료")
    assert agg[COLS.QUARTER].tolist() == ["20253", "20254"]
    assert agg[COLS.STORE_CO].tolist() == [10, 35]
    assert agg[COLS.OPEN_CO].tolist() == [2, 7]
