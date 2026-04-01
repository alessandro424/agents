"""
generate_pptx.py — Chekin Sales Business Case PowerPoint Generator
Usage: python generate_pptx.py <input_json> <output_pptx>
Requires: python-pptx (pip install python-pptx)
Auto-installs python-pptx if not present.
"""

import sys
import subprocess

def ensure_pptx():
    try:
        import pptx  # noqa
    except ImportError:
        print("Installing python-pptx...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "python-pptx", "-q"])
        print("Done.")

ensure_pptx()

import json
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

# Chekin brand colors
BLUE = RGBColor(30, 90, 180)
DARK = RGBColor(20, 30, 50)
LIGHT_BG = RGBColor(245, 247, 252)
ACCENT = RGBColor(60, 160, 120)
WHITE = RGBColor(255, 255, 255)
MID_GRAY = RGBColor(100, 110, 130)
LIGHT_GRAY = RGBColor(220, 225, 235)

SLIDE_W = Inches(13.33)
SLIDE_H = Inches(7.5)

SECTION_TITLES = {
    "current_state": "1. Where We Are",
    "target_state": "2. Where We Want to Be",
    "strategy": "3. How We Get There",
    "resources": "4. What We Need",
    "roi": "5. Expected ROI",
}


def rgb(r, g, b):
    return RGBColor(r, g, b)


def add_rect(slide, left, top, width, height, fill_color, line_color=None):
    from pptx.util import Emu
    shape = slide.shapes.add_shape(
        1,  # MSO_SHAPE_TYPE.RECTANGLE
        left, top, width, height
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(0.5)
    else:
        shape.line.fill.background()
    return shape


def add_textbox(slide, text, left, top, width, height,
                font_size=14, bold=False, color=None, align=PP_ALIGN.LEFT,
                italic=False, word_wrap=True):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = word_wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(font_size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color or DARK
    return txBox


def cover_slide(prs, data):
    slide_layout = prs.slide_layouts[6]  # blank
    slide = prs.slides.add_slide(slide_layout)

    # Background
    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, LIGHT_BG)

    # Left blue panel (40% width)
    panel_w = Inches(5.2)
    add_rect(slide, 0, 0, panel_w, SLIDE_H, BLUE)

    # "BUSINESS CASE" label
    add_textbox(slide, "BUSINESS CASE", Inches(0.4), Inches(1.0),
                Inches(4.4), Inches(0.5), font_size=10, bold=True,
                color=RGBColor(160, 200, 240), align=PP_ALIGN.LEFT)

    # Title
    add_textbox(slide, data.get("title", "Sales Business Case"),
                Inches(0.4), Inches(1.7), Inches(4.4), Inches(2.5),
                font_size=26, bold=True, color=WHITE, align=PP_ALIGN.LEFT)

    # Author + date
    add_textbox(slide, data.get("author", "Alessandro — Head of Sales, Chekin"),
                Inches(0.4), Inches(5.5), Inches(4.4), Inches(0.4),
                font_size=9, color=RGBColor(180, 210, 240))
    add_textbox(slide, data.get("date", ""),
                Inches(0.4), Inches(5.9), Inches(4.4), Inches(0.4),
                font_size=9, color=RGBColor(180, 210, 240))

    # Right panel: "Presented to"
    add_textbox(slide, "Presented to", Inches(5.8), Inches(2.5),
                Inches(7.0), Inches(0.4), font_size=10, bold=True, color=MID_GRAY)
    add_textbox(slide, "Carlos (CEO)  ·  Gianluca (Director of Operations)",
                Inches(5.8), Inches(3.0), Inches(7.0), Inches(0.5),
                font_size=12, color=DARK)

    # Accent line under "Presented to"
    add_rect(slide, Inches(5.8), Inches(2.45), Inches(6.5), Inches(0.03), BLUE)


def content_slide(prs, section_key, section_data):
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)

    # Background
    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, WHITE)

    # Top blue bar
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.08), BLUE)

    # Section title
    title = SECTION_TITLES.get(section_key, section_key)
    add_textbox(slide, title, Inches(0.5), Inches(0.25),
                Inches(12.0), Inches(0.6), font_size=18, bold=True, color=BLUE)

    # Blue accent line under title
    add_rect(slide, Inches(0.5), Inches(0.9), Inches(12.3), Inches(0.03), BLUE)

    content_top = Inches(1.05)
    content_height = Inches(5.2)
    content_left = Inches(0.5)
    content_width = Inches(12.3)

    bullets = section_data.get("bullets", [])
    table_data = section_data.get("table")
    highlight = section_data.get("highlight", "")

    # If we have a table, split vertically: bullets left, table right (or stack)
    if table_data and bullets:
        _render_bullets_left(slide, bullets, content_top)
        _render_table_right(slide, table_data, content_top)
    elif table_data:
        _render_table_full(slide, table_data, content_top)
    elif bullets:
        _render_bullets_full(slide, bullets, content_top)

    # Highlight box at bottom
    if highlight:
        highlight_top = Inches(6.35)
        box = add_rect(slide, Inches(0.5), highlight_top,
                       Inches(12.3), Inches(0.75), LIGHT_BG, BLUE)
        add_textbox(slide, f"  {highlight}",
                    Inches(0.55), highlight_top + Inches(0.1),
                    Inches(12.2), Inches(0.6),
                    font_size=9, bold=True, color=BLUE)

    # Footer
    add_textbox(slide, "Chekin — Confidential",
                Inches(0.5), Inches(7.2), Inches(6.0), Inches(0.3),
                font_size=7, color=MID_GRAY)


def _render_bullets_full(slide, bullets, top):
    from pptx.util import Inches, Pt
    txBox = slide.shapes.add_textbox(Inches(0.5), top, Inches(12.3), Inches(5.0))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"•  {bullet}"
        p.font.size = Pt(13)
        p.font.color.rgb = DARK
        p.space_after = Pt(8)


def _render_bullets_left(slide, bullets, top):
    from pptx.util import Inches, Pt
    txBox = slide.shapes.add_textbox(Inches(0.5), top, Inches(5.5), Inches(5.0))
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = f"•  {bullet}"
        p.font.size = Pt(11)
        p.font.color.rgb = DARK
        p.space_after = Pt(6)


def _render_table_right(slide, table_data, top):
    headers = table_data["headers"]
    rows = table_data["rows"]
    cols = len(headers)
    left = Inches(6.2)
    width = Inches(6.6)
    col_w = width / cols
    row_h = Inches(0.42)

    # Header row
    for i, h in enumerate(headers):
        add_rect(slide, left + col_w * i, top, col_w, row_h, BLUE)
        add_textbox(slide, h, left + col_w * i + Inches(0.05), top + Inches(0.07),
                    col_w - Inches(0.1), row_h,
                    font_size=9, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    for ri, row in enumerate(rows):
        bg = LIGHT_BG if ri % 2 == 0 else WHITE
        y = top + row_h * (ri + 1)
        for ci, cell in enumerate(row):
            add_rect(slide, left + col_w * ci, y, col_w, row_h, bg)
            add_textbox(slide, str(cell),
                        left + col_w * ci + Inches(0.05), y + Inches(0.07),
                        col_w - Inches(0.1), row_h,
                        font_size=9, color=DARK, align=PP_ALIGN.CENTER)


def _render_table_full(slide, table_data, top):
    headers = table_data["headers"]
    rows = table_data["rows"]
    cols = len(headers)
    left = Inches(0.5)
    width = Inches(12.3)
    col_w = width / cols
    row_h = Inches(0.45)

    for i, h in enumerate(headers):
        add_rect(slide, left + col_w * i, top, col_w, row_h, BLUE)
        add_textbox(slide, h, left + col_w * i + Inches(0.05), top + Inches(0.08),
                    col_w - Inches(0.1), row_h,
                    font_size=9, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    for ri, row in enumerate(rows):
        bg = LIGHT_BG if ri % 2 == 0 else WHITE
        y = top + row_h * (ri + 1)
        for ci, cell in enumerate(row):
            add_rect(slide, left + col_w * ci, y, col_w, row_h, bg)
            add_textbox(slide, str(cell),
                        left + col_w * ci + Inches(0.05), y + Inches(0.08),
                        col_w - Inches(0.1), row_h,
                        font_size=9, color=DARK, align=PP_ALIGN.CENTER)


def timeline_slide(prs, timeline_rows):
    slide_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(slide_layout)

    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, WHITE)
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.08), BLUE)

    add_textbox(slide, "If Approved — Execution Timeline",
                Inches(0.5), Inches(0.25), Inches(12.0), Inches(0.6),
                font_size=18, bold=True, color=BLUE)
    add_rect(slide, Inches(0.5), Inches(0.9), Inches(12.3), Inches(0.03), BLUE)

    headers = ["Week", "Dates", "Action"]
    col_widths = [Inches(1.2), Inches(2.0), Inches(9.1)]
    top = Inches(1.05)
    row_h = Inches(0.5)

    for i, h in enumerate(headers):
        x = Inches(0.5) + sum(col_widths[:i])
        add_rect(slide, x, top, col_widths[i], row_h, BLUE)
        add_textbox(slide, h, x + Inches(0.05), top + Inches(0.08),
                    col_widths[i] - Inches(0.1), row_h,
                    font_size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

    for ri, row in enumerate(timeline_rows):
        bg = LIGHT_BG if ri % 2 == 0 else WHITE
        y = top + row_h * (ri + 1)
        for ci, cell in enumerate(row):
            x = Inches(0.5) + sum(col_widths[:ci])
            add_rect(slide, x, y, col_widths[ci], row_h, bg)
            align = PP_ALIGN.CENTER if ci < 2 else PP_ALIGN.LEFT
            add_textbox(slide, str(cell), x + Inches(0.08), y + Inches(0.08),
                        col_widths[ci] - Inches(0.1), row_h,
                        font_size=10, color=DARK, align=align)

    add_textbox(slide, "Chekin — Confidential",
                Inches(0.5), Inches(7.2), Inches(6.0), Inches(0.3),
                font_size=7, color=MID_GRAY)


def generate(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    cover_slide(prs, data)

    section_order = ["current_state", "target_state", "strategy", "resources", "roi"]
    sections = data.get("sections", {})
    for key in section_order:
        if key in sections:
            content_slide(prs, key, sections[key])

    # Execution timeline slide (optional)
    timeline = data.get("execution_timeline")
    if timeline:
        timeline_slide(prs, timeline)

    prs.save(output_path)
    print(f"PPTX saved to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_pptx.py <input_json> <output_pptx>")
        sys.exit(1)
    generate(sys.argv[1], sys.argv[2])
