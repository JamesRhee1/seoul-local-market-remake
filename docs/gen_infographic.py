"""아키텍처 인포그래픽(v3) SVG/PNG 생성 스크립트.

사용법:
    python docs/gen_infographic.py

출력:
    docs/architecture.svg  — 벡터 원본 (1920×1080)
    docs/architecture.png  — README용 래스터 (1920×1080)

PNG 변환은 Pillow 로 SVG 를 직접 렌더링한다(추가 런타임 의존성 없음).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DOCS = Path(__file__).resolve().parent
W, H = 1920, 1080

# README Mermaid classDef 색상과 동일
COLORS = {
    "source": ("#E8F0FE", "#4285F4"),
    "collect": ("#E6F4EA", "#34A853"),
    "store": ("#FEF7E0", "#FBBC04"),
    "process": ("#FCE8E6", "#EA4335"),
    "load": ("#F3E8FD", "#A142F4"),
    "analyze": ("#E0F7FA", "#00ACC1"),
    "dashboard": ("#212121", "#000000"),
    "bg": ("#FAFAFA", "#DDDDDD"),
    "text": "#1a1a1a",
    "text_light": "#ffffff",
    "dash": "#666666",
}


def _svg_header() -> str:
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">\n'
        f'<rect width="{W}" height="{H}" fill="{COLORS["bg"][0]}"/>\n'
    )


def _svg_footer() -> str:
    return "</svg>\n"


def _svg_rect(x, y, w, h, fill, stroke, rx=12, sw=2) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>\n'
    )


def _svg_text(
    x, y, lines: list[str], size=16, fill="#1a1a1a", anchor="middle", weight="normal"
) -> str:
    out = f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" '
    out += f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">\n'
    for i, line in enumerate(lines):
        dy = 0 if i == 0 else size + 4
        out += f'<tspan x="{x}" dy="{dy}">{line}</tspan>\n'
    out += "</text>\n"
    return out


def _svg_line(x1, y1, x2, y2, dashed=False, color="#333", sw=2) -> str:
    dash = ' stroke-dasharray="8,6"' if dashed else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
        f'stroke-width="{sw}" marker-end="url(#arrow)"{dash}/>\n'
    )


def build_svg() -> str:
    svg = _svg_header()
    svg += (
        "<defs>\n"
        '<marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto">\n'
        '<path d="M0,0 L8,3 L0,6 Z" fill="#333"/>\n'
        "</marker>\n"
        "</defs>\n"
    )

    svg += _svg_text(
        W // 2, 48, ["서울시 상권 분석 대시보드 — 데이터 파이프라인"], size=28, weight="bold"
    )

    # 5개 계층 밴드 (좌→우)
    bands = [
        ("외부", "source", 40, ["서울 API", ".env", "사용자"]),
        ("ETL", "collect", 400, ["run_pipeline", "collector", "preprocessor", "geo"]),
        ("저장소", "store", 760, ["storage.py", "raw", "processed", "sample"]),
        ("분석", "analyze", 1120, ["data_loader", "metrics", "charts", "maps", "report"]),
        ("대시보드", "dashboard", 1480, ["app.py", "3탭: 현황/추이/지도"]),
    ]
    bw, bh = 320, 820
    by = 100
    cx_list = []
    for title, key, bx, nodes in bands:
        fill, stroke = COLORS[key]
        svg += _svg_rect(bx, by, bw, bh, fill, stroke)
        text_fill = COLORS["text_light"] if key == "dashboard" else COLORS["text"]
        svg += _svg_text(bx + bw // 2, by + 36, [title], size=20, fill=text_fill, weight="bold")
        ny = by + 80
        for node in nodes:
            inner_fill = "#ffffff" if key != "dashboard" else "#333333"
            inner_stroke = stroke
            svg += _svg_rect(bx + 24, ny, bw - 48, 52, inner_fill, inner_stroke, rx=8)
            svg += _svg_text(bx + bw // 2, ny + 32, [node], size=15, fill=text_fill)
            ny += 68
        cx_list.append(bx + bw // 2)

    for i in range(len(cx_list) - 1):
        svg += _svg_line(cx_list[i] + 160, by + bh // 2, cx_list[i + 1] - 160, by + bh // 2)

    # 오케스트레이터 제어 흐름 (점선)
    svg += _svg_line(cx_list[1], by + 120, cx_list[0], by + 200, dashed=True, color=COLORS["dash"])
    svg += _svg_text(
        (cx_list[0] + cx_list[1]) // 2, by + 100, ["제어"], size=13, fill=COLORS["dash"]
    )

    # 푸터
    footer_y = 980
    for label, fx in [("pytest", 420), ("ruff", 720), ("CI", 960), ("Parquet", 1200)]:
        svg += _svg_rect(fx - 60, footer_y, 120, 40, "#ffffff", "#cccccc", rx=8)
        svg += _svg_text(fx, footer_y + 26, [label], size=14)

    svg += _svg_text(
        W // 2,
        1040,
        ["다이어그램은 docs/gen_infographic.py 로 재생성 가능"],
        size=14,
        fill="#666666",
    )
    svg += _svg_footer()
    return svg


def _load_font(size: int):
    for name in ("DejaVuSans.ttf", "Arial.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_png(svg_path: Path, png_path: Path) -> None:
    """SVG 레이아웃과 동일한 구성을 Pillow 로 1920×1080 PNG 에 그린다."""
    img = Image.new("RGB", (W, H), COLORS["bg"][0])
    draw = ImageDraw.Draw(img)
    title_font = _load_font(28)
    band_font = _load_font(20)
    node_font = _load_font(15)
    small_font = _load_font(13)

    draw.text(
        (W // 2, 24),
        "서울시 상권 분석 대시보드 — 데이터 파이프라인",
        fill=COLORS["text"],
        font=title_font,
        anchor="mt",
    )

    bands = [
        ("외부", "source", 40, ["서울 API", ".env", "사용자"]),
        ("ETL", "collect", 400, ["run_pipeline", "collector", "preprocessor", "geo"]),
        ("저장소", "store", 760, ["storage.py", "raw", "processed", "sample"]),
        ("분석", "analyze", 1120, ["data_loader", "metrics", "charts", "maps", "report"]),
        ("대시보드", "dashboard", 1480, ["app.py", "3탭: 현황/추이/지도"]),
    ]
    bw, bh = 320, 820
    by = 100
    cx_list: list[int] = []

    for title, key, bx, nodes in bands:
        fill, stroke = COLORS[key]
        draw.rounded_rectangle(
            (bx, by, bx + bw, by + bh), radius=12, fill=fill, outline=stroke, width=2
        )
        text_fill = COLORS["text_light"] if key == "dashboard" else COLORS["text"]
        draw.text((bx + bw // 2, by + 20), title, fill=text_fill, font=band_font, anchor="mt")
        ny = by + 80
        for node in nodes:
            inner_fill = "#ffffff" if key != "dashboard" else "#333333"
            draw.rounded_rectangle(
                (bx + 24, ny, bx + bw - 24, ny + 52),
                radius=8,
                fill=inner_fill,
                outline=stroke,
                width=1,
            )
            draw.text((bx + bw // 2, ny + 26), node, fill=text_fill, font=node_font, anchor="mm")
            ny += 68
        cx_list.append(bx + bw // 2)

    for i in range(len(cx_list) - 1):
        y = by + bh // 2
        draw.line((cx_list[i] + 160, y, cx_list[i + 1] - 160, y), fill="#333333", width=2)

    draw.line((cx_list[1], by + 120, cx_list[0], by + 200), fill=COLORS["dash"], width=2)
    draw.text(
        ((cx_list[0] + cx_list[1]) // 2, by + 88),
        "제어",
        fill=COLORS["dash"],
        font=small_font,
        anchor="mm",
    )

    footer_y = 980
    for label, fx in [("pytest", 420), ("ruff", 720), ("CI", 960), ("Parquet", 1200)]:
        draw.rounded_rectangle(
            (fx - 60, footer_y, fx + 60, footer_y + 40), radius=8, fill="#ffffff", outline="#cccccc"
        )
        draw.text((fx, footer_y + 20), label, fill=COLORS["text"], font=small_font, anchor="mm")

    draw.text(
        (W // 2, 1030),
        "docs/gen_infographic.py 로 재생성 가능",
        fill="#666666",
        font=small_font,
        anchor="mm",
    )
    img.save(png_path, format="PNG", optimize=True)


def main() -> None:
    svg_path = DOCS / "architecture.svg"
    png_path = DOCS / "architecture.png"
    svg_path.write_text(build_svg(), encoding="utf-8")
    render_png(svg_path, png_path)
    print(f"Wrote {svg_path.name} ({svg_path.stat().st_size:,} bytes)")
    print(f"Wrote {png_path.name} ({png_path.stat().st_size:,} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
