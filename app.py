"""Streamlit 대시보드 진입점.

모든 도메인 로직은 src 패키지에 위임하고, 이 파일은 UI 조립만 담당한다.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src import charts, config, data_loader, maps, metrics

COLS = config.COLS

_TAB_SNAPSHOT = "📊 현황 분석"
_TAB_MAP = "🗺️ 점포 밀도 지도"

st.set_page_config(
    page_title="2025 서울시 로컬 상권 분석",
    page_icon="🛒",
    layout="wide",
)


@st.cache_data(show_spinner="데이터 로딩 중...")
def get_data(path: str, mtime: float) -> pd.DataFrame:
    """Parquet/CSV 를 읽어 캐시한다."""
    del mtime
    return data_loader.load_market_data(Path(path))


def _data_version(directory: Path, prefix: str) -> float:
    """분기 스냅샷 mtime 최댓값 — 캐시 무효화 키."""
    mtimes = [p.stat().st_mtime for p in directory.glob(f"{prefix}*.parquet")]
    return max(mtimes) if mtimes else 0.0


@st.cache_data(show_spinner=False)
def get_trend_data(_version: float) -> pd.DataFrame:
    """추이 탭용 분기 합본 데이터 (processed → sample)."""
    del _version
    return data_loader.load_quarter_trend_data()


@st.cache_data(show_spinner=False)
def get_district_chart(district_df: pd.DataFrame, title: str) -> go.Figure:
    return charts.district_open_close_bar(district_df, title=title)


@st.cache_data(show_spinner=False)
def get_trend_chart(trend_filtered: pd.DataFrame, title: str) -> go.Figure:
    return charts.industry_trend_line(trend_filtered, title=title)


@st.cache_resource(show_spinner=False)
def get_density_deck(map_signature: str, map_df: pd.DataFrame, title: str):
    """pydeck Deck — map_signature 로 필터 변경 시에만 재생성."""
    del map_signature
    return maps.store_density_deck(map_df, title=title)


def _map_signature(map_df: pd.DataFrame) -> str:
    if map_df.empty:
        return "empty"
    cols = [c for c in (COLS.TRDAR_CD, COLS.LAT, COLS.LON, COLS.STORE_CO) if c in map_df.columns]
    ordered = map_df[cols].sort_values(cols, kind="mergesort").reset_index(drop=True)
    return hashlib.md5(ordered.to_json().encode(), usedforsecurity=False).hexdigest()


def _default_industry_index(industries: list[str]) -> int:
    for i, name in enumerate(industries):
        if config.DEFAULT_INDUSTRY_KEYWORD in name:
            return i
    return 0


def _render_trend_quarter_checkboxes(all_quarters: list[str], quarter_year: str) -> list[str]:
    st.sidebar.markdown(f"**{quarter_year} 추이 분기 (추이 탭)**")
    selected: list[str] = []
    for q in all_quarters:
        if st.sidebar.checkbox(
            metrics.format_quarter_short_label(q),
            value=True,
            key=f"trend_quarter_{q}",
        ):
            selected.append(q)
    return selected


@st.fragment
def _render_map_tab(
    snapshot_df: pd.DataFrame,
    selected_industry: str,
    selected_districts: list[str],
    selected_quarter: str,
) -> None:
    map_df = metrics.aggregate_for_map(
        snapshot_df, industry=selected_industry, districts=selected_districts
    )
    if map_df.empty or COLS.LAT not in map_df.columns:
        st.info(
            "지도를 표시하려면 **위치 좌표가 포함된 processed 데이터**가 필요합니다.\n\n"
            "`python run_pipeline.py` 로 수집·전처리하면 상권 TM 좌표가 "
            "WGS84 로 변환되어 지도에 표시됩니다."
        )
        return

    year = metrics.quarter_year(selected_quarter) if selected_quarter else ""
    quarter_note = (
        f"{year} 기준 분기: **{metrics.format_quarter_short_label(selected_quarter)}** · "
        if selected_quarter
        else ""
    )
    st.caption(
        f"{quarter_note}"
        "상권 단위 점포 수 — 아래 범례 참고"
    )
    deck = get_density_deck(
        _map_signature(map_df),
        map_df,
        title=f"{selected_industry} 점포 밀도",
    )
    st.pydeck_chart(deck, use_container_width=True, key="store_density_map")
    vmin = float(map_df[COLS.STORE_CO].min())
    vmax = float(map_df[COLS.STORE_CO].max())
    st.markdown(maps.density_legend_html(vmin, vmax), unsafe_allow_html=True)


@st.fragment
def _render_trend_tab(
    trend_version: float,
    selected_industry: str,
    selected_districts: list[str],
    selected_trend_quarters: list[str],
) -> None:
    trend_df = get_trend_data(trend_version)
    trend_filtered = metrics.aggregate_industry_by_quarter(
        trend_df, industry=selected_industry, districts=selected_districts
    )
    if selected_trend_quarters:
        trend_filtered = metrics.sort_by_quarter(
            trend_filtered[
                trend_filtered[COLS.QUARTER].astype(str).isin(selected_trend_quarters)
            ]
        )

    if selected_trend_quarters:
        year = metrics.quarter_year(selected_trend_quarters[0])
        labels = ", ".join(
            metrics.format_quarter_short_label(q) for q in selected_trend_quarters
        )
        st.caption(f"{year} 표시 분기: {labels}")

    n_quarters = len(trend_filtered)

    if len(selected_trend_quarters) < 2:
        st.info("추이를 보려면 사이드바에서 **2개 이상 분기**를 선택하세요.")
    if trend_filtered.empty:
        st.warning("조건에 해당하는 분기 데이터가 없습니다.")
    elif n_quarters >= 2:
        fig = get_trend_chart(
            trend_filtered,
            title=f"{selected_industry} 분기별 추이 ({n_quarters}개 분기)",
        )
        st.plotly_chart(fig, use_container_width=True, key="industry_trend_chart")


def _render_snapshot_tab(
    filtered: pd.DataFrame,
    selected_industry: str,
    selected_quarter: str,
) -> None:
    if selected_quarter:
        year = metrics.quarter_year(selected_quarter)
        st.caption(
            f"{year} 기준 분기: **{metrics.format_quarter_short_label(selected_quarter)}**"
        )

    st.subheader(f"'{selected_industry}' 상권 현황")
    kpi = metrics.compute_kpi(filtered)
    c1, c2, c3, c4 = st.columns(4, gap="small")
    c1.metric("총 점포 수", f"{kpi.total_stores:,}개")
    c2.metric(
        "신규 개업",
        f"{kpi.total_open:,}개",
        delta=kpi.total_open if kpi.total_open else None,
    )
    c3.metric(
        "폐업",
        f"{kpi.total_close:,}개",
        delta=-kpi.total_close if kpi.total_close else None,
    )
    net = kpi.net_change
    c4.metric(
        "순증감 (개업−폐업)",
        f"{net:,}개",
        delta=net if net != 0 else None,
        delta_color="normal",
    )

    st.divider()

    st.subheader("📊 자치구별 개업 vs 폐업")
    district_df = metrics.aggregate_by_district(filtered)
    if district_df.empty:
        st.warning("조건에 해당하는 데이터가 없습니다.")
    else:
        st.caption("자치구 정렬: **개업+폐업 합계(활동량)** 내림차순 — 활동이 많은 자치구가 위쪽")
        fig = get_district_chart(
            district_df,
            title=f"{selected_industry} 자치구별 현황 (활동량 순)",
        )
        st.plotly_chart(fig, use_container_width=True, key="district_bar_chart")

    with st.expander("📄 원본 데이터 보기"):
        view_cols = [
            c
            for c in [
                COLS.TRDAR_CD_NM,
                COLS.DISTRICT,
                COLS.STORE_CO,
                COLS.OPEN_CO,
                COLS.CLOSE_CO,
            ]
            if c in filtered.columns
        ]
        st.dataframe(filtered[view_cols], use_container_width=True)


def main() -> None:
    path, source = data_loader.resolve_data_path()
    if path is None:
        df = pd.DataFrame()
    else:
        df = get_data(str(path), path.stat().st_mtime)

    if df.empty:
        st.error(
            "표시할 데이터가 없습니다.\n\n"
            "1) `python -m src.collector` 로 수집 → `python -m src.preprocessor` 로 전처리하거나,\n"
            "2) `python -m src.sample_data` 로 `data/sample/` 분기 샘플을 생성하세요."
        )
        st.stop()

    trend_version = max(
        _data_version(config.PROCESSED_DIR, config.QUARTER_FILE_PREFIX),
        _data_version(config.SAMPLE_DIR, config.QUARTER_FILE_PREFIX),
    )

    all_quarters = metrics.quarter_options(df)
    year_label = metrics.quarter_year(all_quarters[-1]) if all_quarters else ""
    title = (
        f"🛒 {year_label} 서울시 로컬 상권 분석 대시보드"
        if year_label
        else "🛒 서울시 로컬 상권 분석 대시보드"
    )
    st.title(title)
    st.caption("Source: 서울 열린데이터 광장 (Seoul Open Data Plaza)")

    if source == "sample":
        st.info("🧪 데모용 **샘플 데이터**로 실행 중입니다. 전체 분석은 수집/전처리 후 가능합니다.")

    st.sidebar.header("🔍 분석 조건")
    industries = metrics.industry_options(df)
    selected_industry = st.sidebar.selectbox(
        "업종",
        industries,
        index=_default_industry_index(industries),
        key="filter_industry",
    )
    selected_districts = st.sidebar.multiselect(
        "자치구 (미선택 시 전체)",
        metrics.district_options(df),
        default=[],
        placeholder="자치구 선택",
        key="filter_districts",
    )

    selected_quarter = all_quarters[-1] if all_quarters else ""
    selected_trend_quarters: list[str] = list(all_quarters)

    if all_quarters:
        quarter_year = metrics.quarter_year(all_quarters[-1])
        st.sidebar.divider()
        selected_quarter = st.sidebar.select_slider(
            f"{quarter_year} 기준 분기 (현황·지도)",
            options=all_quarters,
            value=all_quarters[-1],
            format_func=metrics.format_quarter_short_label,
            key="filter_quarter",
        )
        selected_trend_quarters = _render_trend_quarter_checkboxes(
            all_quarters, quarter_year
        )
        st.sidebar.info(
            "📌 **기준 분기** → 현황·지도 뷰  \n"
            "**추이 분기** → 추이 뷰"
        )

    demo_year = metrics.quarter_year(config.DEMO_QUARTERS[0])
    demo_n = len(config.DEMO_QUARTERS)
    st.sidebar.divider()
    st.sidebar.caption(
        f"데이터: [서울 열린데이터 광장](https://data.seoul.go.kr/) · "
        f"{demo_year}년 1~{demo_n}분기"
    )

    snapshot_df = (
        metrics.filter_by_quarter(df, selected_quarter)
        if selected_quarter
        else metrics.filter_latest_quarter(df)
    )
    filtered = metrics.filter_data(
        snapshot_df, industry=selected_industry, districts=selected_districts
    )

    trend_tab_label = (
        f"📈 {year_label} 업종별 분기 추이" if year_label else "📈 업종별 분기 추이"
    )
    tab_options = [_TAB_SNAPSHOT, _TAB_MAP, trend_tab_label]
    active_tab = st.segmented_control(
        "탭",
        options=tab_options,
        default=_TAB_SNAPSHOT,
        key="main_tab",
        label_visibility="collapsed",
    )

    if active_tab == _TAB_SNAPSHOT:
        _render_snapshot_tab(filtered, selected_industry, selected_quarter)
    elif active_tab == _TAB_MAP:
        _render_map_tab(
            snapshot_df, selected_industry, selected_districts, selected_quarter
        )
    elif active_tab == trend_tab_label:
        _render_trend_tab(
            trend_version,
            selected_industry,
            selected_districts,
            selected_trend_quarters,
        )


if __name__ == "__main__":
    main()
