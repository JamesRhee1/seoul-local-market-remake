"""pydeck 지도 시각화."""
from __future__ import annotations

import math

import pandas as pd
import pydeck as pdk

from . import config

COLS = config.COLS

# 저밀도(파랑) → 중밀도(노랑) → 고밀도(빨강)
_COLOR_LOW = (46, 134, 171)
_COLOR_MID = (244, 208, 63)
_COLOR_HIGH = (231, 76, 60)

# 서울 전역 기본 뷰 (데이터 없을 때)
_SEOUL_CENTER_LAT = 37.5665
_SEOUL_CENTER_LON = 126.9780
_DEFAULT_ZOOM = 11.5


def _view_state_from_bounds(lat: pd.Series, lon: pd.Series) -> pdk.ViewState:
    """좌표 min/max 중앙값과 범위로 초기 뷰(중심·zoom)를 계산한다."""
    lat_min, lat_max = float(lat.min()), float(lat.max())
    lon_min, lon_max = float(lon.min()), float(lon.max())
    center_lat = (lat_min + lat_max) / 2.0
    center_lon = (lon_min + lon_max) / 2.0

    lat_span = max(lat_max - lat_min, 1e-4)
    lon_span = max(lon_max - lon_min, 1e-4)
    lon_span_lat = lon_span * math.cos(math.radians(center_lat))
    span = max(lat_span, lon_span_lat) * 1.1

    # 서울 시내 데이터가 화면을 채우도록 zoom 보정 (외곽 경기도 여백 최소화)
    zoom = math.log2(360.0 / span) + 1.0
    zoom = float(max(11.0, min(13.0, zoom)))

    return pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=zoom,
        pitch=0,
    )


def density_color(value: float, vmin: float, vmax: float, alpha: int = 190) -> list[int]:
    """점포 수 구간에 따른 RGBA 색상 (순수 함수)."""
    if vmax <= vmin:
        ratio = 0.5
    else:
        ratio = max(0.0, min(1.0, (float(value) - vmin) / (vmax - vmin)))

    if ratio <= 0.5:
        t = ratio / 0.5
        rgb = tuple(int(_COLOR_LOW[i] + (_COLOR_MID[i] - _COLOR_LOW[i]) * t) for i in range(3))
    else:
        t = (ratio - 0.5) / 0.5
        rgb = tuple(int(_COLOR_MID[i] + (_COLOR_HIGH[i] - _COLOR_MID[i]) * t) for i in range(3))
    return [rgb[0], rgb[1], rgb[2], alpha]


def store_density_deck(map_df: pd.DataFrame, title: str = "") -> pdk.Deck:
    """상권 단위 점포 수를 ScatterplotLayer 로 표시한다."""
    if map_df.empty:
        return pdk.Deck(
            layers=[],
            initial_view_state=pdk.ViewState(
                latitude=_SEOUL_CENTER_LAT,
                longitude=_SEOUL_CENTER_LON,
                zoom=_DEFAULT_ZOOM,
            ),
        )

    plot_df = map_df.copy()
    vmin = float(plot_df[COLS.STORE_CO].min())
    vmax = float(plot_df[COLS.STORE_CO].max())
    max_stores = max(vmax, 1.0)
    plot_df["radius"] = (plot_df[COLS.STORE_CO] / max_stores).clip(lower=0.08) * 600
    plot_df["color"] = plot_df[COLS.STORE_CO].apply(
        lambda v: density_color(v, vmin, vmax)
    )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=plot_df,
        get_position=f"[{COLS.LON}, {COLS.LAT}]",
        get_radius="radius",
        get_fill_color="color",
        # pickable=True 는 hover/click 시 Streamlit rerun 루프를 유발할 수 있어 비활성화.
        pickable=False,
    )
    view_state = _view_state_from_bounds(plot_df[COLS.LAT], plot_df[COLS.LON])
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
