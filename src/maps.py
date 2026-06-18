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


def _rgb_css(rgb: tuple[int, int, int]) -> str:
    return f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})"


def density_legend_html(vmin: float, vmax: float) -> str:
    """점포 밀도 지도용 색상 그라데이션·원 크기 범례 HTML."""
    low = _rgb_css(_COLOR_LOW)
    mid = _rgb_css(_COLOR_MID)
    high = _rgb_css(_COLOR_HIGH)
    vmin_i = int(round(vmin))
    vmax_i = int(round(vmax))
    gradient = f"linear-gradient(to right, {low}, {mid}, {high})"
    outer = (
        "display:flex; flex-wrap:wrap; gap:28px; align-items:flex-end; "
        "margin-top:10px; font-size:0.9rem; color:#333;"
    )
    bar = (
        f"width:180px; height:14px; border-radius:6px; border:1px solid #ddd; "
        f"background:{gradient};"
    )
    labels = (
        "display:flex; justify-content:space-between; width:180px; "
        "margin:4px 0 0 3.3em; font-size:0.78rem; color:#666;"
    )
    dot_sm = (
        f"width:14px; height:14px; border-radius:50%; background:{mid}; "
        "opacity:0.85; border:1px solid #ccc;"
    )
    dot_lg = (
        f"width:30px; height:30px; border-radius:50%; background:{mid}; "
        "opacity:0.85; border:1px solid #ccc;"
    )
    return f"""<div style="{outer}">
  <div>
    <div style="margin-bottom:6px; font-weight:600;">점포 밀도 (색상)</div>
    <div style="display:flex; align-items:center; gap:8px;">
      <span style="min-width:2.5em; text-align:right;">{vmin_i}</span>
      <div style="{bar}"></div>
      <span style="min-width:2.5em;">{vmax_i}</span>
    </div>
    <div style="{labels}">
      <span>저밀도</span><span>고밀도</span>
    </div>
  </div>
  <div>
    <div style="margin-bottom:6px; font-weight:600;">점포 수 (원 크기)</div>
    <div style="display:flex; align-items:flex-end; gap:10px;">
      <div style="{dot_sm}"></div>
      <span style="font-size:0.82rem; margin-bottom:1px;">적음</span>
      <div style="{dot_lg}"></div>
      <span style="font-size:0.82rem; margin-bottom:1px;">많음</span>
    </div>
  </div>
</div>"""
