"""charts 의 figure 생성 스모크 테스트.

렌더링 결과까지 검증하지 않고, trace 구성과 barmode 등
차트 골격이 의도대로 만들어지는지만 확인한다.
"""
from __future__ import annotations

import pandas as pd

from src import config
from src.charts import district_open_close_bar, industry_trend_line

COLS = config.COLS


def _district_df():
    return pd.DataFrame(
        {
            COLS.DISTRICT: ["강남구", "마포구"],
            COLS.OPEN_CO: [10, 5],
            COLS.CLOSE_CO: [3, 7],
        }
    )


def test_bar_chart_has_open_close_traces():
    fig = district_open_close_bar(_district_df(), title="테스트")
    # 개업/폐업 두 시리즈가 그룹 막대로 그려져야 한다
    assert len(fig.data) == 2
    assert {t.name for t in fig.data} == {"개업", "폐업"}
    assert fig.layout.barmode == "group"
    assert fig.layout.title.text == "테스트"


def test_bar_chart_x_axis_is_district():
    fig = district_open_close_bar(_district_df())
    assert set(fig.data[0].x) == {"강남구", "마포구"}


def _trend_df():
    return pd.DataFrame(
        {
            COLS.QUARTER: ["20253", "20254"],
            COLS.STORE_CO: [100, 120],
            COLS.OPEN_CO: [10, 15],
            COLS.CLOSE_CO: [5, 8],
        }
    )


def test_trend_line_has_three_series_on_split_panels():
    fig = industry_trend_line(_trend_df(), title="추이")
    assert len(fig.data) == 3
    assert {t.name for t in fig.data} == {"총 점포", "개업", "폐업"}
    assert fig.layout.title.text == "추이"
    # 총 점포는 상단, 개업/폐업은 하단 패널
    assert fig.data[0].yaxis == "y"
    assert fig.data[1].yaxis == "y2"
