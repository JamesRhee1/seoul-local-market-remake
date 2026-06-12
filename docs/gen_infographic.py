"""서울시 상권 분석 대시보드 — 아키텍처 인포그래픽 SVG 생성기.

코드 기반이라 화살표 연결·방향·라벨이 결정론적으로 보장된다.
좌표를 수정하고 재실행하면 즉시 재생성된다.

사용법:
    python docs/gen_infographic.py

출력:
    docs/architecture.svg  (README용 PNG는 별도 export 또는 동봉 파일 사용)
"""
from __future__ import annotations

from pathlib import Path

DOCS = Path(__file__).resolve().parent

W, H = 1920, 1080
parts = []


def add(s: str) -> None:
    parts.append(s)


def rrect(x, y, w, h, r, fill, stroke, sw=2, extra=""):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')


def text(x, y, s, size=20, weight="400", fill="#222", anchor="middle", family="Noto Sans CJK KR"):
    add(f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{s}</text>')


# ----------------------------------------------------------------------------
# 카드 (아이콘 + 제목 + 부제)
# ----------------------------------------------------------------------------

def card(x, y, w, h, title, sub, icon, icon_color):
    rrect(x, y, w, h, 14, "#FFFFFF", "#D8DEE6", 1.5,
          'filter="url(#cardshadow)"')
    icx, icy = x + 38, y + h / 2
    draw_icon(icon, icx, icy, icon_color)
    tx = x + 72 + (w - 72) / 2 - 10
    text(tx, y + h / 2 - 6, title, 21, "700", "#1F2937")
    text(tx, y + h / 2 + 22, sub, 16, "400", "#6B7280")


def draw_icon(kind, cx, cy, c):
    if kind == "cloud":
        add(f'<circle cx="{cx-8}" cy="{cy+3}" r="11" fill="none" stroke="{c}" stroke-width="3"/>')
        add(f'<circle cx="{cx+7}" cy="{cy-2}" r="13" fill="none" stroke="{c}" stroke-width="3"/>')
        add(f'<line x1="{cx-1}" y1="{cy-15}" x2="{cx-1}" y2="{cy+11}" stroke="{c}" stroke-width="2"/>')
        add(f'<ellipse cx="{cx-1}" cy="{cy-2}" rx="13" ry="6" fill="none" stroke="{c}" stroke-width="2"/>')
    elif kind == "doc":
        add(f'<path d="M {cx-11} {cy-15} h 15 l 7 7 v 23 h -22 z" fill="none" stroke="{c}" stroke-width="3" stroke-linejoin="round"/>')
        for i in range(3):
            add(f'<line x1="{cx-6}" y1="{cy-2+i*7}" x2="{cx+6}" y2="{cy-2+i*7}" stroke="{c}" stroke-width="2.5"/>')
    elif kind == "person":
        add(f'<circle cx="{cx}" cy="{cy-8}" r="7" fill="{c}"/>')
        add(f'<path d="M {cx-13} {cy+16} a 13 13 0 0 1 26 0 z" fill="{c}"/>')
    elif kind == "gear":
        add(f'<circle cx="{cx}" cy="{cy}" r="9" fill="none" stroke="{c}" stroke-width="4"/>')
        for a in range(0, 360, 45):
            add(f'<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy-17}" stroke="{c}" '
                f'stroke-width="4.5" transform="rotate({a} {cx} {cy})"/>')
        add(f'<circle cx="{cx}" cy="{cy}" r="9" fill="#FFFFFF" stroke="{c}" stroke-width="4"/>')
    elif kind == "download":
        add(f'<line x1="{cx}" y1="{cy-14}" x2="{cx}" y2="{cy+5}" stroke="{c}" stroke-width="4"/>')
        add(f'<path d="M {cx-8} {cy-2} L {cx} {cy+7} L {cx+8} {cy-2}" fill="none" stroke="{c}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
        add(f'<path d="M {cx-13} {cy+12} v 4 h 26 v -4" fill="none" stroke="{c}" stroke-width="3.5" stroke-linecap="round"/>')
    elif kind == "funnel":
        add(f'<path d="M {cx-13} {cy-13} h 26 l -10 14 v 13 l -6 -4 v -9 z" fill="{c}"/>')
    elif kind == "db":
        add(f'<ellipse cx="{cx}" cy="{cy-11}" rx="13" ry="5.5" fill="none" stroke="{c}" stroke-width="3"/>')
        add(f'<path d="M {cx-13} {cy-11} v 22 a 13 5.5 0 0 0 26 0 v -22" fill="none" stroke="{c}" stroke-width="3"/>')
        add(f'<path d="M {cx-13} {cy} a 13 5.5 0 0 0 26 0" fill="none" stroke="{c}" stroke-width="3"/>')
    elif kind == "files":
        add(f'<rect x="{cx-14}" y="{cy-13}" width="18" height="24" rx="3" fill="none" stroke="{c}" stroke-width="3"/>')
        add(f'<rect x="{cx-8}" y="{cy-8}" width="18" height="24" rx="3" fill="#FFFFFF" stroke="{c}" stroke-width="3"/>')
    elif kind == "pin":
        add(f'<path d="M {cx} {cy+14} C {cx-12} {cy} {cx-11} {cy-8} {cx} {cy-14} C {cx+11} {cy-8} {cx+12} {cy} {cx} {cy+14} z" fill="{c}"/>')
        add(f'<path d="M {cx-11} {cy-5} a 11 11 0 0 1 22 0 a 11 14 0 0 1 -11 17 a 11 14 0 0 1 -11 -17 z" fill="{c}"/>')
        add(f'<circle cx="{cx}" cy="{cy-4}" r="4.5" fill="#FFFFFF"/>')
    elif kind == "bars":
        for i, hgt in enumerate((12, 20, 16, 26)):
            add(f'<rect x="{cx-14+i*8}" y="{cy+13-hgt}" width="6" height="{hgt}" rx="1.5" fill="{c}"/>')
    elif kind == "line":
        add(f'<polyline points="{cx-14},{cy+9} {cx-5},{cy-2} {cx+2},{cy+4} {cx+13},{cy-10}" '
            f'fill="none" stroke="{c}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>')
        for px, py in ((cx-14, cy+9), (cx-5, cy-2), (cx+2, cy+4), (cx+13, cy-10)):
            add(f'<circle cx="{px}" cy="{py}" r="3" fill="{c}"/>')


# ----------------------------------------------------------------------------
# 화살표
# ----------------------------------------------------------------------------

def path(points, color, dash=None, marker=True, width=2.6):
    d = f'M {points[0][0]} {points[0][1]} ' + " ".join(f"L {x} {y}" for x, y in points[1:])
    dash_attr = f'stroke-dasharray="{dash}"' if dash else ""
    mk = f'marker-end="url(#arr_{color.strip("#")})"' if marker else ""
    add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" {dash_attr} {mk}/>')


ARROW_COLORS = ["#333333", "#34A853", "#F4A100", "#00ACC1", "#888888"]

# ----------------------------------------------------------------------------
# 문서 시작
# ----------------------------------------------------------------------------
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add('<defs>')
for c in ARROW_COLORS:
    add(f'<marker id="arr_{c.strip("#")}" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{c}"/></marker>')
add('<filter id="cardshadow" x="-10%" y="-10%" width="120%" height="130%">'
    '<feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.08"/></filter>')
add('</defs>')

add(f'<rect width="{W}" height="{H}" fill="#FAFBFC"/>')
text(W / 2, 64, "서울시 상권 분석 대시보드 — 데이터 파이프라인", 40, "800", "#111827")

# ----------------------------------------------------------------------------
# 패널
# ----------------------------------------------------------------------------
PANEL_Y, PANEL_H = 110, 830
panels = [
    (30, 260, "외부", "#EDF3FE", "#4285F4"),
    (310, 450, "ETL 파이프라인", "#EAF6EC", "#34A853"),
    (780, 320, "데이터 저장소 (Parquet)", "#FEF7E0", "#E8A100"),
    (1120, 440, "분석", "#E2F6F9", "#00ACC1"),
    (1580, 310, "대시보드", "#212B36", "#212B36"),
]
for x, w, name, fill, border in panels:
    rrect(x, PANEL_Y, w, PANEL_H, 18, fill, border, 2)
    tcol = "#FFFFFF" if fill == "#212B36" else border
    text(x + w / 2, PANEL_Y + 44, name, 25, "800", tcol)

# ----------------------------------------------------------------------------
# 외부
# ----------------------------------------------------------------------------
card(55, 200, 210, 105, "서울 열린데이터", "상권 API", "cloud", "#4285F4")
card(55, 430, 210, 105, "환경설정", ".env / Secrets", "doc", "#4285F4")
card(55, 660, 210, 105, "사용자", "브라우저", "person", "#4285F4")

# ----------------------------------------------------------------------------
# ETL
# ----------------------------------------------------------------------------
card(340, 185, 400, 85, "run_pipeline.py", "오케스트레이터", "gear", "#34A853")
card(340, 330, 240, 92, "collector", "수집", "download", "#34A853")
card(340, 490, 240, 92, "preprocessor", "병합·정제", "funnel", "#34A853")
card(600, 560, 142, 84, "geo", "좌표 변환", "pin", "#9AA3AE")
card(340, 660, 240, 92, "sample_data", "샘플 생성", "db", "#34A853")

# ----------------------------------------------------------------------------
# 데이터 저장소
# ----------------------------------------------------------------------------
card(820, 300, 240, 92, "raw", "수집 원본", "db", "#E8A100")
card(820, 470, 240, 92, "processed", "분기 스냅샷", "files", "#E8A100")
card(820, 650, 240, 92, "sample", "데모용", "db", "#E8A100")

# ----------------------------------------------------------------------------
# 분석
# ----------------------------------------------------------------------------
card(1170, 195, 240, 88, "data_loader", "로딩 · 폴백", "db", "#00ACC1")
card(1170, 355, 240, 88, "metrics", "KPI · 집계", "bars", "#00ACC1")
card(1158, 512, 178, 88, "charts", "차트", "line", "#00ACC1")
card(1352, 512, 178, 88, "maps", "지도", "pin", "#00ACC1")
card(1170, 690, 240, 88, "report", "README 갱신", "doc", "#00ACC1")
# README 미니 아이콘
draw_icon("doc", 1492, 734, "#00ACC1")
text(1492, 772, "README.md", 14, "600", "#00838F")

# ----------------------------------------------------------------------------
# 대시보드 목업
# ----------------------------------------------------------------------------
rrect(1608, 195, 254, 650, 16, "#FFFFFF", "#37414C", 2)
text(1735, 232, "Streamlit app", 20, "700", "#1F2937")
# 상단 점 3개
for i, c in enumerate(("#FF5F57", "#FEBC2E", "#28C840")):
    add(f'<circle cx="{1630 + i * 18}" cy="{252}" r="5" fill="{c}"/>')
# 탭
tabs = [("현황", True), ("추이", False), ("지도", False)]
for i, (t, active) in enumerate(tabs):
    tx = 1622 + i * 78
    rrect(tx, 268, 72, 34, 8, "#2E6BE6" if active else "#EEF1F5", "#2E6BE6" if active else "#D8DEE6", 1)
    text(tx + 36, 291, t, 16, "700", "#FFFFFF" if active else "#4B5563")
# 콘텐츠 미니 위젯 4칸
for (wx, wy) in ((1622, 318), (1746, 318), (1622, 520), (1746, 520)):
    rrect(wx, wy, 116, 186, 10, "#F6F8FA", "#E2E7ED", 1)
# 막대
for i, hgt in enumerate((52, 86, 66, 110)):
    add(f'<rect x="{1638 + i * 24}" y="{478 - hgt}" width="16" height="{hgt}" rx="3" fill="#3B82F6"/>')
# 라인
add('<polyline points="1758,460 1786,408 1812,432 1850,368" fill="none" stroke="#2E6BE6" stroke-width="4" stroke-linecap="round"/>')
for px, py in ((1758, 460), (1786, 408), (1812, 432), (1850, 368)):
    add(f'<circle cx="{px}" cy="{py}" r="4.5" fill="#2E6BE6"/>')
# 지도 핀
draw_icon("pin", 1680, 600, "#3B82F6")
add('<rect x="1632" y="540" width="96" height="150" rx="8" fill="#E8F0FE" opacity="0.5"/>')
draw_icon("pin", 1680, 600, "#3B82F6")
# 도넛
add('<circle cx="1804" cy="606" r="42" fill="none" stroke="#E2E7ED" stroke-width="18"/>')
add('<path d="M 1804 564 a 42 42 0 0 1 40 55" fill="none" stroke="#34A853" stroke-width="18"/>')
add('<path d="M 1844 619 a 42 42 0 0 1 -62 21" fill="none" stroke="#FBBC04" stroke-width="18"/>')
add('<path d="M 1782 640 a 42 42 0 0 1 -16 -52" fill="none" stroke="#4285F4" stroke-width="18"/>')

# ----------------------------------------------------------------------------
# 화살표 — 데이터 흐름 (실선 검정)
# ----------------------------------------------------------------------------
path([(265, 252), (305, 252), (305, 376), (340, 376)], "#333333")          # API → collector (엘보)
path([(580, 346), (820, 346)], "#333333")                                  # collector → raw
path([(940, 392), (940, 442), (500, 442), (500, 490)], "#333333")          # raw → preprocessor
path([(580, 536), (820, 536)], "#333333")                                  # preprocessor → processed
path([(1060, 516), (1108, 516), (1108, 239), (1170, 239)], "#333333")      # processed → data_loader
path([(1290, 283), (1290, 355)], "#333333")                                # data_loader → metrics
path([(1247, 443), (1247, 512)], "#333333")                                # metrics → charts
path([(1333, 443), (1441, 443), (1441, 512)], "#333333")                   # metrics → maps
path([(1530, 556), (1608, 556)], "#333333")                                # maps → app
path([(1247, 600), (1247, 636), (1608, 636)], "#333333")                   # charts → app

# ----------------------------------------------------------------------------
# 제어 흐름 (초록 점선) — run_pipeline → collector / preprocessor / report
# ----------------------------------------------------------------------------
path([(440, 270), (440, 330)], "#34A853", dash="7 6")
path([(660, 270), (660, 462), (530, 462), (530, 490)], "#34A853", dash="7 6")
path([(700, 185), (700, 176), (1140, 176), (1140, 734), (1170, 734)], "#34A853", dash="7 6")

# ----------------------------------------------------------------------------
# 보조 흐름
# ----------------------------------------------------------------------------
# geo 보조 (회색 점선, preprocessor와 연결)
path([(600, 602), (520, 582)], "#888888", dash="5 5", marker=False, width=2.2)
# 샘플 생성 (주황 점선): processed → sample_data → sample
path([(820, 556), (752, 556), (752, 700), (580, 700)], "#F4A100", dash="7 6")
path([(580, 724), (820, 724)], "#F4A100", dash="7 6")
# 폴백 (청록 점선): sample → data_loader
path([(1060, 696), (1088, 696), (1088, 263), (1170, 263)], "#00ACC1", dash="7 6")
# report → README (청록 점선)
path([(1410, 734), (1462, 734)], "#00ACC1", dash="7 6")

# ----------------------------------------------------------------------------
# 범례 + 배지
# ----------------------------------------------------------------------------
LY = 1006
add(f'<line x1="60" y1="{LY}" x2="104" y2="{LY}" stroke="#333333" stroke-width="3"/>')
text(112, LY + 6, "데이터 흐름", 17, "600", "#374151", anchor="start")
add(f'<line x1="240" y1="{LY}" x2="284" y2="{LY}" stroke="#34A853" stroke-width="3" stroke-dasharray="7 6"/>')
text(292, LY + 6, "제어 (오케스트레이터)", 17, "600", "#374151", anchor="start")
add(f'<line x1="498" y1="{LY}" x2="542" y2="{LY}" stroke="#F4A100" stroke-width="3" stroke-dasharray="7 6"/>')
text(550, LY + 6, "샘플 생성", 17, "600", "#374151", anchor="start")
add(f'<line x1="660" y1="{LY}" x2="704" y2="{LY}" stroke="#00ACC1" stroke-width="3" stroke-dasharray="7 6"/>')
text(712, LY + 6, "샘플 폴백 · 문서 갱신", 17, "600", "#374151", anchor="start")

badges = [("pytest", "#7C3AED", "#F3EEFD"), ("ruff", "#0E9F6E", "#E8F7F0"),
          ("GitHub Actions CI", "#2563EB", "#EAF1FE"), ("Parquet", "#D97706", "#FDF3E3")]
bx = 1180
for label, fg, bg in badges:
    bw = 64 + len(label) * 11
    rrect(bx, LY - 24, bw, 48, 24, bg, fg, 1.5)
    add(f'<circle cx="{bx + 26}" cy="{LY}" r="8" fill="{fg}"/>')
    text(bx + 44, LY + 7, label, 18, "700", fg, anchor="start")
    bx += bw + 24

add('</svg>')


def main() -> None:
    svg_path = DOCS / "architecture.svg"
    svg_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"SVG 생성 완료: {svg_path} ({svg_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
