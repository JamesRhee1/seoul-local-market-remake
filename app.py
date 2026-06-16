"""Streamlit 대시보드 진입점.

모든 도메인 로직은 src 패키지에 위임하고, 이 파일은 UI 조립만 담당한다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import charts, config, data_loader, maps, metrics

COLS = config.COLS

st.set_page_config(
    page_title="2025 서울시 로컬 상권 분석",
    page_icon="🛒",
    layout="wide",
)


@st.cache_data(show_spinner="데이터 로딩 중...")
def get_data(path: str, mtime: float) -> pd.DataFrame:
    """CSV 를 읽어 캐시한다.

    path/mtime 이 캐시 키가 되므로, 전처리로 파일이 새로 생성되면
    (mtime 변경) 재실행 시 자동으로 캐시가 무효화된다.
    """
    del mtime  # 캐시 키 전용 인자
    return data_loader.load_market_data(Path(path))


def _default_industry_index(industries: list[str]) -> int:
    for i, name in enumerate(industries):
        if config.DEFAULT_INDUSTRY_KEYWORD in name:
            return i
    return 0


def _render_trend_quarter_checkboxes(all_quarters: list[str], quarter_year: str) -> list[str]:
    """추이 분기 선택 — all_quarters 순(1→4분기)으로 렌더해 표시·결과 순서를 고정한다."""
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

    # --- 사이드바: 필터 ---
    st.sidebar.header("🔍 분석 조건")
    industries = metrics.industry_options(df)
    selected_industry = st.sidebar.selectbox(
        "업종", industries, index=_default_industry_index(industries)
    )
    selected_districts = st.sidebar.multiselect(
        "자치구 (미선택 시 전체)", metrics.district_options(df), default=[]
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
        )
        selected_trend_quarters = _render_trend_quarter_checkboxes(
            all_quarters, quarter_year
        )
        st.sidebar.caption("기준 분기 = 현황·지도 / 추이 분기 = 추이 탭")

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
    tab_snapshot, tab_map, tab_trend = st.tabs(
        ["📊 현황 분석", "🗺️ 점포 밀도 지도", trend_tab_label]
    )

    with tab_snapshot:
        if selected_quarter:
            year = metrics.quarter_year(selected_quarter)
            st.caption(
                f"{year} 기준 분기: **{metrics.format_quarter_short_label(selected_quarter)}**"
            )

        st.subheader(f"'{selected_industry}' 상권 현황")
        kpi = metrics.compute_kpi(filtered)
        c1, c2, c3 = st.columns(3)
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

        st.divider()

        st.subheader("📊 자치구별 개업 vs 폐업")
        district_df = metrics.aggregate_by_district(filtered)
        if district_df.empty:
            st.warning("조건에 해당하는 데이터가 없습니다.")
        else:
            fig = charts.district_open_close_bar(
                district_df, title=f"{selected_industry} 자치구별 현황"
            )
            st.plotly_chart(fig, use_container_width=True)

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

    with tab_map:
        map_df = metrics.aggregate_for_map(
            snapshot_df, industry=selected_industry, districts=selected_districts
        )
        if map_df.empty or COLS.LAT not in map_df.columns:
            st.info(
                "지도를 표시하려면 **위치 좌표가 포함된 processed 데이터**가 필요합니다.\n\n"
                "`python run_pipeline.py` 로 수집·전처리하면 상권 TM 좌표가 "
                "WGS84 로 변환되어 지도에 표시됩니다."
            )
        else:
            year = metrics.quarter_year(selected_quarter) if selected_quarter else ""
            quarter_note = (
                f"{year} 기준 분기: **{metrics.format_quarter_short_label(selected_quarter)}** · "
                if selected_quarter
                else ""
            )
            st.caption(
                f"{quarter_note}"
                "상권 단위 점포 수 — 원 크기 ∝ 점포 수, "
                "색상: 파랑(저밀도) → 노랑 → 빨강(고밀도)"
            )
            deck = maps.store_density_deck(
                map_df, title=f"{selected_industry} 점포 밀도"
            )
            st.pydeck_chart(deck, use_container_width=True)

    with tab_trend:
        trend_df = data_loader.load_quarter_trend_data()
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
            st.info(
                "추이를 보려면 사이드바에서 **2개 이상 분기**를 선택하세요."
            )
        if trend_filtered.empty:
            st.warning("조건에 해당하는 분기 데이터가 없습니다.")
        elif n_quarters >= 2:
            fig = charts.industry_trend_line(
                trend_filtered,
                title=f"{selected_industry} 분기별 추이 ({n_quarters}개 분기)",
            )
            st.plotly_chart(fig, use_container_width=True)


# Streamlit 은 `streamlit run` 시 이 스크립트를 __main__ 으로 실행하므로
# 별도의 else 분기(import 부수효과) 없이 표준 가드만으로 충분하다.
if __name__ == "__main__":
    main()
