"""
generate_pdf.py -- Chekin Sales Business Case PDF Generator v4
Usage: python generate_pdf.py <input_json> <output_pdf>
Requires: fpdf2
"""
import json, sys, re, math
from fpdf import FPDF
from fpdf.enums import XPos, YPos

# ── Colours ───────────────────────────────────────────────────────────
NAVY       = (10,  28,  66)
TEAL       = (0,  124, 112)
TEAL_LIGHT = (232, 247, 245)
WHITE      = (255, 255, 255)
DARK       = (18,  24,  38)
GRAY       = (90, 100, 118)
GRAY_LIGHT = (210, 215, 225)
ROW_ALT    = (238, 241, 248)
KPI_BG     = (235, 248, 246)

# ── Layout (mm) ───────────────────────────────────────────────────────
LM, RM = 15, 15
PW = 210
CW = 180          # content width
PAD = 6
IW = 168          # inner width

SECTION_LABELS = {
    "current_state": ("01", "Where We Are"),
    "target_state":  ("02", "Where We Want to Be"),
    "strategy":      ("03", "How We Get There"),
    "resources":     ("04", "What We Need"),
    "roi":           ("05", "Expected ROI"),
}

TABLE_COLS = {
    "strategy":  [82, 36, 32, 18],
    "resources": [52, 28, 36, 30, 22],
    "roi":       [42, 18, 26, 32, 28, 22],
    "timeline":  [30, 34, 104],
}


def san(text):
    t = str(text)
    for u, a in {"\u2014":" - ","\u2013":" - ","\u2018":"'","\u2019":"'",
                 "\u201c":'"',"\u201d":'"',"\u2022":"-","\u00b7":"|"}.items():
        t = t.replace(u, a)
    return t.encode("latin-1", errors="replace").decode("latin-1")


def strip_chart(text):
    return re.sub(r'\[CHART SUGGESTION:[^\]]*\]', '', text).strip()

def has_funnel(text):
    m = re.search(r'\[CHART SUGGESTION:([^\]]*)\]', text)
    return bool(m and "funnel" in m.group(1).lower())


# ─────────────────────────────────────────────────────────────────────

class PDF(FPDF):

    def __init__(self, title, author, date):
        super().__init__()
        self.doc_title  = san(title)
        self.doc_author = san(author)
        self.doc_date   = san(date)
        self.set_margins(LM, LM, RM)
        self.set_auto_page_break(True, 18)

    # ── chrome ───────────────────────────────────────────────────────

    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*NAVY)
        self.rect(0, 0, PW, 5, "F")
        self.set_xy(LM, 8)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*GRAY)
        self.cell(0, 4, self.doc_title.upper())
        self.set_y(16)

    def footer(self):
        self.set_y(-13)
        self.set_draw_color(*GRAY_LIGHT)
        self.set_line_width(0.25)
        self.line(LM, self.get_y(), PW - RM, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*GRAY)
        self.cell(0, 4,
            san(f"Chekin  |  Confidential  |  {self.doc_date}  |  Page {self.page_no()-1}"),
            align="C")

    # ── cover ────────────────────────────────────────────────────────

    def cover_page(self):
        self.add_page()
        self.set_fill_color(*NAVY)
        self.rect(0, 0, PW, 118, "F")
        self.set_fill_color(*TEAL)
        self.rect(0, 118, PW, 2.5, "F")

        self.set_xy(LM, 28)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(120, 155, 210)
        self.cell(0, 5, "CHEKIN  --  BUSINESS CASE")

        self.set_xy(LM, 40)
        self.set_font("Helvetica", "B", 22)
        self.set_text_color(*WHITE)
        self.multi_cell(CW, 11, self.doc_title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_x(LM)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(160, 195, 240)
        self.cell(0, 7, san(f"{self.doc_author}   |   {self.doc_date}"))

        # Presented-to card
        cy = 133
        self.set_fill_color(246, 247, 250)
        self.set_draw_color(*GRAY_LIGHT)
        self.set_line_width(0.3)
        self.rect(LM, cy, CW, 30, "FD")
        self.set_fill_color(*TEAL)
        self.rect(LM, cy, 3, 30, "F")
        self.set_xy(LM + 8, cy + 6)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 5, "PRESENTED TO")
        self.set_xy(LM + 8, cy + 13)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*DARK)
        self.cell(0, 6, "Carlos (CEO)   |   Gianluca (Director of Operations)")
        self.set_xy(LM + 8, cy + 21)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 5, "ROI & lean OPEX  /  Predictability & structured timelines")

    # ── section header ───────────────────────────────────────────────

    def _sec_header(self, num, title):
        self.ln(6)
        if self.get_y() > 250:
            self.add_page()
        y = self.get_y()
        self.set_fill_color(*NAVY)
        self.rect(LM, y, CW, 10, "F")
        self.set_fill_color(*TEAL)
        self.rect(LM, y, 12, 10, "F")
        self.set_xy(LM, y)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*WHITE)
        self.cell(12, 10, san(num), align="C")
        self.set_xy(LM + 15, y + 1.5)
        self.set_font("Helvetica", "B", 11)
        self.cell(CW - 15, 7, san(title))
        self.set_y(y + 12)

    # ── KPI cards ────────────────────────────────────────────────────

    def _kpi_row(self, kpis):
        """Draw a row of KPI metric cards."""
        self.ln(4)
        n     = len(kpis)
        gap   = 4
        card_w = (IW - gap * (n - 1)) / n
        card_h = 24
        y = self.get_y()
        x = LM + PAD

        for i, kpi in enumerate(kpis):
            cx = x + i * (card_w + gap)
            # card background
            self.set_fill_color(*KPI_BG)
            self.set_draw_color(*TEAL)
            self.set_line_width(0.5)
            self.rect(cx, y, card_w, card_h, "FD")
            # top teal bar
            self.set_fill_color(*TEAL)
            self.rect(cx, y, card_w, 3, "F")
            # value (large)
            self.set_xy(cx, y + 5)
            self.set_font("Helvetica", "B", 15)
            self.set_text_color(*NAVY)
            self.cell(card_w, 9, san(str(kpi["value"])), align="C")
            # label
            self.set_xy(cx, y + 15)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(*GRAY)
            self.cell(card_w, 6, san(str(kpi["label"])), align="C")

        self.set_y(y + card_h + 5)

    # ── bullets ──────────────────────────────────────────────────────

    def _bullets(self, bullets):
        self.set_font("Helvetica", "", 9.5)
        self.set_text_color(*DARK)
        for b in bullets:
            text = strip_chart(b)
            if not text:
                continue
            y = self.get_y()
            if self.will_page_break(6):
                self.add_page()
                y = self.get_y()
            self.set_fill_color(*TEAL)
            self.ellipse(LM + PAD + 0.5, y + 3.2, 1.8, 1.8, "F")
            self.set_xy(LM + PAD + 5, y)
            self.multi_cell(IW - 5, 5.5, san(text),
                            new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1.5)

    # ── highlight ────────────────────────────────────────────────────

    def _highlight(self, text):
        self.ln(3)
        self.set_font("Helvetica", "B", 9.5)
        lines = max(1, math.ceil(
            self.get_string_width(san(text)) / max(IW - 14, 1)))
        bh = lines * 6.5 + 8
        if self.will_page_break(bh + 4):
            self.add_page()
        y = self.get_y()
        self.set_fill_color(*TEAL_LIGHT)
        self.set_draw_color(*TEAL)
        self.set_line_width(0.3)
        self.rect(LM + PAD, y, IW, bh, "FD")
        self.set_fill_color(*TEAL)
        self.rect(LM + PAD, y, 3, bh, "F")
        self.set_xy(LM + PAD + 7, y + 4)
        self.set_text_color(*NAVY)
        self.set_auto_page_break(False)
        self.multi_cell(IW - 12, 6.5, san(text),
                        new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_auto_page_break(True, 18)
        self.set_y(y + bh + 2)

    # ── table ────────────────────────────────────────────────────────

    def _table(self, headers, rows, col_widths=None):
        n = len(headers)
        if not col_widths or len(col_widths) != n:
            base = IW // n
            col_widths = [base] * n
            col_widths[-1] = IW - base * (n - 1)

        x0   = LM + PAD
        HP   = 3      # horizontal padding
        VP   = 2      # vertical padding
        FS   = 8.5
        LH   = 5.0

        def est_lines(txt, cw):
            self.set_font("Helvetica", "", FS)
            inner = max(cw - HP * 2, 1)
            return max(1, math.ceil(self.get_string_width(san(str(txt))) / inner))

        def row_h(row):
            return max(est_lines(t, w) for t, w in zip(row, col_widths)) * LH + VP * 2

        # ── header row
        hh = max(est_lines(h, w) for h, w in zip(headers, col_widths)) * LH + VP * 2
        hh = max(hh, 9)
        if self.will_page_break(hh + 2):
            self.add_page()
        y = self.get_y()
        self.set_fill_color(*NAVY)
        self.rect(x0, y, sum(col_widths), hh, "F")
        self.set_auto_page_break(False)
        x = x0
        for hdr, cw in zip(headers, col_widths):
            self.set_xy(x + HP, y + VP)
            self.set_font("Helvetica", "B", FS)
            self.set_text_color(*WHITE)
            self.multi_cell(cw - HP * 2, LH, san(str(hdr)), align="C",
                            new_x=XPos.RIGHT, new_y=YPos.TOP)
            x += cw
        self.set_auto_page_break(True, 18)
        self.set_y(y + hh)

        # ── data rows
        for ri, row in enumerate(rows):
            rh = max(row_h(row), 8)
            if self.will_page_break(rh + 2):
                self.add_page()
            y = self.get_y()
            is_total = san(str(row[0])).strip().upper() == "TOTAL"
            bg = TEAL_LIGHT if is_total else (ROW_ALT if ri % 2 == 0 else WHITE)
            # background
            self.set_fill_color(*bg)
            self.rect(x0, y, sum(col_widths), rh, "F")
            # bottom border
            self.set_draw_color(*GRAY_LIGHT)
            self.set_line_width(0.2)
            self.line(x0, y + rh, x0 + sum(col_widths), y + rh)
            # cell text -- disable auto_page_break to prevent mid-row breaks
            self.set_auto_page_break(False)
            self.set_text_color(*DARK)   # explicit reset before row
            x = x0
            for ci, (cell, cw) in enumerate(zip(row, col_widths)):
                self.set_xy(x + HP, y + VP)
                self.set_font("Helvetica", "B" if is_total else "", FS)
                self.set_text_color(*(NAVY if is_total else DARK))
                self.multi_cell(cw - HP * 2, LH, san(str(cell)),
                                align="L" if ci == 0 else "C",
                                new_x=XPos.RIGHT, new_y=YPos.TOP)
                x += cw
            self.set_auto_page_break(True, 18)
            self.set_y(y + rh)   # always advance exactly rh

        # outer bottom border
        self.set_draw_color(*GRAY_LIGHT)
        self.set_line_width(0.35)
        self.line(x0, self.get_y(), x0 + sum(col_widths), self.get_y())
        self.ln(5)

    # ── funnel chart ─────────────────────────────────────────────────

    def _funnel(self, stages):
        """Stacked funnel bars with down-arrow connectors."""
        BAR_H  = 13
        GAP    = 5
        MIN_W  = 0.30
        colors = [NAVY, TEAL, (0, 92, 82)]
        total  = BAR_H * len(stages) + GAP * (len(stages) - 1)
        if self.will_page_break(total + 10):
            self.add_page()
        self.ln(3)
        top = self.get_y()
        mx  = stages[0][0]

        for i, (val, label) in enumerate(stages):
            pct = val / mx
            bw  = IW * (MIN_W + (1 - MIN_W) * pct)
            bx  = LM + PAD + (IW - bw) / 2
            y   = top + i * (BAR_H + GAP)

            # bar
            self.set_fill_color(*colors[i])
            self.rect(bx, y, bw, BAR_H, "F")
            # text
            self.set_auto_page_break(False)
            self.set_xy(bx, y + 2)
            self.set_font("Helvetica", "B", 9.5)
            self.set_text_color(*WHITE)
            self.cell(bw, BAR_H - 4, san(f"{val:,}   {label}"), align="C")
            self.set_auto_page_break(True, 18)

            # arrow connector
            if i < len(stages) - 1:
                mx2 = LM + PAD + IW / 2
                ay  = y + BAR_H
                self.set_fill_color(*GRAY_LIGHT)
                self.rect(mx2 - 2.5, ay, 5, GAP - 2, "F")
                self.polygon([
                    (mx2 - 5,  ay + GAP - 2),
                    (mx2 + 5,  ay + GAP - 2),
                    (mx2,      ay + GAP + 1),
                ], style="F")

        self.set_y(top + total + 4)

    # ── section card ─────────────────────────────────────────────────

    def section_card(self, key, data):
        num, title = SECTION_LABELS.get(key, ("--", key))
        bullets    = data.get("bullets", [])
        table      = data.get("table")
        highlight  = data.get("highlight", "")
        kpis       = data.get("kpis")

        self._sec_header(num, title)

        # KPI metric cards (if provided)
        if kpis:
            self._kpi_row(kpis)

        if bullets:
            self._bullets(bullets)

        # funnel chart if any bullet requests it
        if any(has_funnel(b) for b in bullets) and key == "current_state":
            self._funnel([
                (350, "Leads Worked"),
                (41,  "Demos Booked"),
                (15,  "Deals Created"),
            ])

        if table:
            self.ln(2)
            self._table(table["headers"], table["rows"], TABLE_COLS.get(key))

        if highlight:
            self._highlight(highlight)

    # ── timeline ─────────────────────────────────────────────────────

    def timeline_section(self, rows):
        self._sec_header(">>", "If Approved -- Execution Timeline")
        self.ln(1)
        self._table(["Week", "Dates", "Action"], rows, TABLE_COLS["timeline"])


# ─────────────────────────────────────────────────────────────────────

def generate(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    pdf = PDF(
        title=data.get("title", "Sales Business Case"),
        author=data.get("author", "Alessandro - Head of Sales, Chekin"),
        date=data.get("date", "2026"),
    )

    pdf.cover_page()
    pdf.add_page()

    sections = data.get("sections", {})
    for key in ["current_state", "target_state", "strategy", "resources", "roi"]:
        if key in sections:
            pdf.section_card(key, sections[key])

    timeline = data.get("execution_timeline")
    if timeline:
        pdf.timeline_section(timeline)

    pdf.output(output_path)
    print(f"PDF saved to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_pdf.py <input_json> <output_pdf>")
        sys.exit(1)
    generate(sys.argv[1], sys.argv[2])
