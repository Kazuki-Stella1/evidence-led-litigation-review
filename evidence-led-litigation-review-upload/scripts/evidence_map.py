#!/usr/bin/env python3
"""Generate a diagonal evidence timeline as self-contained SVG and HTML."""

from __future__ import annotations

import argparse
import html
import json
import textwrap
from pathlib import Path

from evidence_model import EvidenceError, annotation_lines, load_json, parse_event_date


SIDE_COLORS = {
    "self": ("#1b73e8", "#eaf3ff", "自分側"),
    "opponent": ("#d65f32", "#fff0e9", "相手方"),
    "neutral": ("#667085", "#f2f4f7", "中立・その他"),
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def wrapped_lines(value: object, width: int, max_lines: int) -> list[str]:
    normalized = " ".join(str(value).split())
    if not normalized:
        return []
    lines = textwrap.wrap(
        normalized,
        width=width,
        break_long_words=True,
        break_on_hyphens=False,
    )
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1][:-1] + "…" if len(lines[-1]) > 1 else "…"
    return lines


def svg_text(x: float, y: float, lines: list[str], css_class: str, line_height: int = 22) -> str:
    if not lines:
        return ""
    spans = [f'<tspan x="{x:.1f}" y="{y:.1f}">{esc(lines[0])}</tspan>']
    spans.extend(
        f'<tspan x="{x:.1f}" dy="{line_height}">{esc(line)}</tspan>'
        for line in lines[1:]
    )
    return f'<text class="{css_class}">{"".join(spans)}</text>'


def evidence_card_text(item: dict, x: float, y: float) -> list[str]:
    annotations = item.get("annotations", {})
    result = [svg_text(x, y, wrapped_lines(item.get("title"), 21, 2), "card-title", 25)]
    cursor = y + 54
    sections = (
        ("事実", "facts", "field facts"),
        ("立証趣旨", "proves", "field proves"),
        ("因果関係", "causation", "field causation"),
        ("矛盾点", "contradictions", "field contradictions"),
        ("推論", "inferences", "field inferences"),
        ("法的評価", "legal_evaluation", "field legal"),
    )
    for label, key, css_class in sections:
        values = annotation_lines(annotations, key)
        value = values[0] if values else "未記載"
        lines = wrapped_lines(f"{label}: {value}", 30, 2)
        result.append(svg_text(x, cursor, lines, css_class, 20))
        cursor += 21 * len(lines) + 4
    return [value for value in result if value]


def source_card_text(item: dict, x: float, y: float, side_label: str) -> list[str]:
    result = [
        svg_text(x, y, [side_label], "side-label"),
        svg_text(x, y + 32, [str(item.get("id") or "未記載")], "evidence-id"),
        svg_text(x, y + 65, [str(item.get("event_date") or "日付未記載")], "evidence-date"),
        svg_text(x, y + 94, wrapped_lines(item.get("title"), 24, 2), "source-title", 23),
    ]
    meta_y = y + 145
    result.append(
        svg_text(
            x,
            meta_y,
            wrapped_lines(
                f"頁 {item.get('source_pages') or '未記載'} / 精度 {item.get('precision_status') or '未確認'}",
                47,
                2,
            ),
            "source-meta",
            20,
        )
    )
    return [value for value in result if value]


def render_svg(index: dict) -> str:
    events = [item for item in index.get("items", []) if item.get("event_date")]
    for item in events:
        item["_date"] = parse_event_date(item["event_date"])
    events.sort(key=lambda item: (item["_date"], item.get("id", "")))
    if not events:
        raise EvidenceError("No dated items are available for the evidence map")

    width = 1680
    gap = 390
    height = max(1160, 520 + gap * (len(events) - 1))
    top_y = 120
    bottom_y = height - 220
    x_bottom = 650
    x_top = 980
    axis_span = bottom_y - top_y

    def axis_x(y: float) -> float:
        fraction = (bottom_y - y) / axis_span if axis_span else 0
        return x_bottom + fraction * (x_top - x_bottom)

    defs = """
<defs>
  <marker id="arrow" markerWidth="12" markerHeight="12" refX="10" refY="5" orient="auto">
    <path d="M0,0 L10,5 L0,10 z" fill="#64c4e8"/>
  </marker>
</defs>
"""
    style = """
<style>
  .canvas { fill: #f8fafc; }
  .axis { stroke: #64c4e8; stroke-width: 14; stroke-linecap: round; }
  .month-tick { stroke: #0e7490; stroke-width: 4; }
  .month-label { fill: #0e5268; font: 700 23px system-ui, sans-serif; }
  .connector { stroke-width: 3; fill: none; opacity: .75; }
  .node { stroke-width: 5; fill: #ffffff; }
  .card { stroke-width: 2; }
  .left-card { fill: #ffffff; stroke: #d0d5dd; }
  .right-card { stroke-width: 2; }
  text { font-family: "Noto Sans CJK JP", "Noto Sans JP", "Yu Gothic", "Hiragino Sans", sans-serif; }
  .card-title { fill: #101828; font-size: 22px; font-weight: 800; }
  .field { fill: #344054; font-size: 16px; }
  .proves { fill: #05603a; }
  .causation { fill: #175cd3; }
  .contradictions { fill: #b42318; }
  .inferences { fill: #7a5af8; }
  .legal { fill: #6941c6; }
  .side-label { font-size: 17px; font-weight: 800; }
  .evidence-id { fill: #101828; font-size: 29px; font-weight: 850; }
  .evidence-date { fill: #101828; font-size: 22px; font-weight: 750; }
  .source-title { fill: #101828; font-size: 19px; font-weight: 650; }
  .source-meta { fill: #475467; font-size: 15px; }
  .legend { font: 18px system-ui, sans-serif; fill: #344054; }
  .title { font: 800 38px system-ui, sans-serif; fill: #101828; }
  .subtitle { font: 20px system-ui, sans-serif; fill: #475467; }
  .event.hidden { display: none; }
</style>
"""
    parts = [
        f'<svg id="evidence-map-svg" xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        defs,
        style,
        f'<rect class="canvas" width="{width}" height="{height}"/>',
        f'<text x="42" y="55" class="title">{esc(index.get("case_title") or index.get("case_id"))}</text>',
        '<text x="42" y="88" class="subtitle">左：事実・因果関係・矛盾・立証趣旨・法的評価　／　右：号証・日時・原資料</text>',
        f'<line class="axis" x1="{x_bottom}" y1="{bottom_y}" x2="{x_top}" y2="{top_y}" marker-end="url(#arrow)"/>',
    ]

    legend_x = width - 540
    for offset, side in enumerate(("self", "opponent", "neutral")):
        color, _, label = SIDE_COLORS[side]
        x = legend_x + offset * 175
        parts.extend(
            [
                f'<circle cx="{x}" cy="58" r="10" fill="{color}"/>',
                f'<text x="{x + 17}" y="64" class="legend">{esc(label)}</text>',
            ]
        )

    seen_months: set[str] = set()
    for position, item in enumerate(events):
        y = bottom_y - position * gap
        x = axis_x(y)
        side = item.get("side", "neutral")
        color, pale, side_label = SIDE_COLORS.get(side, SIDE_COLORS["neutral"])
        month = item["_date"].strftime("%Y-%m")
        month_label = f"{item['_date'].year}年{item['_date'].month:02d}月"
        if month not in seen_months:
            seen_months.add(month)
            parts.extend(
                [
                    f'<line class="month-tick" x1="{x - 48:.1f}" y1="{y - 14}" x2="{x + 48:.1f}" y2="{y + 14}"/>',
                    f'<rect x="{x - 65:.1f}" y="{y + 27}" width="130" height="34" rx="17" fill="#f8fafc" opacity="0.96"/>',
                    f'<text x="{x:.1f}" y="{y + 52}" text-anchor="middle" class="month-label">{esc(month_label)}</text>',
                ]
            )

        left_x = 38
        left_width = 535
        left_height = 350
        left_y = y - left_height / 2
        right_x = x + 62
        right_width = min(500, width - right_x - 32)
        right_height = 218
        right_y = y - right_height / 2
        left_text = evidence_card_text(item, left_x + 18, left_y + 31)
        right_text = source_card_text(item, right_x + 19, right_y + 27, side_label)
        parts.extend(
            [
                f'<g class="event" data-side="{esc(side)}" data-month="{esc(month)}">',
                f'<line class="connector" stroke="{color}" x1="{left_x + left_width}" y1="{y}" x2="{x - 18:.1f}" y2="{y}"/>',
                f'<line class="connector" stroke="{color}" x1="{x + 18:.1f}" y1="{y}" x2="{right_x}" y2="{y}"/>',
                f'<rect class="card left-card" x="{left_x}" y="{left_y:.1f}" width="{left_width}" height="{left_height}" rx="18"/>',
                *left_text,
                f'<rect class="card right-card" fill="{pale}" stroke="{color}" x="{right_x:.1f}" y="{right_y:.1f}" width="{right_width:.1f}" height="{right_height}" rx="18"/>',
                f'<rect x="{right_x + 14:.1f}" y="{right_y + 12:.1f}" width="116" height="27" rx="13.5" fill="#ffffff" opacity="0.72"/>',
                f'<g style="fill:{color}">{"".join(right_text)}</g>',
                f'<circle class="node" stroke="{color}" cx="{x:.1f}" cy="{y}" r="17"/>',
                "</g>",
            ]
        )
    parts.append("</svg>")
    return "\n".join(parts)


def render_html(index: dict, svg: str) -> str:
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(index.get('case_title') or index.get('case_id'))} — 証拠マップ</title>
<style>
body {{ margin: 0; background: #eef2f6; color: #101828; font-family: system-ui, sans-serif; }}
.toolbar {{ position: sticky; top: 0; z-index: 2; display: flex; gap: 10px; align-items: center; padding: 12px 20px; background: rgba(255,255,255,.96); border-bottom: 1px solid #d0d5dd; }}
.toolbar strong {{ margin-right: 10px; }}
button {{ border: 1px solid #98a2b3; background: white; border-radius: 999px; padding: 8px 15px; cursor: pointer; font-weight: 700; }}
button.active {{ background: #101828; color: white; border-color: #101828; }}
.map {{ max-width: 1680px; margin: 20px auto; box-shadow: 0 10px 35px rgba(16,24,40,.12); overflow: auto; background: white; }}
.map svg {{ display: block; min-width: 1180px; width: 100%; height: auto; }}
.notice {{ max-width: 1640px; margin: 14px auto 28px; padding: 0 20px; color: #475467; }}
@media print {{ .toolbar, .notice {{ display: none; }} .map {{ margin: 0; box-shadow: none; }} }}
</style>
</head>
<body>
<div class="toolbar">
  <strong>表示</strong>
  <button class="active" data-filter="all">すべて</button>
  <button data-filter="self">自分側</button>
  <button data-filter="opponent">相手方</button>
  <button data-filter="neutral">中立・その他</button>
</div>
<div class="map">{svg}</div>
<p class="notice">この図は証拠テキスト台帳のナビゲーションです。重要な引用、日時、金額、署名、画像内容及び争点は元ファイルで確認してください。</p>
<script>
for (const button of document.querySelectorAll('button[data-filter]')) {{
  button.addEventListener('click', () => {{
    const filter = button.dataset.filter;
    document.querySelectorAll('button[data-filter]').forEach(item => item.classList.toggle('active', item === button));
    document.querySelectorAll('.event').forEach(event => event.classList.toggle('hidden', filter !== 'all' && event.dataset.side !== filter));
  }});
}}
</script>
</body>
</html>
"""


def build_map(index_path: Path, out_html: Path, out_svg: Path | None = None) -> dict:
    index = load_json(index_path)
    svg = render_svg(index)
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(render_html(index, svg), encoding="utf-8")
    if out_svg:
        out_svg.parent.mkdir(parents=True, exist_ok=True)
        out_svg.write_text(svg, encoding="utf-8")
    count = sum(1 for item in index.get("items", []) if item.get("event_date"))
    return {"events": count, "html": str(out_html), "svg": str(out_svg) if out_svg else None}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--html", type=Path, required=True)
    parser.add_argument("--svg", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = build_map(args.index, args.html, args.svg)
    except EvidenceError as exc:
        print(f"Evidence map failed: {exc}")
        return 2
    print(f"Mapped {result['events']} dated item(s).")
    print(result["html"])
    if result["svg"]:
        print(result["svg"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
