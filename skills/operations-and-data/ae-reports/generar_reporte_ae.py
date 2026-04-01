"""
AE Performance Report
Usage:
  python generar_reporte_ae.py <won_csv> [pipeline_csv]

  won_csv      : CSV with Won + Ready to Buy amounts (Deal owner, Close Date - Monthly, (Sum) Amount)
  pipeline_csv : CSV with total pipeline generated (same format). Optional — conversion shown as N/A if missing.
"""
import csv, sys
from datetime import date
from fpdf import FPDF

# ── Config ────────────────────────────────────────────────────────────────────
QUOTAS = {
    "Antonio Garcia":       ("EUR", 1361.11),
    "Aris Iskandaryan":     ("EUR", 1562.50),
    "Florencia Gonzalez":   ("EUR",  694.00),
    "Florencia Torres":     ("GBP", 1000.00),
    "Giulia D":             ("EUR", 1154.83),
    "Joan Herrera":         ("EUR",  250.00),
    "Jorge Garcia del Rey": ("EUR",  250.00),
    "Jose Miguel Pena":     ("EUR",  694.44),
    "Pablo Alonso Sanchez": ("EUR",  250.00),
    "Pablo Calderon":       ("EUR",  625.00),
    "Rocco Del Bellino":    ("EUR",  250.00),
}
AES    = list(QUOTAS.keys())
MONTHS = [(2026, 1, "January"), (2026, 2, "February")]

# ── Read CSV ──────────────────────────────────────────────────────────────────
def strip_accents(t):
    """Normalize accented characters to ASCII equivalents for name matching."""
    return (t.replace('\xe1','a').replace('\xe9','e').replace('\xed','i')
             .replace('\xf3','o').replace('\xfa','u').replace('\xf1','n')
             .replace('\xc1','A').replace('\xc9','E').replace('\xcd','I')
             .replace('\xd3','O').replace('\xda','U').replace('\xd1','N'))

# Map from normalized name -> canonical name used in QUOTAS
CANON = {strip_accents(ae): ae for ae in QUOTAS}

def canon_name(raw):
    return CANON.get(strip_accents(raw.strip()), raw.strip())

def read_won_csv(path):
    """Won CSV: Deal owner | Close Date - Monthly (YYYY-MM-DD) | (Sum) Amount"""
    data = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            ae    = canon_name(row["Deal owner"])
            fecha = row["Close Date - Monthly"].strip()
            amt   = float(row["(Sum) Amount"].replace(",", "").strip() or 0)
            yr, mo = int(fecha[:4]), int(fecha[5:7])
            data[(ae, yr, mo)] = amt
    return data

def read_pipeline_csv(path):
    """Pipeline CSV: Deal owner | Close Date (YYYY-MM-DD HH:MM) | Amount | Deal ID — summed by month"""
    data = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            ae    = canon_name(row["Deal owner"])
            fecha = row["Close Date"].strip()[:7]   # YYYY-MM
            raw   = row["Amount"].replace(",", "").strip()
            try:    amt = float(raw)
            except: amt = 0.0
            yr, mo = int(fecha[:4]), int(fecha[5:7])
            key = (ae, yr, mo)
            data[key] = data.get(key, 0.0) + amt
    return data

# ── Load data (hardcoded for now; replace with read_csv() when running from CLI) ──
WON_DATA = {
    ("Antonio Garcia",       2026, 1):  790.66,  ("Antonio Garcia",       2026, 2): 2410.72,
    ("Aris Iskandaryan",     2026, 1): 1111.27,  ("Aris Iskandaryan",     2026, 2):  135.00,
    ("Florencia Gonzalez",   2026, 1):  179.79,  ("Florencia Gonzalez",   2026, 2):  641.35,
    ("Florencia Torres",     2026, 1):  636.00,  ("Florencia Torres",     2026, 2):  289.80,
    ("Giulia D",             2026, 1): 1715.83,  ("Giulia D",             2026, 2): 2423.00,
    ("Joan Herrera",         2026, 1):  145.23,  ("Joan Herrera",         2026, 2):  251.35,
    ("Jorge Garcia del Rey", 2026, 1):  118.84,  ("Jorge Garcia del Rey", 2026, 2):  128.16,
    ("Jose Miguel Pena",     2026, 1):  432.52,  ("Jose Miguel Pena",     2026, 2):  846.72,
    ("Pablo Alonso Sanchez", 2026, 1):   94.79,  ("Pablo Alonso Sanchez", 2026, 2):  191.64,
    ("Pablo Calderon",       2026, 1):  243.36,  ("Pablo Calderon",       2026, 2):  673.64,
    ("Rocco Del Bellino",    2026, 1):  202.26,  ("Rocco Del Bellino",    2026, 2):  566.05,
}

# Pipeline data (aggregated from pipeline CSV by month)
PIPELINE_DATA = {
    ("Antonio Garcia",       2026, 1): 1421.81, ("Antonio Garcia",       2026, 2): 2849.53,
    ("Aris Iskandaryan",     2026, 1): 2997.27, ("Aris Iskandaryan",     2026, 2): 5750.00,
    ("Florencia Gonzalez",   2026, 1):    0.00, ("Florencia Gonzalez",   2026, 2):    0.00,
    ("Florencia Torres",     2026, 1):  782.24, ("Florencia Torres",     2026, 2): 1036.80,
    ("Giulia D",             2026, 1): 2923.33, ("Giulia D",             2026, 2): 4186.50,
    ("Joan Herrera",         2026, 1):  208.38, ("Joan Herrera",         2026, 2):  398.65,
    ("Jorge Garcia del Rey", 2026, 1):    0.00, ("Jorge Garcia del Rey", 2026, 2):    0.00,
    ("Jose Miguel Pena",     2026, 1):    0.00, ("Jose Miguel Pena",     2026, 2):    0.00,
    ("Pablo Alonso Sanchez", 2026, 1):  219.40, ("Pablo Alonso Sanchez", 2026, 2):  262.97,
    ("Pablo Calderon",       2026, 1):    0.00, ("Pablo Calderon",       2026, 2):    0.00,
    ("Rocco Del Bellino",    2026, 1):  496.11, ("Rocco Del Bellino",    2026, 2): 1035.25,
}

# Override with CLI args if provided
if len(sys.argv) >= 2:
    WON_DATA = read_won_csv(sys.argv[1])
if len(sys.argv) >= 3:
    PIPELINE_DATA = read_pipeline_csv(sys.argv[2])

HAS_PIPELINE = bool(PIPELINE_DATA)

# ── Helpers ───────────────────────────────────────────────────────────────────
def c(v, cur="EUR"):
    p = "GBP" if cur == "GBP" else "EUR"
    return f"{p} {v:,.0f}"

def pct(earned, quota):
    return (earned / quota * 100) if quota else 0

def conv_str(won, pipeline):
    if not HAS_PIPELINE or pipeline == 0:
        return "N/A"
    return f"{won / pipeline * 100:.1f}%"

def s(text):
    return (text.replace('\u2014', '-').replace('\u2013', '-')
                .replace('\u2022', '*').replace('\u20ac', 'EUR')
                .replace('\u2500', '-'))

# ── Metrics ───────────────────────────────────────────────────────────────────
metrics = {}
for ae in AES:
    cur, quota = QUOTAS[ae]
    rows = []
    for yr, mo, lbl in MONTHS:
        earned   = WON_DATA.get((ae, yr, mo), 0.0)
        pipeline = PIPELINE_DATA.get((ae, yr, mo), 0.0)
        p        = pct(earned, quota)
        rows.append({
            "month": lbl, "earned": earned, "quota": quota,
            "pct": p, "diff": earned - quota, "reached": earned >= quota,
            "cur": cur, "pipeline": pipeline,
        })
    metrics[ae] = rows

def total_e(ae):  return sum(r["earned"]   for r in metrics[ae])
def total_p(ae):  return sum(r["pipeline"] for r in metrics[ae])
def avg_p(ae):    return sum(r["pct"]      for r in metrics[ae]) / len(MONTHS)
def overall_conv(ae):
    w = total_e(ae); p = total_p(ae)
    return (w / p * 100) if p > 0 else None

rank_e    = sorted(AES, key=total_e, reverse=True)
rank_pct  = sorted(AES, key=avg_p,   reverse=True)
rank_conv = sorted([ae for ae in AES if overall_conv(ae) is not None],
                   key=overall_conv, reverse=True) if HAS_PIPELINE else []

def box_color(p):
    if p >= 100: return (34, 160, 56)
    if p >= 80:  return (220, 160, 0)
    return (210, 48, 48)

# ── PDF ───────────────────────────────────────────────────────────────────────
class PDF(FPDF):
    def footer(self):
        self.set_y(-11)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(160)
        self.cell(0, 8, f"AE Performance Report  |  Jan - Feb 2026  |  Page {self.page_no()}", align="C")
        self.set_text_color(0)

pdf = PDF(orientation="L", unit="mm", format="A4")
pdf.set_margins(12, 12, 12)
pdf.set_auto_page_break(auto=True, margin=14)

def sec(title, w=0):
    pdf.set_fill_color(35, 35, 35)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(w or (pdf.w - 24), 7, f"  {title}", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(30, 30, 30)
    pdf.ln(2)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — Cover + Executive Summary
# ═══════════════════════════════════════════════════════════════════════════════
pdf.add_page()
pdf.set_fill_color(35, 35, 35)
pdf.rect(0, 0, pdf.w, 38, style="F")
pdf.set_y(8)
pdf.set_font("Helvetica", "B", 22)
pdf.set_text_color(255, 255, 255)
pdf.cell(0, 10, "AE PERFORMANCE REPORT", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 12)
pdf.set_text_color(200, 200, 200)
pdf.cell(0, 7, f"January - February 2026   |   Generated: {date.today().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
pdf.set_text_color(30)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — Quota Dashboard
# ═══════════════════════════════════════════════════════════════════════════════
pdf.add_page()
pdf.set_auto_page_break(auto=False)

sec("QUOTA ATTAINMENT DASHBOARD")

# Legend
ly = pdf.get_y()
for col, label, x in [((210,48,48), "< 80%  Below target", 12),
                       ((220,160,0), "80-99%  Near target",  80),
                       ((34,160,56), ">= 100%  Target hit",  148)]:
    pdf.set_fill_color(*col)
    pdf.rect(x, ly, 4, 4, style="F")
    pdf.set_xy(x+5, ly)
    pdf.set_font("Helvetica", "", 7.5)
    pdf.cell(60, 4, label)
pdf.ln(8)

BW, BH, BGAP, BCOLS = 62, 22, 3, 4

for yr, mo, mlabel in MONTHS:
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(30)
    pdf.cell(0, 5, mlabel, new_x="LMARGIN", new_y="NEXT")
    start_y = pdf.get_y() + 1
    start_x = 12

    for idx, ae in enumerate(AES):
        row  = next(r for r in metrics[ae] if r["month"] == mlabel)
        p    = row["pct"]
        col  = box_color(p)
        ci   = idx % BCOLS
        ri   = idx // BCOLS
        x    = start_x + ci * (BW + BGAP)
        y    = start_y + ri * (BH + BGAP)

        # Shadow + box
        pdf.set_fill_color(180, 180, 180)
        pdf.rect(x+1, y+1, BW, BH, style="F")
        pdf.set_fill_color(*col)
        pdf.rect(x, y, BW, BH, style="F")
        rc = tuple(max(0, v-50) for v in col)
        pdf.set_draw_color(*rc)
        pdf.rect(x, y, BW, BH, style="D")
        pdf.set_draw_color(0)

        # AE name
        pdf.set_xy(x+2, y+2)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(BW-4, 4, ae[:23])

        # Quota %
        pdf.set_xy(x+2, y+7)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(BW//2, 5.5, f"{p:.1f}%")

        # Conversion (right side of box)
        if HAS_PIPELINE:
            cv = conv_str(row["earned"], row["pipeline"])
            pdf.set_xy(x + BW//2, y+7)
            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(230, 230, 230)
            pdf.cell(BW//2 - 2, 5.5, f"Conv: {cv}", align="R")

        # Amounts
        pdf.set_xy(x+2, y+15)
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(BW-4, 4, f"{c(row['earned'], row['cur'])}  /  {c(row['quota'], row['cur'])}")

    rows_count = -(-len(AES) // BCOLS)
    pdf.set_xy(12, start_y + rows_count * (BH + BGAP) + 4)
    pdf.set_text_color(30)

pdf.set_auto_page_break(auto=True, margin=14)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3+4 — Performance Tables
# ═══════════════════════════════════════════════════════════════════════════════
pdf.add_page()
sec("PERFORMANCE BY ACCOUNT EXECUTIVE")

# Dynamic columns depending on whether pipeline data is available
if HAS_PIPELINE:
    CW   = [26, 30, 30, 18, 28, 28, 22]
    HDRS = ["Month", "Earned", "Quota", "% Quota", "Difference", "Pipeline", "Conversion"]
else:
    CW   = [28, 36, 36, 20, 36]
    HDRS = ["Month", "Earned", "Quota", "% Quota", "Difference"]

for ae in AES:
    cur, quota = QUOTAS[ae]
    if pdf.get_y() > 168:
        pdf.add_page()
        sec("PERFORMANCE BY ACCOUNT EXECUTIVE (cont.)")

    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(30)
    pdf.cell(0, 5, f"{ae}   |   Quota: {c(quota, cur)}/mo", new_x="LMARGIN", new_y="NEXT")

    # Header row
    pdf.set_fill_color(50, 50, 50)
    pdf.set_text_color(255)
    pdf.set_font("Helvetica", "B", 7.5)
    for i, h in enumerate(HDRS):
        pdf.cell(CW[i], 5, h, border=1, fill=True, align="C")
    pdf.ln()

    for idx, r in enumerate(metrics[ae]):
        pdf.set_fill_color(248, 248, 248) if idx % 2 == 0 else pdf.set_fill_color(255, 255, 255)
        pdf.set_font("Helvetica", "", 8)
        clr  = (20, 140, 20) if r["reached"] else (180, 0, 0)
        diff = f"+{c(r['diff'],cur)}" if r["diff"] >= 0 else f"-{c(abs(r['diff']),cur)}"

        pdf.set_text_color(*clr)
        pdf.cell(CW[0], 4.5, r["month"],           border=1, fill=True)
        pdf.cell(CW[1], 4.5, c(r["earned"], cur),  border=1, fill=True, align="R")
        pdf.set_text_color(30)
        pdf.cell(CW[2], 4.5, c(r["quota"],  cur),  border=1, fill=True, align="R")
        pdf.cell(CW[3], 4.5, f"{r['pct']:.1f}%",  border=1, fill=True, align="C")
        pdf.set_text_color(*clr)
        pdf.cell(CW[4], 4.5, diff,                 border=1, fill=True, align="R")
        if HAS_PIPELINE:
            pdf.set_text_color(30)
            pdf.cell(CW[5], 4.5, c(r["pipeline"], cur),          border=1, fill=True, align="R")
            cv_clr = (20, 120, 20) if r["pipeline"] > 0 and r["earned"]/r["pipeline"] >= 0.3 else (30, 30, 30)
            pdf.set_text_color(*cv_clr)
            pdf.cell(CW[6], 4.5, conv_str(r["earned"], r["pipeline"]), border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(30)

    ok = [r["month"] for r in metrics[ae] if r["reached"]]
    ko = [r["month"] for r in metrics[ae] if not r["reached"]]
    pdf.set_font("Helvetica", "I", 7)
    parts = []
    if ok: parts.append(f"Hit: {', '.join(ok)}")
    if ko: parts.append(f"Missed: {', '.join(ko)}")
    pdf.cell(0, 3.5, "   " + "   |   ".join(parts), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — Insights + Rankings
# ═══════════════════════════════════════════════════════════════════════════════
pdf.add_page()

insights = {
    "Antonio Garcia":       ["Strong recovery: EUR 791 Jan to EUR 2,411 Feb (+205%). High volatility - watch pipeline consistency."],
    "Aris Iskandaryan":     ["Sharp drop: EUR 1,111 Jan to EUR 135 Feb. Critical underperformance in Feb. Immediate review needed."],
    "Florencia Gonzalez":   ["Improving: EUR 180 to EUR 641. Near quota in Feb (92%). Good momentum heading into March."],
    "Florencia Torres":     ["Declining: GBP 636 to GBP 290. Both months missed. GBP pipeline requires attention."],
    "Giulia D":             ["Best performer. Exceeded quota both months: 149% Jan, 210% Feb. Team benchmark."],
    "Joan Herrera":         ["Hit quota in Feb (100.5%). Jan was weak (58%). Needs more consistency month to month."],
    "Jorge Garcia del Rey": ["Stable but low: ~48-51% both months. Needs to significantly increase closing volume."],
    "Jose Miguel Pena":     ["Recovery: EUR 433 to EUR 847. Hit quota in Feb (122%). Good momentum - maintain it."],
    "Pablo Alonso Sanchez": ["Improving: EUR 95 to EUR 192. Still below quota (38%/77%) but steady positive trajectory."],
    "Pablo Calderon":       ["Slow Jan (39%) but strong Feb (108%). Quota hit in Feb. Watch for consistency in March."],
    "Rocco Del Bellino":    ["Near quota Jan (81%), exceptional Feb (226%). Strong pattern. One of the most improved AEs."],
}

LEFT_W  = 155
RIGHT_W = pdf.w - 24 - LEFT_W - 4
left_x, right_x = 12, 12 + LEFT_W + 4
top_y = pdf.get_y()

# Insights column
pdf.set_xy(left_x, top_y)
pdf.set_fill_color(35, 35, 35)
pdf.set_text_color(255)
pdf.set_font("Helvetica", "B", 11)
pdf.cell(LEFT_W, 7, "  INSIGHTS BY AE", fill=True, new_x="LMARGIN", new_y="NEXT")
pdf.set_text_color(30)
pdf.ln(2)

for ae in AES:
    if pdf.get_y() > 185: break
    pdf.set_x(left_x)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(30)
    pdf.cell(LEFT_W, 4.5, ae, new_x="LMARGIN", new_y="NEXT")
    for line in insights.get(ae, []):
        pdf.set_x(left_x + 3)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(60)
        pdf.multi_cell(LEFT_W - 3, 4, s(f"- {line}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)

# Rankings column
pdf.set_xy(right_x, top_y)
pdf.set_fill_color(35, 35, 35)
pdf.set_text_color(255)
pdf.set_font("Helvetica", "B", 11)
pdf.cell(RIGHT_W, 7, "  RANKINGS", fill=True)
pdf.set_text_color(30)
ry = top_y + 9

def draw_rank(title, ae_list, val_fn, fmt_fn, x, y, w):
    pdf.set_xy(x, y)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(30, 30, 100)
    pdf.cell(w, 5, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(30)
    top_v = val_fn(ae_list[0]) if ae_list else 1
    for i, ae in enumerate(ae_list, 1):
        v   = val_fn(ae)
        bar = int((v / top_v) * (w - 52)) if top_v > 0 else 0
        pdf.set_xy(x, pdf.get_y())
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(5, 4, f"{i}.", align="R")
        pdf.cell(42, 4, f" {ae[:22]}")
        pdf.set_fill_color(100, 149, 237)
        pdf.cell(bar, 4, "", fill=True)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.cell(w - 47 - bar, 4, f" {fmt_fn(ae)}", new_x="LMARGIN", new_y="NEXT")
    return pdf.get_y() + 4

next_y = draw_rank("By Total Revenue (Jan+Feb)", rank_e, total_e,
                   lambda ae: c(total_e(ae), QUOTAS[ae][0]), right_x, ry, RIGHT_W)
next_y = draw_rank("By Avg Quota % (*Torres in GBP)", rank_pct, avg_p,
                   lambda ae: f"{avg_p(ae):.1f}%", right_x, next_y, RIGHT_W)
if HAS_PIPELINE and rank_conv:
    draw_rank("By Conversion Rate (won/pipeline)", rank_conv, overall_conv,
              lambda ae: f"{overall_conv(ae):.1f}%", right_x, next_y, RIGHT_W)

# ── Save ──────────────────────────────────────────────────────────────────────
out = f"reporte_ae_jan-feb-2026_{date.today().strftime('%Y%m%d')}.pdf"
pdf.output(out)
print(f"PDF saved: {out}  ({pdf.page} pages)")
