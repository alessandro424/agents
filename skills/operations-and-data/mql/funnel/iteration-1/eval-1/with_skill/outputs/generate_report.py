import csv
from datetime import date, datetime
from collections import defaultdict
import sys

# ── Step 1: Load CSV ──────────────────────────────────────────────────────────
csv_path = "c:/Users/aless/AppData/Local/Temp/69ac6d09-63d7-471e-a03d-3afed2d43190_hubspot-custom-report-total-mql-entered-2026-03-26-1.zip.190/total-mql-entered.csv"

def parse_int(val):
    if not val or val.strip() == '(No value)':
        return 0
    try:
        return int(float(val.strip()))
    except ValueError:
        return 0

def days_since(date_str):
    if not date_str or date_str.strip() == '(No value)':
        return None
    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return (date.today() - datetime.strptime(date_str.strip(), fmt).date()).days
        except ValueError:
            continue
    return None

def clean(val):
    v = (val or '').strip()
    return '' if v == '(No value)' else v

with open(csv_path, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Loaded {len(rows)} rows")
print("Columns:", list(rows[0].keys()) if rows else [])

# ── Step 2: Parse each lead ───────────────────────────────────────────────────
CONVERTED_STAGES    = {'Sales Qualified Lead', 'Opportunity', 'Customer'}
NURTURING_STAGES    = {'Nurturing'}
DISQUALIFIED_STAGES = {'Not ICP', 'Lost'}
ACTIVE_STAGES       = {'Marketing Qualified Lead'}

def bucket(stage):
    if stage in CONVERTED_STAGES:    return 'CONVERTED'
    if stage in NURTURING_STAGES:    return 'NURTURING'
    if stage in DISQUALIFIED_STAGES: return 'DISQUALIFIED'
    if stage in ACTIVE_STAGES:       return 'ACTIVE MQL'
    return 'OTHER'

leads = []
for row in rows:
    stage = clean(row.get('Lifecycle Stage', ''))
    leads.append({
        'segment':          clean(row.get('Property Size', '')),
        'ae':               clean(row.get('AE owner', '')),
        'nurturing_reason': clean(row.get('Nurturing Reason', '')),
        'units':            parse_int(row.get('Number of Properties or Rooms', '0')),
        'country':          clean(row.get('Country', '')),
        'source':           clean(row.get('Original Traffic Source', '')),
        'source_detail':    clean(row.get('Original Traffic Source Drill-Down 1', '')),
        'email':            clean(row.get('Email', '')),
        'stage':            stage,
        'bucket':           bucket(stage),
        'contact_id':       clean(row.get('Contact ID', '')),
        'days_as_mql':      days_since(row.get('Date entered "Marketing Qualified Lead (Lifecycle Stage Pipeline)"', '')),
    })

print(f"Parsed {len(leads)} leads")

# ── Step 3a: Overall funnel distribution ─────────────────────────────────────
total = len(leads)

stage_counts = defaultdict(int)
bucket_counts = defaultdict(int)
for l in leads:
    stage_counts[l['stage'] if l['stage'] else '(Unknown)'] += 1
    bucket_counts[l['bucket']] += 1

stage_dist = sorted(stage_counts.items(), key=lambda x: -x[1])
bucket_dist = sorted(bucket_counts.items(), key=lambda x: -x[1])

print("\n=== 3a. Overall Distribution ===")
for s, c in stage_dist:
    print(f"  {s}: {c} ({100*c/total:.1f}%)")
print("Buckets:")
for b, c in bucket_dist:
    print(f"  {b}: {c} ({100*c/total:.1f}%)")

# ── Step 3b: Source -> outcome matrix ─────────────────────────────────────────
source_data = defaultdict(lambda: defaultdict(int))
for l in leads:
    src = l['source'] if l['source'] else '(Unknown)'
    source_data[src][l['bucket']] += 1
    source_data[src]['_total'] += 1

source_rows = []
for src, d in source_data.items():
    tot = d['_total']
    conv = d.get('CONVERTED', 0)
    nurt = d.get('NURTURING', 0)
    disq = d.get('DISQUALIFIED', 0)
    actv = d.get('ACTIVE MQL', 0)
    othr = d.get('OTHER', 0)
    conv_rate = 100 * conv / tot if tot > 0 else 0
    nurt_rate = 100 * nurt / tot if tot > 0 else 0
    source_rows.append((src, tot, conv, nurt, disq, actv, othr, conv_rate, nurt_rate))

source_rows.sort(key=lambda x: -x[1])

print("\n=== 3b. Source -> Outcome ===")
for r in source_rows:
    print(f"  {r[0]}: total={r[1]}, conv={r[2]}({r[7]:.1f}%), nurt={r[3]}({r[8]:.1f}%), disq={r[4]}, active={r[5]}")

# Sub-breakdown by drill-down for top sources
top_sources = [r[0] for r in source_rows[:5]]
detail_data = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
for l in leads:
    src = l['source'] if l['source'] else '(Unknown)'
    if src in top_sources:
        det = l['source_detail'] if l['source_detail'] else '(No detail)'
        detail_data[src][det][l['bucket']] += 1
        detail_data[src][det]['_total'] += 1

# ── Step 3c: Nurturing deep-dive ─────────────────────────────────────────────
nurturing_leads = [l for l in leads if l['bucket'] == 'NURTURING']
n_total = len(nurturing_leads)

reason_counts = defaultdict(int)
for l in nurturing_leads:
    r = l['nurturing_reason'] if l['nurturing_reason'] else '(No reason)'
    reason_counts[r] += 1

reason_rows = sorted(reason_counts.items(), key=lambda x: -x[1])

# Reason × source
reason_source = defaultdict(lambda: defaultdict(int))
for l in nurturing_leads:
    r = l['nurturing_reason'] if l['nurturing_reason'] else '(No reason)'
    src = l['source'] if l['source'] else '(Unknown)'
    reason_source[r][src] += 1

# Reason × segment
reason_segment = defaultdict(lambda: defaultdict(int))
for l in nurturing_leads:
    r = l['nurturing_reason'] if l['nurturing_reason'] else '(No reason)'
    seg = l['segment'] if l['segment'] else '(Unknown)'
    reason_segment[r][seg] += 1

# Reason × country
reason_country = defaultdict(lambda: defaultdict(int))
for l in nurturing_leads:
    r = l['nurturing_reason'] if l['nurturing_reason'] else '(No reason)'
    cnt = l['country'] if l['country'] else '(Unknown)'
    reason_country[r][cnt] += 1

print(f"\n=== 3c. Nurturing Deep-Dive ({n_total} leads) ===")
for r, c in reason_rows[:10]:
    print(f"  {r}: {c} ({100*c/n_total:.1f}%)")

# ── Step 3d: Disqualified deep-dive ──────────────────────────────────────────
disq_leads = [l for l in leads if l['bucket'] == 'DISQUALIFIED']
d_total = len(disq_leads)

disq_source = defaultdict(int)
disq_country = defaultdict(int)
disq_segment = defaultdict(int)
for l in disq_leads:
    disq_source[l['source'] if l['source'] else '(Unknown)'] += 1
    disq_country[l['country'] if l['country'] else '(Unknown)'] += 1
    disq_segment[l['segment'] if l['segment'] else '(Unknown)'] += 1

print(f"\n=== 3d. Disqualified ({d_total} leads) ===")
for s, c in sorted(disq_source.items(), key=lambda x: -x[1]):
    print(f"  Source {s}: {c}")

# ── Step 3e: Converted leads analysis ────────────────────────────────────────
conv_leads = [l for l in leads if l['bucket'] == 'CONVERTED']
c_total = len(conv_leads)

conv_source = defaultdict(int)
conv_country = defaultdict(int)
conv_segment = defaultdict(int)
for l in conv_leads:
    conv_source[l['source'] if l['source'] else '(Unknown)'] += 1
    conv_country[l['country'] if l['country'] else '(Unknown)'] += 1
    conv_segment[l['segment'] if l['segment'] else '(Unknown)'] += 1

print(f"\n=== 3e. Converted ({c_total} leads) ===")
for s, c in sorted(conv_source.items(), key=lambda x: -x[1]):
    print(f"  Source {s}: {c}")

# ── Step 3f: Country × bucket matrix ─────────────────────────────────────────
country_data = defaultdict(lambda: defaultdict(int))
for l in leads:
    cnt = l['country'] if l['country'] else '(Unknown)'
    country_data[cnt][l['bucket']] += 1
    country_data[cnt]['_total'] += 1

country_rows = sorted(country_data.items(), key=lambda x: -x[1]['_total'])
top10_countries = country_rows[:10]

print("\n=== 3f. Country × Bucket (top 10) ===")
for cnt, d in top10_countries:
    tot = d['_total']
    conv_r = 100 * d.get('CONVERTED', 0) / tot if tot > 0 else 0
    print(f"  {cnt}: total={tot}, conv={d.get('CONVERTED',0)}({conv_r:.1f}%), nurt={d.get('NURTURING',0)}, disq={d.get('DISQUALIFIED',0)}, active={d.get('ACTIVE MQL',0)}")

# ── Step 3g: Segment × bucket matrix ─────────────────────────────────────────
seg_data = defaultdict(lambda: defaultdict(int))
for l in leads:
    seg = l['segment'] if l['segment'] else '(Unknown)'
    seg_data[seg][l['bucket']] += 1
    seg_data[seg]['_total'] += 1

print("\n=== 3g. Segment × Bucket ===")
for seg, d in sorted(seg_data.items()):
    tot = d['_total']
    conv_r = 100 * d.get('CONVERTED', 0) / tot if tot > 0 else 0
    print(f"  {seg}: total={tot}, conv={d.get('CONVERTED',0)}({conv_r:.1f}%), nurt={d.get('NURTURING',0)}, disq={d.get('DISQUALIFIED',0)}, active={d.get('ACTIVE MQL',0)}")

# ── Step 3h: AE performance ───────────────────────────────────────────────────
ae_data = defaultdict(lambda: defaultdict(int))
for l in leads:
    ae = l['ae'] if l['ae'] else '(Unassigned)'
    ae_data[ae][l['bucket']] += 1
    ae_data[ae]['_total'] += 1

ae_rows = []
for ae, d in ae_data.items():
    tot = d['_total']
    conv = d.get('CONVERTED', 0)
    nurt = d.get('NURTURING', 0)
    disq = d.get('DISQUALIFIED', 0)
    actv = d.get('ACTIVE MQL', 0)
    conv_rate = 100 * conv / tot if tot > 0 else 0
    ae_rows.append((ae, tot, conv, nurt, disq, actv, conv_rate))

ae_rows.sort(key=lambda x: -x[1])

print("\n=== 3h. AE Performance ===")
for r in ae_rows:
    print(f"  {r[0]}: total={r[1]}, conv={r[2]}({r[6]:.1f}%), nurt={r[3]}, disq={r[4]}, active={r[5]}")

# ── Step 4: Generate PDF ──────────────────────────────────────────────────────
try:
    from fpdf import FPDF
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'fpdf2', '-q'])
    from fpdf import FPDF

output_dir = "c:/Users/aless/Documents/skills/mql-funnel-workspace/iteration-1/eval-1/with_skill/outputs/"
today_str = date.today().strftime('%Y-%m-%d')
output_path = output_dir + f"mql_funnel_analysis_{today_str}.pdf"

# Color constants
HEADER_BG   = (232, 232, 232)   # #E8E8E8
TABLE_HDR   = (204, 204, 204)   # #CCCCCC
ALT_ROW     = (245, 245, 245)   # #F5F5F5
GREEN_TINT  = (232, 245, 233)   # #E8F5E9
YELLOW_TINT = (255, 253, 231)   # #FFFDE7
RED_TINT    = (255, 235, 238)   # #FFEBEE
WHITE       = (255, 255, 255)
DARK_TEXT   = (30, 30, 30)

def safe(text):
    """Encode string to latin-1, replacing unmappable characters with '?'."""
    return str(text).encode('latin-1', errors='replace').decode('latin-1')

class MQLReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        pass  # custom footer only

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f'Page {self.page_no()}', align='C')

    def section_header(self, title):
        self.ln(4)
        self.set_fill_color(*HEADER_BG)
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(*DARK_TEXT)
        self.cell(0, 9, self.safe(title), ln=True, fill=True)
        self.ln(2)

    def table_header(self, cols, widths):
        self.set_fill_color(*TABLE_HDR)
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(*DARK_TEXT)
        for col, w in zip(cols, widths):
            self.cell(w, 7, self.safe(str(col)), border=1, fill=True, align='C')
        self.ln()

    @staticmethod
    def safe(text):
        """Encode to latin-1, replacing unmappable chars with '?'."""
        return str(text).encode('latin-1', errors='replace').decode('latin-1')

    def table_row(self, vals, widths, fill_color=None, aligns=None):
        if fill_color:
            self.set_fill_color(*fill_color)
        else:
            self.set_fill_color(*WHITE)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(*DARK_TEXT)
        if aligns is None:
            aligns = ['L'] + ['C'] * (len(vals) - 1)
        for v, w, a in zip(vals, widths, aligns):
            txt = self.safe(v if v is not None else '')
            # Truncate to fit
            self.cell(w, 6, txt[:30], border=1, fill=bool(fill_color), align=a)
        self.ln()

    def bullet(self, text, indent=5):
        self.set_font('Helvetica', '', 9)
        self.set_text_color(*DARK_TEXT)
        self.set_x(self.get_x() + indent)
        self.multi_cell(0, 5, self.safe('* ' + text))
        self.ln(1)

pdf = MQLReport()
pdf.set_margins(15, 15, 15)

# ─── PAGE 1: Cover ────────────────────────────────────────────────────────────
pdf.add_page()
pdf.ln(30)
pdf.set_font('Helvetica', 'B', 24)
pdf.set_text_color(33, 37, 41)
pdf.cell(0, 12, 'MQL Funnel Analysis Report', ln=True, align='C')
pdf.ln(6)
pdf.set_font('Helvetica', '', 14)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 8, f'Report Date: {today_str}', ln=True, align='C')
pdf.ln(4)
pdf.cell(0, 8, f'Total MQLs Analyzed: {total}', ln=True, align='C')
pdf.ln(20)

# Bucket summary boxes
pdf.set_font('Helvetica', 'B', 11)
bucket_colors_map = {
    'CONVERTED':  GREEN_TINT,
    'NURTURING':  YELLOW_TINT,
    'DISQUALIFIED': RED_TINT,
    'ACTIVE MQL': (220, 235, 252),
    'OTHER':      ALT_ROW,
}
bx = 30
for bkt, cnt in bucket_dist:
    pct = 100 * cnt / total
    col = bucket_colors_map.get(bkt, WHITE)
    pdf.set_fill_color(*col)
    pdf.set_x(bx)
    pdf.cell(38, 20, f'{bkt}\n{cnt} ({pct:.1f}%)', border=1, fill=True, align='C', ln=0)
    bx += 40
pdf.ln(30)

pdf.set_font('Helvetica', 'I', 10)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 8, 'Internal Marketing Report - Confidential', ln=True, align='C')

# ─── PAGE 2: Executive Summary ───────────────────────────────────────────────
pdf.add_page()
pdf.section_header('Executive Summary')
pdf.ln(2)

# Derive key insights
best_source = max(source_rows, key=lambda x: x[7])
worst_source = min(source_rows, key=lambda x: (x[7], -x[1]))  # lowest conv, high volume
top_reason = reason_rows[0] if reason_rows else ('N/A', 0)
top_nurture_source = source_rows[0] if source_rows else None

# Top conversion country
top_conv_country = max(country_rows[:10], key=lambda x: x[1].get('CONVERTED', 0) / x[1]['_total'] if x[1]['_total'] > 0 else 0)
top_volume_country = country_rows[0] if country_rows else None

paid_social = next((r for r in source_rows if r[0] == 'Paid Social'), None)
direct = next((r for r in source_rows if r[0] == 'Direct Traffic'), None)
organic = next((r for r in source_rows if r[0] == 'Organic Search'), None)

bullets = []

if paid_social:
    bullets.append(
        f"Paid Social is the largest channel ({paid_social[1]} leads, {paid_social[1]*100//total}% of total) "
        f"but has only a {paid_social[7]:.1f}% conversion rate - the volume-to-quality gap is significant."
    )

if direct:
    bullets.append(
        f"Direct Traffic delivers the best conversion quality: {direct[2]} of {direct[1]} leads converted "
        f"({direct[7]:.1f}% conversion rate), suggesting high-intent inbound visitors."
    )

if top_reason[0] != '(No reason)' and top_reason[0] != 'N/A':
    bullets.append(
        f"The top nurturing reason is '{top_reason[0]}' ({top_reason[1]} leads, "
        f"{100*top_reason[1]//n_total if n_total else 0}% of nurturing), "
        f"indicating a key qualification gap that should be addressed at the top of the funnel."
    )

nurt_pct = 100 * bucket_counts.get('NURTURING', 0) / total
disq_pct = 100 * bucket_counts.get('DISQUALIFIED', 0) / total
conv_pct_overall = 100 * bucket_counts.get('CONVERTED', 0) / total
active_pct = 100 * bucket_counts.get('ACTIVE MQL', 0) / total

bullets.append(
    f"Overall funnel health: {conv_pct_overall:.1f}% converted, {nurt_pct:.1f}% in nurturing, "
    f"{disq_pct:.1f}% disqualified, {active_pct:.1f}% still active. "
    f"More than half the funnel has not yet converted."
)

if top_volume_country:
    cnt_name = top_volume_country[0]
    cnt_d = top_volume_country[1]
    cnt_conv_r = 100 * cnt_d.get('CONVERTED', 0) / cnt_d['_total']
    bullets.append(
        f"{cnt_name} is the top country by volume ({cnt_d['_total']} leads) "
        f"with a {cnt_conv_r:.1f}% conversion rate - "
        + ("a strong anchor market." if cnt_conv_r > 15 else "conversion potential remains underexploited.")
    )

europe_count = country_data.get('Europe', {}).get('_total', 0)
if europe_count > 0:
    bullets.append(
        f"'Europe' appears as a country for {europe_count} leads - this is a data quality issue. "
        f"These leads cannot be properly geo-analyzed and should be reviewed in HubSpot."
    )

lang_barrier = reason_counts.get('Language barrier', 0)
if lang_barrier > 0:
    bullets.append(
        f"Language barrier accounts for {lang_barrier} nurturing leads, pointing to AE routing issues "
        f"where non-Spanish/English leads are handled by the wrong team."
    )

for b in bullets[:7]:
    pdf.bullet(b)
    pdf.ln(1)

# ─── PAGE 3: Overall Funnel Distribution ─────────────────────────────────────
pdf.add_page()
pdf.section_header('Overall Funnel Distribution')

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Lifecycle Stage', ln=True)
pdf.ln(2)
cols  = ['Lifecycle Stage', 'Count', '% of Total']
ws    = [100, 40, 40]
pdf.table_header(cols, ws)
for i, (s, c) in enumerate(stage_dist):
    fill = ALT_ROW if i % 2 == 1 else None
    bkt = bucket(s)
    row_color = bucket_colors_map.get(bkt) if bkt != 'OTHER' else None
    pdf.table_row([s, c, f'{100*c/total:.1f}%'], ws, fill_color=row_color or fill)

pdf.ln(6)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Outcome Bucket', ln=True)
pdf.ln(2)
cols2 = ['Bucket', 'Count', '% of Total']
ws2   = [80, 40, 40]
pdf.table_header(cols2, ws2)
for i, (b, c) in enumerate(bucket_dist):
    col = bucket_colors_map.get(b, ALT_ROW if i % 2 == 1 else WHITE)
    pdf.table_row([b, c, f'{100*c/total:.1f}%'], ws2, fill_color=col)

# ─── PAGE 4: Source -> Outcome Analysis ───────────────────────────────────────
pdf.add_page()
pdf.section_header('Source -> Outcome Analysis')

pdf.set_font('Helvetica', 'B', 9)
pdf.set_text_color(60, 60, 60)
pdf.cell(0, 5, 'Main table sorted by volume (descending). Conv. Rate = CONVERTED / Total.', ln=True)
pdf.ln(3)

cols = ['Source', 'Total', 'Conv', 'Nurt', 'Disq', 'Active', 'Conv%', 'Nurt%']
ws   = [52, 16, 16, 16, 16, 16, 18, 18]
pdf.table_header(cols, ws)

for i, r in enumerate(source_rows):
    src_name, tot, conv, nurt, disq, actv, othr, conv_rate, nurt_rate = r
    # Color best conversion green, worst red
    if conv_rate == max(rr[7] for rr in source_rows) and tot >= 3:
        fill = GREEN_TINT
    elif conv_rate == min(rr[7] for rr in source_rows if rr[1] >= 3):
        fill = RED_TINT
    elif i % 2 == 1:
        fill = ALT_ROW
    else:
        fill = WHITE
    pdf.table_row([src_name, tot, conv, nurt, disq, actv, f'{conv_rate:.1f}%', f'{nurt_rate:.1f}%'],
                  ws, fill_color=fill)

# Drill-down sub-tables for top 3 sources
pdf.ln(5)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Drill-Down by Sub-Source (Top Sources)', ln=True)
pdf.ln(2)

for src in top_sources[:3]:
    if src not in detail_data:
        continue
    pdf.set_font('Helvetica', 'BI', 9)
    pdf.set_fill_color(*HEADER_BG)
    pdf.cell(0, 6, f'  {src}', ln=True, fill=True)
    cols_d = ['Sub-Source', 'Total', 'Conv', 'Nurt', 'Disq', 'Active', 'Conv%']
    ws_d   = [62, 16, 16, 16, 16, 16, 20]
    pdf.table_header(cols_d, ws_d)
    sub_rows = sorted(detail_data[src].items(), key=lambda x: -x[1]['_total'])
    for j, (det, d) in enumerate(sub_rows[:8]):
        tot_d = d['_total']
        conv_d = d.get('CONVERTED', 0)
        nurt_d = d.get('NURTURING', 0)
        disq_d = d.get('DISQUALIFIED', 0)
        actv_d = d.get('ACTIVE MQL', 0)
        cr = 100 * conv_d / tot_d if tot_d else 0
        fill = ALT_ROW if j % 2 == 1 else WHITE
        det_name = det if len(det) <= 30 else det[:27] + '...'
        pdf.table_row([det_name, tot_d, conv_d, nurt_d, disq_d, actv_d, f'{cr:.1f}%'],
                      ws_d, fill_color=fill)
    pdf.ln(2)

# ─── PAGE 5: Nurturing Deep-Dive ─────────────────────────────────────────────
pdf.add_page()
pdf.section_header(f'Nurturing Deep-Dive ({n_total} leads)')

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Reason Breakdown', ln=True)
pdf.ln(2)
cols = ['Nurturing Reason', 'Count', '% of Nurturing']
ws   = [110, 30, 40]
pdf.table_header(cols, ws)
for i, (r, c) in enumerate(reason_rows):
    fill = YELLOW_TINT if i < 3 else (ALT_ROW if i % 2 == 1 else WHITE)
    pct = f'{100*c/n_total:.1f}%' if n_total > 0 else '0%'
    pdf.table_row([r if r else '(No reason)', c, pct], ws, fill_color=fill)

# Reason × Source (top 5 reasons × top 4 sources)
pdf.ln(5)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Reason × Source (top 5 reasons, top 4 sources)', ln=True)
pdf.ln(2)

top5_reasons = [r[0] for r in reason_rows[:5]]
top4_sources = [r[0] for r in source_rows[:4]]

rs_cols = ['Reason'] + [s[:18] for s in top4_sources]
rs_ws   = [65] + [30] * len(top4_sources)
pdf.table_header(rs_cols, rs_ws)
for i, rsn in enumerate(top5_reasons):
    row_vals = [rsn if rsn else '(No reason)']
    for src in top4_sources:
        row_vals.append(reason_source[rsn].get(src, 0))
    fill = ALT_ROW if i % 2 == 1 else WHITE
    pdf.table_row(row_vals, rs_ws, fill_color=fill)

# Reason × Segment
pdf.ln(5)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Reason × Segment', ln=True)
pdf.ln(2)
all_segs = sorted(set(l['segment'] for l in nurturing_leads if l['segment']))
seg_cols = ['Reason'] + all_segs
seg_ws   = [80] + [30] * len(all_segs)
pdf.table_header(seg_cols, seg_ws)
for i, rsn in enumerate(top5_reasons):
    row_vals = [rsn if rsn else '(No reason)']
    for seg in all_segs:
        row_vals.append(reason_segment[rsn].get(seg, 0))
    fill = ALT_ROW if i % 2 == 1 else WHITE
    pdf.table_row(row_vals, seg_ws, fill_color=fill)

# Key observations
pdf.ln(5)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Key Observations', ln=True)
pdf.ln(2)

top3 = reason_rows[:3]
obs = []
for rsn, cnt in top3:
    pct = 100 * cnt / n_total if n_total > 0 else 0
    top_src_for_reason = max(reason_source[rsn].items(), key=lambda x: x[1]) if reason_source[rsn] else ('N/A', 0)
    obs.append(
        f"'{rsn}' is reason #{top3.index((rsn,cnt))+1} ({cnt} leads, {pct:.1f}% of nurturing). "
        f"Predominantly from {top_src_for_reason[0]} ({top_src_for_reason[1]} leads). "
        + (
            "Suggests top-of-funnel qualification questions should filter these leads earlier."
            if 'info' in rsn.lower() else
            "Indicates a timing or readiness gap - consider automated re-engagement sequences."
            if 'timing' in rsn.lower() or 'workload' in rsn.lower() else
            "Points to ICP definition issues or ad targeting reaching unqualified audiences."
            if 'icp' in rsn.lower() else
            "Review ad targeting and country-language routing to reduce friction."
            if 'language' in rsn.lower() else
            "Add pre-qualification to forms and ads to filter low-intent leads."
        )
    )

for o in obs:
    pdf.bullet(o)
    pdf.ln(1)

# ─── PAGE 6: Disqualified Analysis ───────────────────────────────────────────
pdf.add_page()
pdf.section_header(f'Disqualified (Not ICP / Lost) Analysis - {d_total} leads')

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Source', ln=True)
pdf.ln(2)
cols = ['Source', 'Count', '% of Disqualified']
ws   = [80, 30, 50]
pdf.table_header(cols, ws)
disq_src_rows = sorted(disq_source.items(), key=lambda x: -x[1])
for i, (s, c) in enumerate(disq_src_rows):
    fill = RED_TINT if i == 0 else (ALT_ROW if i % 2 == 1 else WHITE)
    pct = f'{100*c/d_total:.1f}%' if d_total > 0 else '0%'
    pdf.table_row([s, c, pct], ws, fill_color=fill)

pdf.ln(4)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Country', ln=True)
pdf.ln(2)
cols2 = ['Country', 'Count', '% of Disqualified']
ws2   = [80, 30, 50]
pdf.table_header(cols2, ws2)
disq_cnt_rows = sorted(disq_country.items(), key=lambda x: -x[1])
for i, (c, n) in enumerate(disq_cnt_rows):
    fill = ALT_ROW if i % 2 == 1 else WHITE
    pct = f'{100*n/d_total:.1f}%' if d_total > 0 else '0%'
    pdf.table_row([c, n, pct], ws2, fill_color=fill)

pdf.ln(4)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Segment', ln=True)
pdf.ln(2)
cols3 = ['Segment', 'Count', '% of Disqualified']
ws3   = [80, 30, 50]
pdf.table_header(cols3, ws3)
disq_seg_rows = sorted(disq_segment.items(), key=lambda x: -x[1])
for i, (s, c) in enumerate(disq_seg_rows):
    fill = ALT_ROW if i % 2 == 1 else WHITE
    pct = f'{100*c/d_total:.1f}%' if d_total > 0 else '0%'
    pdf.table_row([s, c, pct], ws3, fill_color=fill)

pdf.ln(4)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Full Disqualified Lead List', ln=True)
pdf.ln(2)
cols4 = ['AE', 'Email', 'Country', 'Source', 'Stage']
ws4   = [36, 66, 26, 30, 22]
pdf.table_header(cols4, ws4)
for i, l in enumerate(sorted(disq_leads, key=lambda x: x['country'])):
    fill = RED_TINT if i % 2 == 0 else WHITE
    ae_s = (l['ae'][:15] + '..') if len(l['ae']) > 17 else l['ae']
    em_s = (l['email'][:28] + '..') if len(l['email']) > 30 else l['email']
    pdf.table_row([ae_s, em_s, l['country'][:20], l['source'][:20], l['stage'][:15]],
                  ws4, fill_color=fill)

# ─── PAGE 7: Converted Leads Analysis ────────────────────────────────────────
pdf.add_page()
pdf.section_header(f'Converted Leads Analysis - {c_total} leads')

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Source', ln=True)
pdf.ln(2)
cols = ['Source', 'Count', '% of Converted']
ws   = [80, 30, 50]
pdf.table_header(cols, ws)
for i, (s, c) in enumerate(sorted(conv_source.items(), key=lambda x: -x[1])):
    fill = GREEN_TINT if i == 0 else (ALT_ROW if i % 2 == 1 else WHITE)
    pct = f'{100*c/c_total:.1f}%' if c_total > 0 else '0%'
    pdf.table_row([s, c, pct], ws, fill_color=fill)

pdf.ln(4)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Country', ln=True)
pdf.ln(2)
pdf.table_header(['Country', 'Count', '% of Converted'], [80, 30, 50])
for i, (c, n) in enumerate(sorted(conv_country.items(), key=lambda x: -x[1])):
    fill = ALT_ROW if i % 2 == 1 else WHITE
    pct = f'{100*n/c_total:.1f}%' if c_total > 0 else '0%'
    pdf.table_row([c, n, pct], [80, 30, 50], fill_color=fill)

pdf.ln(4)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Segment', ln=True)
pdf.ln(2)
pdf.table_header(['Segment', 'Count', '% of Converted'], [80, 30, 50])
for i, (s, c) in enumerate(sorted(conv_segment.items(), key=lambda x: -x[1])):
    fill = ALT_ROW if i % 2 == 1 else WHITE
    pct = f'{100*c/c_total:.1f}%' if c_total > 0 else '0%'
    pdf.table_row([s, c, pct], [80, 30, 50], fill_color=fill)

pdf.ln(4)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Full Converted Lead List', ln=True)
pdf.ln(2)
cols_c = ['AE', 'Email', 'Country', 'Source', 'Stage', 'Units']
ws_c   = [32, 60, 24, 26, 24, 14]
pdf.table_header(cols_c, ws_c)
for i, l in enumerate(sorted(conv_leads, key=lambda x: x['source'])):
    fill = GREEN_TINT if i % 2 == 0 else WHITE
    ae_s = (l['ae'][:14] + '..') if len(l['ae']) > 16 else l['ae']
    em_s = (l['email'][:24] + '..') if len(l['email']) > 26 else l['email']
    pdf.table_row([ae_s, em_s, l['country'][:18], l['source'][:18], l['stage'][:18], l['units']],
                  ws_c, fill_color=fill)

# ─── PAGE 8: Country × Outcome Matrix ────────────────────────────────────────
pdf.add_page()
pdf.section_header('Country × Outcome Matrix (Top 10 Countries by Volume)')

cols = ['Country', 'Total', 'Converted', 'Nurturing', 'Disqualified', 'Active MQL', 'Conv%']
ws   = [42, 16, 22, 22, 26, 22, 20]
pdf.table_header(cols, ws)
for i, (cnt, d) in enumerate(top10_countries):
    tot = d['_total']
    conv = d.get('CONVERTED', 0)
    nurt = d.get('NURTURING', 0)
    disq = d.get('DISQUALIFIED', 0)
    actv = d.get('ACTIVE MQL', 0)
    cr = 100 * conv / tot if tot else 0
    if cnt == 'Europe':
        fill = (255, 245, 200)  # flag data quality
    elif cr > 20:
        fill = GREEN_TINT
    elif cr == 0 and tot > 3:
        fill = RED_TINT
    elif i % 2 == 1:
        fill = ALT_ROW
    else:
        fill = WHITE
    pdf.table_row([cnt[:20], tot, conv, nurt, disq, actv, f'{cr:.1f}%'], ws, fill_color=fill)

if europe_count > 0:
    pdf.ln(4)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(180, 0, 0)
    pdf.cell(0, 5, '* "Europe" as country is a data quality issue. These leads cannot be geo-analyzed. Review in HubSpot.', ln=True)
    pdf.set_text_color(*DARK_TEXT)

# ─── PAGE 9: Segment Analysis ─────────────────────────────────────────────────
pdf.add_page()
pdf.section_header('Segment Analysis')

cols = ['Segment', 'Total', 'Converted', 'Nurturing', 'Disqualified', 'Active MQL', 'Conv%']
ws   = [40, 16, 22, 22, 26, 22, 20]
pdf.table_header(cols, ws)
for i, (seg, d) in enumerate(sorted(seg_data.items(), key=lambda x: -x[1]['_total'])):
    tot = d['_total']
    conv = d.get('CONVERTED', 0)
    nurt = d.get('NURTURING', 0)
    disq = d.get('DISQUALIFIED', 0)
    actv = d.get('ACTIVE MQL', 0)
    cr = 100 * conv / tot if tot else 0
    fill = GREEN_TINT if cr == max(100*v.get('CONVERTED',0)/v['_total'] for v in seg_data.values() if v['_total'] > 0) else (ALT_ROW if i % 2 == 1 else WHITE)
    pdf.table_row([seg, tot, conv, nurt, disq, actv, f'{cr:.1f}%'], ws, fill_color=fill)

# AE Performance
pdf.ln(8)
pdf.section_header('AE Performance')
cols = ['AE', 'Total', 'Converted', 'Conv%', 'Nurturing', 'Disqualified', 'Active']
ws   = [50, 16, 20, 18, 20, 24, 16]
pdf.table_header(cols, ws)
for i, r in enumerate(ae_rows):
    ae, tot, conv, nurt, disq, actv, cr = r
    fill = GREEN_TINT if cr == max(rr[6] for rr in ae_rows if rr[1] >= 3) and tot >= 3 else (ALT_ROW if i % 2 == 1 else WHITE)
    ae_disp = (ae[:22] + '..') if len(ae) > 24 else ae
    pdf.table_row([ae_disp, tot, conv, f'{cr:.1f}%', nurt, disq, actv], ws, fill_color=fill)

# ─── PAGE 10: Recommendations ─────────────────────────────────────────────────
pdf.add_page()
pdf.section_header('Recommendations for Marketing')
pdf.ln(3)

recs = []

# Rec 1: top nurturing reason
if reason_rows and reason_rows[0][0] not in ('(No reason)', ''):
    top_rsn = reason_rows[0][0]
    recs.append(
        f"Address top nurturing reason '{top_rsn}': Add intent-qualification questions to landing page "
        f"forms (e.g., 'Are you currently managing a property?', 'How many units do you manage?'). "
        f"This alone could prevent {reason_rows[0][1]} leads from entering nurturing without intent signal."
    )

# Rec 2: Paid Social conversion
if paid_social and paid_social[7] < 15:
    recs.append(
        f"Paid Social has a {paid_social[7]:.1f}% conversion rate on {paid_social[1]} leads. "
        f"Reduce wasted spend by adding property-count filters to Facebook/Instagram ad targeting "
        f"(require 5+ units) and add a disqualifying question at the form level."
    )

# Rec 3: Language barrier
if lang_barrier > 2:
    top_lb_countries = sorted(reason_country.get('Language barrier', {}).items(), key=lambda x: -x[1])[:3]
    countries_str = ', '.join(c for c, _ in top_lb_countries)
    recs.append(
        f"Language barrier affects {lang_barrier} leads, primarily from: {countries_str}. "
        f"Review AE routing logic - route non-Spanish/non-English leads to the appropriate regional rep. "
        f"Consider adding language-based routing in HubSpot workflows."
    )

# Rec 4: Europe data quality
if europe_count > 0:
    recs.append(
        f"Fix 'Europe' country data: {europe_count} leads have 'Europe' as country - a HubSpot enrichment failure. "
        f"Enable IP-based country detection or require country field validation on all landing page forms. "
        f"These leads are unroutable and unanalyzable."
    )

# Rec 5: Direct Traffic / high-intent channels
if direct and direct[7] > 20:
    recs.append(
        f"Direct Traffic converts at {direct[7]:.1f}% - nearly {direct[7]//paid_social[7] if paid_social and paid_social[7] > 0 else '2'}x the Paid Social rate. "
        f"Invest in SEO and content to grow organic and direct traffic. "
        f"Review landing pages for Paid Search to improve landing-to-MQL conversion quality."
    )

# Rec 6: No-answer nurturing
no_answer = reason_counts.get('No answer', 0)
if no_answer > 3:
    recs.append(
        f"'No answer' accounts for {no_answer} nurturing leads. "
        f"Implement automated follow-up sequences for MQLs that don't respond within 48h: "
        f"add 2-3 automated touchpoints (email + WhatsApp) before moving to nurturing."
    )

# Rec 7: Compliance/timing
compliance = reason_counts.get('Compliance/paperwork not ready yet', 0)
timing_count = reason_counts.get('Timing', 0)
if compliance + timing_count > 3:
    recs.append(
        f"'Timing' ({timing_count}) and 'Compliance/paperwork not ready' ({compliance}) total {timing_count+compliance} leads. "
        f"These are temporarily unready but not disqualified. Create a structured 30/60/90-day re-engagement "
        f"nurture sequence with compliance guides and feature updates to convert them when ready."
    )

for idx, rec in enumerate(recs[:7], 1):
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(0, 6, f'Recommendation {idx}', ln=True)
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, safe(rec))
    pdf.ln(2)

# ─── PAGE 11: Appendix - Full Lead List ──────────────────────────────────────
pdf.add_page()
pdf.section_header('Appendix - Full Lead List')

pdf.set_font('Helvetica', '', 8)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 5, f'All {total} leads sorted by bucket then segment. Colors: green=converted, yellow=nurturing, red=disqualified.', ln=True)
pdf.ln(2)

cols_a = ['Contact ID', 'AE', 'Segment', 'Email', 'Country', 'Source', 'Units', 'Stage', 'Nurt. Reason']
ws_a   = [24, 30, 14, 52, 20, 22, 10, 24, 30]
pdf.table_header(cols_a, ws_a)

bucket_order = {'CONVERTED': 0, 'ACTIVE MQL': 1, 'NURTURING': 2, 'DISQUALIFIED': 3, 'OTHER': 4}
sorted_leads = sorted(leads, key=lambda x: (bucket_order.get(x['bucket'], 5), x['segment'], x['country']))

for i, l in enumerate(sorted_leads):
    bkt = l['bucket']
    if bkt == 'CONVERTED':
        fill = GREEN_TINT
    elif bkt == 'NURTURING':
        fill = YELLOW_TINT
    elif bkt == 'DISQUALIFIED':
        fill = RED_TINT
    else:
        fill = ALT_ROW if i % 2 == 1 else WHITE

    em = (l['email'][:22] + '..') if len(l['email']) > 24 else l['email']
    ae = (l['ae'][:13] + '..') if len(l['ae']) > 15 else l['ae']
    nr = (l['nurturing_reason'][:13] + '..') if len(l['nurturing_reason']) > 15 else l['nurturing_reason']
    cid = l['contact_id'][-10:] if len(l['contact_id']) > 10 else l['contact_id']

    pdf.table_row(
        [cid, ae, l['segment'][:8], em, l['country'][:14], l['source'][:14], l['units'], l['stage'][:14], nr],
        ws_a, fill_color=fill
    )

# Save PDF
pdf.output(output_path)
print(f"\nPDF saved to: {output_path}")
