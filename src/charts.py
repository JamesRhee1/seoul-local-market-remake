"""Plotly 차트 생성 함수."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from . import config
from .metrics import (
    format_quarter_short_label,
    sort_by_quarter,
    total_store_fluctuation_caption,
)

COLS = config.COLS

_COLOR_OPEN = "#5DADE2"
_COLOR_CLOSE = "#EC7063"
_STATUS_LABELS = {COLS.OPEN_CO: "개업", COLS.CLOSE_CO: "폐업"}


def district_open_close_bar(district_df: pd.DataFrame, title: str = "") -> go.Figure:
    """자치구별 개업 vs 폐업 가로 그룹 막대그래프 (순증감 정렬 순서 유지)."""
    district_order = district_df[COLS.DISTRICT].astype(str).tolist()
    melted = district_df.melt(
        id_vars=COLS.DISTRICT,
        value_vars=[COLS.OPEN_CO, COLS.CLOSE_CO],
        var_name="구분",
        value_name="점포 수",
    )
    melted["구분"] = melted["구분"].map(_STATUS_LABELS)
    melted[COLS.DISTRICT] = pd.Categorical(
        melted[COLS.DISTRICT], categories=district_order, ordered=True
    )

    fig = px.bar(
        melted,
        y=COLS.DISTRICT,
        x="점포 수",
        color="구분",
        barmode="group",
        orientation="h",
        color_discrete_map={"개업": _COLOR_OPEN, "폐업": _COLOR_CLOSE},
        title=title,
        category_orders={COLS.DISTRICT: district_order},
    )
    fig.update_layout(
        xaxis_title="점포 수",
        yaxis_title="자치구",
        legend_title_text="",
        margin=dict(t=60, b=40, l=20, r=20),
        plot_bgcolor="rgba(0,0,0,0)",
        height=max(360, 28 * len(district_order)),
    )
    # 순증감 1위 자치구가 차트 상단에 오도록
    fig.update_yaxes(categoryorder="array", categoryarray=list(reversed(district_order)))
    return fig


def industry_trend_line(trend_df: pd.DataFrame, title: str = "") -> go.Figure:
    """분기별 추이 차트 (총 점포 / 개업·폐업 분리 패널)."""
    from plotly.subplots import make_subplots

    df = sort_by_quarter(trend_df.copy())
    df["_분기라벨"] = df[COLS.QUARTER].astype(str).map(format_quarter_short_label)
    quarter_labels = df["_분기라벨"].tolist()
    fluctuation = total_store_fluctuation_caption(df)
    total_panel_title = (
        f"총 점포 수 — {fluctuation}" if fluctuation else "총 점포 수"
    )

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=(total_panel_title, "개업 / 폐업"),
        vertical_spacing=0.14,
    )
    fig.add_trace(
        go.Scatter(
            x=df["_분기라벨"],
            y=df[COLS.STORE_CO],
            name="총 점포",
            mode="lines+markers",
            line=dict(color="#2E86AB", width=2),
            marker=dict(size=8),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["_분기라벨"],
            y=df[COLS.OPEN_CO],
            name="개업",
            mode="lines+markers",
            line=dict(color=_COLOR_OPEN, width=2),
            marker=dict(size=8),
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df["_분기라벨"],
            y=df[COLS.CLOSE_CO],
            name="폐업",
            mode="lines+markers",
            line=dict(color=_COLOR_CLOSE, width=2),
            marker=dict(size=8),
        ),
        row=2,
        col=1,
    )
    fig.update_layout(
        title=title,
        legend_title_text="",
        margin=dict(t=80, b=40, l=20, r=20),
        plot_bgcolor="rgba(0,0,0,0)",
        height=520,
    )
    xaxis_kw = dict(title_text="분기", categoryorder="array", categoryarray=quarter_labels)
    fig.update_yaxes(title_text="점포 수", row=1, col=1)
    fig.update_yaxes(title_text="점포 수", row=2, col=1)
    fig.update_xaxes(**xaxis_kw, row=1, col=1)
    fig.update_xaxes(**xaxis_kw, row=2, col=1)
    return fig
