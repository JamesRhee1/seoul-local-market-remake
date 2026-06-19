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
    assert len(fig.data) == 2
    assert {t.name for t in fig.data} == {"개업", "폐업"}
    assert fig.layout.barmode == "group"
    assert fig.layout.title.text == "테스트"
    assert fig.data[0].orientation == "h"
    assert fig.data[0].name == "폐업"
    assert fig.data[1].name == "개업"
    assert fig.data[0].marker.color == config.CHART_COLOR_CLOSE
    assert fig.data[1].marker.color == config.CHART_COLOR_OPEN
    # 입력 순서와 무관하게 활동량(개업+폐업) 내림차순
    assert list(fig.data[1].y) == ["강남구", "마포구"]


def test_bar_chart_y_axis_is_district_sorted_by_activity():
    raw = pd.DataFrame(
        {
            COLS.DISTRICT: ["마포구", "강남구", "중구"],
            COLS.OPEN_CO: [5, 10, 8],
            COLS.CLOSE_CO: [7, 3, 1],
        }
    )
    fig = district_open_close_bar(raw)
    assert list(fig.data[1].y) == ["강남구", "마포구", "중구"]
    assert list(fig.layout.yaxis.categoryarray) == ["중구", "마포구", "강남구"]


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
    assert fig.data[1].line.color == config.CHART_COLOR_OPEN
    assert fig.data[2].line.color == config.CHART_COLOR_CLOSE
    # 총 점포는 상단, 개업/폐업은 하단 패널
    assert fig.data[0].yaxis == "y"
    assert fig.data[1].yaxis == "y2"


def test_trend_line_total_panel_shows_fluctuation_context():
    df = pd.DataFrame(
        {
            COLS.QUARTER: ["20251", "20252", "20253", "20254"],
            COLS.STORE_CO: [16700, 16650, 16600, 16700],
            COLS.OPEN_CO: [100, 90, 85, 110],
            COLS.CLOSE_CO: [150, 140, 135, 120],
        }
    )
    fig = industry_trend_line(df)
    top_title = fig.layout.annotations[0].text
    assert "총 점포 수" in top_title
    assert "변동폭" in top_title
    assert "100" in top_title
    bottom_title = fig.layout.annotations[1].text
    assert "개업 / 폐업" in bottom_title
    assert "개업" in bottom_title and "폐업" in bottom_title
    assert fig.data[0].showlegend is False
    assert {t.name for t in fig.data if t.showlegend} == {"개업", "폐업"}
