"""Streamlit 대시보드 진입점.

모든 도메인 로직은 src 패키지에 위임하고, 이 파일은 UI 조립만 담당한다.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src import charts, config, data_loader, metrics

COLS = config.COLS

st.set_page_config(
    page_title="서울시 로컬 상권 분석",
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


def main() -> None:
    path, source = data_loader.resolve_data_path()
    if path is None:
        df = pd.DataFrame()
    else:
        df = get_data(str(path), path.stat().st_mtime)

    st.title("🛒 서울시 로컬 상권 분석 대시보드")
    st.caption("Source: 서울 열린데이터 광장 (Seoul Open Data Plaza)")

    if df.empty:
        st.error(
            "표시할 데이터가 없습니다.\n\n"
            "1) `python -m src.collector` 로 수집 → `python -m src.preprocessor` 로 전처리하거나,\n"
            "2) `data/sample/` 에 샘플 CSV 를 두고 다시 실행하세요."
        )
        st.stop()

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

    filtered = metrics.filter_data(df, industry=selected_industry, districts=selected_districts)

    # --- KPI ---
    st.subheader(f"'{selected_industry}' 상권 현황")
    kpi = metrics.compute_kpi(filtered)
    c1, c2, c3 = st.columns(3)
    c1.metric("총 점포 수", f"{kpi.total_stores:,}개")
    c2.metric("신규 개업", f"{kpi.total_open:,}개", delta=kpi.total_open)
    c3.metric("폐업", f"{kpi.total_close:,}개", delta=-kpi.total_close, delta_color="inverse")

    st.divider()

    # --- 차트 ---
    st.subheader("📊 자치구별 개업 vs 폐업")
    district_df = metrics.aggregate_by_district(filtered)
    if district_df.empty:
        st.warning("조건에 해당하는 데이터가 없습니다.")
    else:
        fig = charts.district_open_close_bar(
            district_df, title=f"{selected_industry} 자치구별 현황"
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- 원본 데이터 ---
    with st.expander("📄 원본 데이터 보기"):
        view_cols = [
            c
            for c in [COLS.TRDAR_CD_NM, COLS.DISTRICT, COLS.STORE_CO, COLS.OPEN_CO, COLS.CLOSE_CO]
            if c in filtered.columns
        ]
        st.dataframe(filtered[view_cols], use_container_width=True)


# Streamlit 은 `streamlit run` 시 이 스크립트를 __main__ 으로 실행하므로
# 별도의 else 분기(import 부수효과) 없이 표준 가드만으로 충분하다.
if __name__ == "__main__":
    main()
