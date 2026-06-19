"""README 인사이트 섹션 자동 생성기.

processed(또는 sample) 데이터에서 핵심 지표를 계산해 마크다운을 만들고,
README.md 의 마커 구간(AUTO-INSIGHTS:START ~ END)을 교체한다.
전처리(`preprocessor.run`)가 끝날 때마다 호출되어 README가 항상 최신 데이터를 반영한다.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from . import config, data_loader
from .metrics import format_quarter_label
from .utils import get_logger

logger = get_logger(__name__)
C = config.COLS

START_MARKER = "<!-- AUTO-INSIGHTS:START -->"
END_MARKER = "<!-- AUTO-INSIGHTS:END -->"

_BIG_STORE_THRESHOLD = 500  # 폐업률 비교 시 표본이 너무 작은 업종 제외

# 성장/쇠퇴 표 하단 각주 — AUTO-INSIGHTS 재생성 시에도 유지
_GROWTH_NET_FOOTNOTE = (
    "> ※ 순증 수치는 서울 열린데이터 광장 원천 분류 기준 집계로, "
    "업종 코드 재분류·원천 입력 방식의 영향이 있을 수 있어 "
    "이상치 가능성을 함께 고려하세요."
)


def _n(x: float | int) -> str:
    return f"{int(round(float(x))):,}"


def _signed(x: float | int) -> str:
    v = int(round(float(x)))
    return f"+{v:,}" if v >= 0 else f"−{abs(v):,}"  # U+2212 minus


def _josa(word: str, with_batchim: str, without_batchim: str) -> str:
    """한글 받침 유무에 따라 알맞은 조사(만)를 반환한다 (예: 은/는, 이/가)."""
    if not word:
        return without_batchim
    last = word[-1]
    if "가" <= last <= "힣":
        has_batchim = (ord(last) - 0xAC00) % 28 != 0
        return with_batchim if has_batchim else without_batchim
    return without_batchim


def _industry_stats(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(C.INDUSTRY).agg(
        open=(C.OPEN_CO, "sum"),
        close=(C.CLOSE_CO, "sum"),
        store=(C.STORE_CO, "sum"),
    )
    g["net"] = g["open"] - g["close"]
    return g


def _representative_industry(df: pd.DataFrame, stats: pd.DataFrame) -> str:
    for name in df[C.INDUSTRY].unique():
        if isinstance(name, str) and config.DEFAULT_INDUSTRY_KEYWORD in name:
            return name
    return stats["store"].idxmax()


def _latest_quarter_only(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """여러 분기가 섞여 있으면 최신 분기만 남긴다 (순수 함수).

    분기 구분 없이 합산하면 개업/폐업이 분기 수만큼 부풀어 인사이트가
    왜곡되므로, 항상 단일(최신) 분기 기준으로 계산한다.

    Returns:
        (필터링된 DataFrame, 분기 라벨)
    """
    if C.QUARTER not in df.columns:
        return df, "N/A"
    quarters = sorted(str(q) for q in df[C.QUARTER].dropna().unique())
    if not quarters:
        return df, "N/A"
    latest = quarters[-1]
    filtered = df[df[C.QUARTER].astype(str) == latest]
    return filtered, latest


def _warn_if_insight_quarter_outside_demo(latest_quarter: str) -> None:
    """인사이트 기준 분기가 문서 안내(DEMO_QUARTERS)와 다르면 경고만 남긴다."""
    if latest_quarter in ("N/A", ""):
        return
    if latest_quarter not in config.DEMO_QUARTERS:
        demo = ", ".join(config.DEMO_QUARTERS)
        logger.warning(
            "문서 안내 분기(DEMO_QUARTERS)와 인사이트 기준 분기가 다릅니다: "
            "인사이트=%s, DEMO_QUARTERS=[%s]",
            format_quarter_label(latest_quarter),
            demo,
        )


def build_insights_markdown(df: pd.DataFrame) -> str:
    """데이터프레임에서 인사이트 마크다운 본문을 생성한다 (순수 함수)."""
    df, q_label = _latest_quarter_only(df)
    _warn_if_insight_quarter_outside_demo(q_label)
    stats = _industry_stats(df)
    growth = stats.sort_values("net", ascending=False).head(3)
    decline = stats.sort_values("net").head(3)

    big = stats[stats["store"] >= _BIG_STORE_THRESHOLD].copy()
    big["rate"] = big["close"] / big["store"] * 100
    closure = big.sort_values("rate", ascending=False).head(3)

    rep = _representative_industry(df, stats)
    rep_df = df[df[C.INDUSTRY] == rep]
    rep_dist = (
        rep_df.groupby(C.DISTRICT)
        .agg(store=(C.STORE_CO, "sum"), open=(C.OPEN_CO, "sum"), close=(C.CLOSE_CO, "sum"))
    )
    rep_dist["net"] = rep_dist["open"] - rep_dist["close"]
    rep_dist["activity"] = rep_dist["open"] + rep_dist["close"]
    # 대시보드 막대 차트와 동일: 활동량(개업+폐업) 내림차순
    rep_top = rep_dist.sort_values("activity", ascending=False).head(3)
    store_leader = rep_dist.sort_values("store", ascending=False).index[0]

    n_districts = df[C.DISTRICT].nunique()
    n_industries = df[C.INDUSTRY].nunique()
    n_areas = df[C.TRDAR_CD_NM].nunique() if C.TRDAR_CD_NM in df.columns else 0
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 입지 인사이트: 활동량 상위 자치구와 순증감 대비 (막대 차트 정렬과 정합)
    top_name = rep_top.index[0]
    top_row = rep_top.iloc[0]
    neg_in_top = rep_top[rep_top["net"] < 0]

    lines: list[str] = []
    add = lines.append

    top_growth = growth.index[0]
    top_decline = decline.index[0]

    add(f"> 📂 아래 수치는 **실제 수집 데이터에서 자동 생성**되었습니다 — "
        f"**최신 분기 `{format_quarter_label(q_label)}` 기준**, 점포 **{_n(len(df))}행** · "
        f"{n_industries}개 업종 · "
        f"{n_districts}개 자치구 · {n_areas}개 상권. "
        f"_(생성: {generated_at}, `python -m src.report`)_")
    add("")

    add('### 1. 성장하는 업종 vs 쇠퇴하는 업종 — "지금 뜨는 시장 / 지는 시장"')
    add("")
    add("분기 내 **순증감(개업 − 폐업)** 으로 시장의 진입·철수 방향을 읽을 수 있습니다.")
    add("")
    add("| 순증가 상위 (성장) | 개업 | 폐업 | 순증 | | 순감소 상위 (쇠퇴) | 개업 | 폐업 | 순증 |")
    add("|---|--:|--:|--:|---|---|--:|--:|--:|")
    for (gi, gr), (di, dr) in zip(growth.iterrows(), decline.iterrows()):
        add(f"| {gi} | {_n(gr['open'])} | {_n(gr['close'])} | **{_signed(gr['net'])}** | "
            f"| {di} | {_n(dr['open'])} | {_n(dr['close'])} | **{_signed(dr['net'])}** |")
    add("")
    add(f"→ **인사이트:** 이번 분기 순증 1위는 **{top_growth}**({_signed(growth.iloc[0]['net'])}), "
        f"순감소 1위는 **{top_decline}**({_signed(decline.iloc[0]['net'])}). "
        f"신규 창업·투자라면 순증 업종에, 리스크 관리라면 순감소 업종에 주목하게 됩니다.")
    add("")
    add(_GROWTH_NET_FOOTNOTE)
    add("")

    add('### 2. 창업 리스크 — "여긴 들어가면 위험한 시장인가"')
    add("")
    add(f"점포 수 대비 폐업 비중(**폐업률**)으로 업종의 생존 난이도를 가늠합니다. "
        f"(점포 {_BIG_STORE_THRESHOLD}개 이상 업종 대상)")
    add("")
    add("| 업종 | 점포 수 | 폐업 | 폐업률 |")
    add("|---|--:|--:|--:|")
    for name, r in closure.iterrows():
        add(f"| {name} | {_n(r['store'])} | {_n(r['close'])} | **{r['rate']:.1f}%** |")
    add("")
    add("→ **인사이트:** 진입장벽이 낮은 프랜차이즈형 업종일수록 회전율(폐업률)이 높음 "
        "→ **과당경쟁·포화 신호**.")
    add("")

    add('### 3. 입지/경쟁 강도 — "이 업종은 어느 자치구에 집중되나"')
    add("")
    add(
        f"특정 업종을 선택하면 자치구별 점포·개업·폐업을 비교할 수 있습니다 "
        f"(대시보드 막대 차트와 동일하게 **활동량=개업+폐업** 상위 순). 예: **{rep}**"
    )
    add("")
    add("| 자치구 | 점포 수 | 개업 | 폐업 | 순증 |")
    add("|---|--:|--:|--:|--:|")
    for name, r in rep_top.iterrows():
        add(f"| {name} | {_n(r['store'])} | {_n(r['open'])} | {_n(r['close'])} "
            f"| **{_signed(r['net'])}** |")
    add("")
    if top_row["net"] < 0:
        add(
            f"→ **인사이트:** 활동량 1위 **{top_name}**{_josa(top_name, '은', '는')} "
            f"개업 {_n(top_row['open'])}·폐업 {_n(top_row['close'])}로 거래가 가장 활발하지만 "
            f"순증 {_signed(top_row['net'])} — "
            f"\"활동이 많다 = 좋은 입지\"가 아니라 **활동량과 순증감을 함께 봐야** 합니다."
        )
    elif not neg_in_top.empty:
        contrast_name = neg_in_top["net"].idxmin()
        contrast_net = neg_in_top.loc[contrast_name, "net"]
        store_note = (
            f" (점포 수 1위는 **{store_leader}**)"
            if store_leader != top_name
            else ""
        )
        add(
            f"→ **인사이트:** 활동량 1위 **{top_name}**{_josa(top_name, '은', '는')} "
            f"순증 {_signed(top_row['net'])}{store_note}인 반면, "
            f"**{contrast_name}**{_josa(contrast_name, '은', '는')} "
            f"순증 {_signed(contrast_net)}로 폐업이 개업을 앞섭니다 — "
            f"막대 차트의 활동량 순서만으로 입지를 판단하기보다 "
            f"**순증감을 함께 확인**해야 합니다."
        )
    else:
        add(
            f"→ **인사이트:** 활동량 상위 **{top_name}**{_josa(top_name, '은', '는')} "
            f"순증 {_signed(top_row['net'])} — "
            f"활동이 많은 자치구라도 분기별 순증감을 함께 확인해야 합니다."
        )

    return "\n".join(lines)


def update_readme(df: pd.DataFrame | None = None, readme_path: Path | None = None) -> bool:
    """README 의 마커 구간을 최신 인사이트로 교체한다. 성공 시 True."""
    readme_path = readme_path or (config.ROOT_DIR / "README.md")

    if df is None:
        path, source = data_loader.resolve_data_path()
        if path is None:
            logger.warning("데이터가 없어 README 자동 갱신을 건너뜁니다.")
            return False
        df = data_loader.load_market_data(path)
        logger.info("README 인사이트 생성용 데이터 출처: %s (%d행)", source, len(df))

    if not readme_path.exists():
        logger.warning("README 를 찾을 수 없습니다: %s", readme_path)
        return False

    text = readme_path.read_text(encoding="utf-8")
    if START_MARKER not in text or END_MARKER not in text:
        logger.warning("README 에 AUTO-INSIGHTS 마커가 없어 갱신을 건너뜁니다.")
        return False

    body = build_insights_markdown(df)
    new_block = f"{START_MARKER}\n\n{body}\n\n{END_MARKER}"
    new_text = re.sub(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        lambda _: new_block,
        text,
        flags=re.S,
    )
    readme_path.write_text(new_text, encoding="utf-8")
    logger.info("README 인사이트 섹션 갱신 완료: %s", readme_path)
    return True


if __name__ == "__main__":
    update_readme()
