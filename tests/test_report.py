import logging

import pandas as pd

from src import config
from src.report import (
    END_MARKER,
    START_MARKER,
    build_insights_markdown,
    update_readme,
)

C = config.COLS


def _df():
    return pd.DataFrame(
        {
            C.QUARTER: [20254] * 6,
            C.INDUSTRY: ["커피-음료", "커피-음료", "한식음식점", "편의점", "편의점", "일반의류"],
            C.DISTRICT: ["강남구", "서초구", "중구", "강남구", "마포구", "중구"],
            C.TRDAR_CD_NM: ["A", "B", "C", "D", "E", "F"],
            C.STORE_CO: [600, 300, 50, 700, 200, 40],
            C.OPEN_CO: [50, 40, 1, 5, 3, 1],
            C.CLOSE_CO: [10, 5, 0, 60, 20, 30],
        }
    )


def test_build_insights_contains_tables_and_scope():
    md = build_insights_markdown(_df())
    assert "### 1. 성장하는 업종" in md
    assert "### 2. 창업 리스크" in md
    assert "### 3. 입지/경쟁 강도" in md
    assert "개업" in md and "폐업률" in md
    # 대표 업종은 커피-음료가 우선 선택되어야 함
    assert "커피-음료" in md


def test_representative_industry_prefers_coffee():
    md = build_insights_markdown(_df())
    assert "예: **커피-음료**" in md


def test_update_readme_replaces_markers(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(
        f"# 제목\n\n{START_MARKER}\n오래된 내용\n{END_MARKER}\n\n## 다음 섹션\n",
        encoding="utf-8",
    )
    ok = update_readme(df=_df(), readme_path=readme)
    assert ok is True
    text = readme.read_text(encoding="utf-8")
    assert "오래된 내용" not in text
    assert START_MARKER in text and END_MARKER in text
    assert "## 다음 섹션" in text  # 마커 밖 내용은 보존
    assert text.count(START_MARKER) == 1  # 마커 중복 생성 방지


def test_update_readme_no_marker_returns_false(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# 마커 없음\n", encoding="utf-8")
    assert update_readme(df=_df(), readme_path=readme) is False


def test_multi_quarter_uses_latest_only():
    """여러 분기가 섞이면 최신 분기만으로 인사이트를 만들어야 한다.

    과거 분기를 합산하면 개업/폐업 수가 부풀어 왜곡되므로,
    구분기 전용 업종이 결과에 나타나지 않는지 확인한다.
    """
    old = _df().assign(**{C.QUARTER: 20251, C.INDUSTRY: "구분기전용업종"})
    multi = pd.concat([old, _df()], ignore_index=True)

    md = build_insights_markdown(multi)

    assert "`2025-4분기`" in md     # 최신 분기가 헤더에 명시됨
    assert "구분기전용업종" not in md  # 과거 분기 데이터는 제외됨
    # 최신 분기 단독 결과와 동일해야 한다 (생성 시각 줄 제외)
    def strip(text: str) -> str:
        return "\n".join(line for line in text.splitlines() if "생성:" not in line)

    single = build_insights_markdown(_df())
    assert strip(md) == strip(single)


def test_warns_when_insight_quarter_outside_demo_quarters(caplog):
    """DEMO_QUARTERS 밖 분기가 최신이면 경고만 출력하고 인사이트는 생성한다."""
    df = _df().assign(**{C.QUARTER: 20261})

    with caplog.at_level(logging.WARNING, logger="src.report"):
        md = build_insights_markdown(df)

    assert "`2026-1분기`" in md
    assert any("DEMO_QUARTERS" in r.message and "다릅니다" in r.message for r in caplog.records)
