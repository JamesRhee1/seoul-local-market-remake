"""pydeck 지도 시각화."""
from __future__ import annotations

import pandas as pd
import pydeck as pdk

from . import config

COLS = config.COLS


def store_density_deck(map_df: pd.DataFrame, title: str = "") -> pdk.Deck:
    """상권 단위 점포 수를 ScatterplotLayer 로 표시한다."""
    if map_df.empty:
        return pdk.Deck(
            layers=[],
            initial_view_state=pdk.ViewState(
                latitude=37.5665, longitude=126.9780, zoom=10
            ),
        )

    plot_df = map_df.copy()
    max_stores = max(plot_df[COLS.STORE_CO].max(), 1)
    plot_df["radius"] = (plot_df[COLS.STORE_CO] / max_stores).clip(lower=0.05) * 500

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=plot_df,
        get_position=f"[{COLS.LON}, {COLS.LAT}]",
        get_radius="radius",
        get_fill_color=[46, 134, 171, 180],
        pickable=True,
    )
    view_state = pdk.ViewState(
        latitude=float(plot_df[COLS.LAT].mean()),
        longitude=float(plot_df[COLS.LON].mean()),
        zoom=10.5,
        pitch=0,
    )
    tooltip = {
        "html": (
            f"<b>{{{COLS.TRDAR_CD_NM}}}</b><br/>"
            f"{{{COLS.DISTRICT}}}<br/>"
            f"점포: {{{COLS.STORE_CO}}}"
        ),
        "style": {"color": "white"},
    }
    return pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        description=title,
    )
