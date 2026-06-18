"""Plotly 차트 생성 함수."""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from . import config
from .metrics import (
    format_quarter_short_label,
    sort_by_quarter,
    sort_districts_by_net_change,
    total_store_fluctuation_caption,
)

COLS = config.COLS

_COLOR_OPEN = "#5DADE2"
_COLOR_CLOSE = "#EC7063"


def district_open_close_bar(district_df: pd.DataFrame, title: str = "") -> go.Figure:
    """자치구별 개업 vs 폐업 가로 그룹 막대그래프 (순증감 내림차순, 상단=순증)."""
    sorted_df = sort_districts_by_net_change(district_df)
    district_order = sorted_df[COLS.DISTRICT].astype(str).tolist()
    # plotly y축: categoryarray 는 하단→상단 순 → 역순으로 상단에 순증 1위
    y_axis_order = list(reversed(district_order))

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=district_order,
            x=sorted_df[COLS.OPEN_CO],
            name="개업",
            orientation="h",
            marker_color=_COLOR_OPEN,
        )
    )
    fig.add_trace(
        go.Bar(
            y=district_order,
            x=sorted_df[COLS.CLOSE_CO],
            name="폐업",
            orientation="h",
            marker_color=_COLOR_CLOSE,
        )
    )
    fig.update_layout(
        title=title,
        barmode="group",
        xaxis_title="점포 수",
        yaxis_title="자치구",
        legend_title_text="",
        margin=dict(t=60, b=40, l=20, r=20),
        plot_bgcolor="rgba(0,0,0,0)",
        height=max(360, 28 * len(district_order)),
    )
    fig.update_yaxes(categoryorder="array", categoryarray=y_axis_order)
    return fig


def industry_trend_line(trend_df: pd.DataFrame, title: str = "") -> go.Figure:
    """분기별 추이 차트 (총 점포 / 개업·폐업 분리 패널)."""
    from plotly.subplots import make_subplots

    df = sort_by_quarter(trend_df.copy())
    df["_분기라벨"] = df[COLS.QUARTER].astype(str).map(format_quarter_short_label)
    quarter_labels = df["_분기라벨"].tolist()
    fluctuation = total_store_fluctuation_caption(df)
    total_subtitle = (
        f"<br><sup style='color:#5a6a7a;font-size:11px'>{fluctuation}</sup>"
        if fluctuation
        else ""
    )
    open_close_legend = (
        f"<span style='color:{_COLOR_OPEN}'>●</span> 개업 &nbsp; "
        f"<span style='color:{_COLOR_CLOSE}'>●</span> 폐업"
    )
    subplot_titles = (
        f"<b>총 점포 수</b>{total_subtitle}",
        f"<b>개업 / 폐업</b><br><sup style='color:#5a6a7a;font-size:11px'>"
        f"{open_close_legend}</sup>",
    )

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        subplot_titles=subplot_titles,
        vertical_spacing=0.16,
    )
    fig.add_trace(
        go.Scatter(
            x=df["_분기라벨"],
            y=df[COLS.STORE_CO],
            name="총 점포",
            mode="lines+markers",
            line=dict(color="#2E86AB", width=2),
            marker=dict(size=8),
            showlegend=False,
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
            showlegend=True,
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
            showlegend=True,
        ),
        row=2,
        col=1,
    )
    fig.update_layout(
        title=title,
        legend_title_text="",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=0.46,
            xanchor="left",
            x=0.02,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#dddddd",
            borderwidth=1,
        ),
        margin=dict(t=90, b=40, l=20, r=20),
        plot_bgcolor="rgba(0,0,0,0)",
        height=540,
    )
    fig.update_annotations(font_size=13)
    xaxis_kw = dict(title_text="분기", categoryorder="array", categoryarray=quarter_labels)
    fig.update_yaxes(title_text="점포 수", row=1, col=1)
    fig.update_yaxes(title_text="점포 수", row=2, col=1)
    fig.update_xaxes(**xaxis_kw, row=1, col=1)
    fig.update_xaxes(**xaxis_kw, row=2, col=1)
    return fig
