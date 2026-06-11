"""Plotly 차트 생성 함수."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from . import config

COLS = config.COLS

_COLOR_OPEN = "#5DADE2"
_COLOR_CLOSE = "#EC7063"
_STATUS_LABELS = {COLS.OPEN_CO: "개업", COLS.CLOSE_CO: "폐업"}


def district_open_close_bar(district_df: pd.DataFrame, title: str = "") -> go.Figure:
    """자치구별 개업 vs 폐업 그룹 막대그래프."""
    melted = district_df.melt(
        id_vars=COLS.DISTRICT,
        value_vars=[COLS.OPEN_CO, COLS.CLOSE_CO],
        var_name="구분",
        value_name="점포 수",
    )
    melted["구분"] = melted["구분"].map(_STATUS_LABELS)

    fig = px.bar(
        melted,
        x=COLS.DISTRICT,
        y="점포 수",
        color="구분",
        barmode="group",
        color_discrete_map={"개업": _COLOR_OPEN, "폐업": _COLOR_CLOSE},
        title=title,
    )
    fig.update_layout(
        xaxis_title="자치구",
        legend_title_text="",
        margin=dict(t=60, b=40, l=20, r=20),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(tickangle=-45)
    return fig
