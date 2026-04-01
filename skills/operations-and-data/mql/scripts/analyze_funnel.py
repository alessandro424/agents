import csv
from datetime import date, datetime
from collections import defaultdict
import os
import sys

# Try to import fpdf2
try:
    from fpdf import FPDF
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'fpdf2', '-q'])
    from fpdf import FPDF

def sanitize(text):
    if not isinstance(text, str):
        text = str(text)
    return (text
        .replace('\u2014', '-').replace('\u2013', '-')
        .replace('\u2018', "'").replace('\u2019', "'")
        .replace('\u201c', '"').replace('\u201d', '"')
        .replace('\u2022', '-').replace('\u2026', '...')
        .encode('latin-1', errors='replace').decode('latin-1'))

if len(sys.argv) < 2:
    print("Usage: python analyze_funnel.py <csv_path> [output_dir]", file=sys.stderr)
    sys.exit(1)
csv_path = sys.argv[1]
output_dir = sys.argv[2] if len(sys.argv) > 2 else "."
output_path = os.path.join(output_dir, f"mql_funnel_analysis_{date.today().isoformat()}.pdf")

# ── Step 1: Load CSV ─────────────────────────────────────────────────────────

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
print(f"Columns: {list(rows[0].keys()) if rows else 'none'}")

# ── Step 2: Parse leads ───────────────────────────────────────────────────────

CONVERTED_STAGES = {'Sales Qualified Lead', 'Opportunity', 'Customer'}
NURTURING_STAGES  = {'Nurturing'}
DISQUALIFIED_STAGES = {'Not ICP', 'Lost'}
ACTIVE_STAGES = {'Marketing Qualified Lead'}

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

total = len(leads)
print(f"Total leads: {total}")

# ── Step 3: Compute analyses ─────────────────────────────────────────────────

# 3a. Overall funnel distribution
stage_counts = defaultdict(int)
bucket_counts = defaultdict(int)
for l in leads:
    stage_counts[l['stage']] += 1
    bucket_counts[l['bucket']] += 1

# 3b. Source → outcome matrix
source_data = defaultdict(lambda: defaultdict(int))
for l in leads:
    src = l['source'] or 'Unknown'
    source_data[src]['total'] += 1
    source_data[src][l['bucket']] += 1

# Sub-breakdown by drill-down 1
source_detail_data = defaultdict(lambda: defaultdict(int))
for l in leads:
    src = l['source'] or 'Unknown'
    detail = l['source_detail'] or 'Unknown'
    key = f"{src} / {detail}"
    source_detail_data[key]['total'] += 1
    source_detail_data[key][l['bucket']] += 1
    source_detail_data[key]['_source'] = src

# 3c. Nurturing deep-dive
nurturing_leads = [l for l in leads if l['bucket'] == 'NURTURING']
nurturing_reason_counts = defaultdict(int)
reason_source = defaultdict(lambda: defaultdict(int))
reason_segment = defaultdict(lambda: defaultdict(int))
reason_country = defaultdict(lambda: defaultdict(int))
for l in nurturing_leads:
    r = l['nurturing_reason'] or 'Not specified'
    nurturing_reason_counts[r] += 1
    reason_source[r][l['source'] or 'Unknown'] += 1
    reason_segment[r][l['segment'] or 'Unknown'] += 1
    reason_country[r][l['country'] or 'Unknown'] += 1

# 3d. Disqualified deep-dive
disq_leads = [l for l in leads if l['bucket'] == 'DISQUALIFIED']
disq_source = defaultdict(int)
disq_country = defaultdict(int)
disq_segment = defaultdict(int)
for l in disq_leads:
    disq_source[l['source'] or 'Unknown'] += 1
    disq_country[l['country'] or 'Unknown'] += 1
    disq_segment[l['segment'] or 'Unknown'] += 1

# 3e. Converted leads
conv_leads = [l for l in leads if l['bucket'] == 'CONVERTED']
conv_source = defaultdict(int)
conv_country = defaultdict(int)
conv_segment = defaultdict(int)
for l in conv_leads:
    conv_source[l['source'] or 'Unknown'] += 1
    conv_country[l['country'] or 'Unknown'] += 1
    conv_segment[l['segment'] or 'Unknown'] += 1

# 3f. Country × bucket matrix
country_data = defaultdict(lambda: defaultdict(int))
for l in leads:
    c = l['country'] or 'Unknown'
    country_data[c]['total'] += 1
    country_data[c][l['bucket']] += 1

top10_countries = sorted(country_data.keys(), key=lambda c: country_data[c]['total'], reverse=True)[:10]

# 3g. Segment × bucket matrix
segment_data = defaultdict(lambda: defaultdict(int))
for l in leads:
    s = l['segment'] or 'Unknown'
    segment_data[s]['total'] += 1
    segment_data[s][l['bucket']] += 1

# 3h. AE performance
ae_data = defaultdict(lambda: defaultdict(int))
for l in leads:
    ae = l['ae'] or 'Unassigned'
    ae_data[ae]['total'] += 1
    ae_data[ae][l['bucket']] += 1

def conv_rate(d):
    t = d.get('total', 0)
    if t == 0: return 0.0
    return 100.0 * d.get('CONVERTED', 0) / t

def nurt_rate(d):
    t = d.get('total', 0)
    if t == 0: return 0.0
    return 100.0 * d.get('NURTURING', 0) / t

# ── Step 4: Executive summary insights ───────────────────────────────────────

sorted_sources = sorted(source_data.keys(), key=lambda s: source_data[s]['total'], reverse=True)
best_conv_source = max(sorted_sources, key=lambda s: conv_rate(source_data[s]))
worst_conv_source = min(sorted_sources, key=lambda s: source_data[s]['total'] > 5 and conv_rate(source_data[s]) or 100, default=sorted_sources[0])
top_nurt_reason = max(nurturing_reason_counts, key=nurturing_reason_counts.get) if nurturing_reason_counts else 'N/A'
top_disq_source = max(disq_source, key=disq_source.get) if disq_source else 'N/A'

# ── Step 5: Generate PDF ──────────────────────────────────────────────────────

BUCKETS = ['CONVERTED', 'NURTURING', 'DISQUALIFIED', 'ACTIVE MQL', 'OTHER']
BUCKET_COLORS = {
    'CONVERTED':    (232, 245, 233),
    'NURTURING':    (255, 253, 231),
    'DISQUALIFIED': (255, 235, 238),
    'ACTIVE MQL':   (255, 255, 255),
    'OTHER':        (245, 245, 245),
}

class PDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f'Page {self.page_no()}', align='C')
        self.set_text_color(0, 0, 0)

    def section_header(self, title):
        self.ln(4)
        self.set_fill_color(232, 232, 232)
        self.set_font('Helvetica', 'B', 13)
        self.cell(0, 9, sanitize(title), fill=True, new_x='LMARGIN', new_y='NEXT')
        self.ln(2)

    def small_text(self, txt, size=9):
        self.set_font('Helvetica', '', size)
        self.multi_cell(0, 5, sanitize(txt))

    def table_header_row(self, cols, widths, font_size=9):
        self.set_fill_color(204, 204, 204)
        self.set_font('Helvetica', 'B', font_size)
        for col, w in zip(cols, widths):
            self.cell(w, 7, sanitize(str(col)), border=1, fill=True, align='C')
        self.ln()

    def table_data_row(self, cells, widths, fill_color=None, font_size=9, aligns=None):
        if fill_color:
            self.set_fill_color(*fill_color)
        else:
            self.set_fill_color(255, 255, 255)
        self.set_font('Helvetica', '', font_size)
        if aligns is None:
            aligns = ['L'] * len(cells)
        for i, (cell, w) in enumerate(zip(cells, widths)):
            align = aligns[i] if i < len(aligns) else 'L'
            self.cell(w, 6, sanitize(str(cell)), border=1, fill=(fill_color is not None), align=align)
        self.ln()

def trunc(s, n=30):
    s = sanitize(str(s))
    return s[:n-2] + '..' if len(s) > n else s

pdf = PDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_margins(15, 15, 15)

# ── Page 1: Cover ─────────────────────────────────────────────────────────────
pdf.add_page()
pdf.set_font('Helvetica', 'B', 28)
pdf.set_text_color(30, 30, 80)
pdf.ln(40)
pdf.cell(0, 14, 'MQL Funnel Analysis Report', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.set_font('Helvetica', '', 14)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 10, f'Generated: {date.today().isoformat()}', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.cell(0, 10, f'Total MQLs: {total}', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.set_text_color(0, 0, 0)
pdf.ln(20)

# Quick bucket summary on cover
pdf.set_font('Helvetica', 'B', 11)
pdf.cell(0, 8, 'Funnel Outcome Summary', align='C', new_x='LMARGIN', new_y='NEXT')
pdf.ln(2)
cover_cols = ['Bucket', 'Count', '% of Total']
cover_widths = [80, 50, 50]
# Draw centered
x_start = (pdf.w - sum(cover_widths)) / 2
pdf.set_x(x_start)
pdf.set_fill_color(204, 204, 204)
pdf.set_font('Helvetica', 'B', 10)
for col, w in zip(cover_cols, cover_widths):
    pdf.cell(w, 7, col, border=1, fill=True, align='C')
pdf.ln()
for b in BUCKETS:
    cnt = bucket_counts.get(b, 0)
    pct = 100.0 * cnt / total if total else 0
    color = BUCKET_COLORS.get(b, (255, 255, 255))
    pdf.set_x(x_start)
    pdf.set_fill_color(*color)
    pdf.set_font('Helvetica', 'B' if b == 'CONVERTED' else '', 10)
    pdf.cell(cover_widths[0], 6, b, border=1, fill=True, align='L')
    pdf.cell(cover_widths[1], 6, str(cnt), border=1, fill=True, align='C')
    pdf.cell(cover_widths[2], 6, f'{pct:.1f}%', border=1, fill=True, align='C')
    pdf.ln()

# ── Page 2: Executive Summary ─────────────────────────────────────────────────
pdf.add_page()
pdf.section_header('Executive Summary')
pdf.set_font('Helvetica', '', 10)

n_conv = bucket_counts.get('CONVERTED', 0)
n_nurt = bucket_counts.get('NURTURING', 0)
n_disq = bucket_counts.get('DISQUALIFIED', 0)
n_active = bucket_counts.get('ACTIVE MQL', 0)
overall_conv_rate = 100.0 * n_conv / total if total else 0

bullets = []
bullets.append(f"Total MQLs analyzed: {total}. Overall conversion rate: {overall_conv_rate:.1f}% ({n_conv} converted, {n_nurt} nurturing, {n_disq} disqualified, {n_active} active).")

def safe(s):
    """Remove or replace non-latin-1 characters."""
    return s.encode('latin-1', errors='replace').decode('latin-1')

if sorted_sources:
    top_src = sorted_sources[0]
    top_src_total = source_data[top_src]['total']
    top_src_conv = conv_rate(source_data[top_src])
    bullets.append(f"'{top_src}' is the highest-volume source with {top_src_total} leads ({100.0*top_src_total/total:.1f}% of total) and a {top_src_conv:.1f}% conversion rate.")

bullets.append(f"Best-converting source: '{best_conv_source}' with {conv_rate(source_data[best_conv_source]):.1f}% conversion rate ({source_data[best_conv_source]['total']} leads).")

if nurturing_leads:
    top_nr_count = nurturing_reason_counts.get(top_nurt_reason, 0)
    top_nr_pct = 100.0 * top_nr_count / len(nurturing_leads) if nurturing_leads else 0
    bullets.append(f"Top nurturing reason: '{top_nurt_reason}' accounts for {top_nr_count} ({top_nr_pct:.1f}%) of all {len(nurturing_leads)} nurturing leads — indicating a specific lead quality gap.")

if disq_leads:
    top_disq_count = disq_source.get(top_disq_source, 0)
    bullets.append(f"Most disqualifications come from '{top_disq_source}': {top_disq_count} out of {len(disq_leads)} total disqualified leads. Review targeting for this channel.")

if country_data:
    top_country = sorted(country_data.keys(), key=lambda c: country_data[c]['total'], reverse=True)[0]
    tc = country_data[top_country]
    bullets.append(f"Top country by volume: {top_country} with {tc['total']} leads ({conv_rate(tc):.1f}% conversion rate).")

if segment_data:
    best_seg = max(segment_data.keys(), key=lambda s: conv_rate(segment_data[s]))
    bullets.append(f"Best-converting segment: '{best_seg}' with {conv_rate(segment_data[best_seg]):.1f}% conversion rate ({segment_data[best_seg]['total']} leads).")

for b in bullets:
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(5, 6, chr(149), new_x='RIGHT', new_y='TOP')
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 6, sanitize(' ' + b))
    pdf.ln(1)

# ── Page 3: Overall Funnel Distribution ───────────────────────────────────────
pdf.add_page()
pdf.section_header('Overall Funnel Distribution')

# Stage-level table
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Lifecycle Stage:', new_x='LMARGIN', new_y='NEXT')
pdf.ln(1)

stage_cols = ['Lifecycle Stage', 'Count', '% of Total', 'Bucket']
stage_widths = [75, 35, 35, 35]
assert sum(stage_widths) <= 180, f"Stage table too wide: {sum(stage_widths)}"
pdf.table_header_row(stage_cols, stage_widths)

sorted_stages = sorted(stage_counts.keys(), key=lambda s: stage_counts[s], reverse=True)
for i, st in enumerate(sorted_stages):
    cnt = stage_counts[st]
    pct = 100.0 * cnt / total if total else 0
    b = bucket(st)
    color = BUCKET_COLORS.get(b) if i % 2 == 0 else None
    fill = color or ((245, 245, 245) if i % 2 else (255, 255, 255))
    pdf.table_data_row([st, cnt, f'{pct:.1f}%', b], stage_widths, fill_color=fill, aligns=['L','C','C','C'])

pdf.ln(6)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Outcome Bucket:', new_x='LMARGIN', new_y='NEXT')
pdf.ln(1)

bkt_cols = ['Bucket', 'Count', '% of Total']
bkt_widths = [80, 50, 50]
assert sum(bkt_widths) <= 180
pdf.table_header_row(bkt_cols, bkt_widths)
for b in BUCKETS:
    cnt = bucket_counts.get(b, 0)
    pct = 100.0 * cnt / total if total else 0
    color = BUCKET_COLORS.get(b, (255, 255, 255))
    pdf.table_data_row([b, cnt, f'{pct:.1f}%'], bkt_widths, fill_color=color, aligns=['L','C','C'])

# ── Page 4: Source → Outcome Analysis (LANDSCAPE) ────────────────────────────
pdf.add_page(orientation='L')
pdf.section_header('Source -> Outcome Analysis')

# Usable width in landscape = 267mm (297 - 2*15)
src_cols = ['Source', 'Total', 'Converted', 'Nurturing', 'Disqualified', 'Active MQL', 'Conv.%', 'Nurt.%']
src_widths = [60, 22, 26, 26, 30, 26, 22, 22]
# Remaining: 267 - sum = 267 - 234 = 33 → extend Source
assert sum(src_widths) <= 267, f"Source table too wide: {sum(src_widths)}"

pdf.table_header_row(src_cols, src_widths, font_size=8)

for src in sorted_sources:
    d = source_data[src]
    row = [
        trunc(src, 35),
        d['total'],
        d.get('CONVERTED', 0),
        d.get('NURTURING', 0),
        d.get('DISQUALIFIED', 0),
        d.get('ACTIVE MQL', 0),
        f"{conv_rate(d):.1f}%",
        f"{nurt_rate(d):.1f}%",
    ]
    i = sorted_sources.index(src)
    fill = (245, 245, 245) if i % 2 else (255, 255, 255)
    pdf.table_data_row(row, src_widths, fill_color=fill, font_size=8, aligns=['L','C','C','C','C','C','C','C'])

pdf.ln(6)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Source Drill-Down Breakdown (top sub-sources by volume):', new_x='LMARGIN', new_y='NEXT')
pdf.ln(1)

# Filter to top 20 sub-sources
sorted_details = sorted(source_detail_data.keys(), key=lambda k: source_detail_data[k]['total'], reverse=True)[:20]

det_cols = ['Source / Detail', 'Total', 'Converted', 'Nurturing', 'Disqualified', 'Active MQL', 'Conv.%', 'Nurt.%']
det_widths = [75, 22, 26, 26, 30, 26, 22, 22]
assert sum(det_widths) <= 267, f"Detail table too wide: {sum(det_widths)}"
pdf.table_header_row(det_cols, det_widths, font_size=8)

for i, key in enumerate(sorted_details):
    d = source_detail_data[key]
    row = [
        trunc(key, 45),
        d['total'],
        d.get('CONVERTED', 0),
        d.get('NURTURING', 0),
        d.get('DISQUALIFIED', 0),
        d.get('ACTIVE MQL', 0),
        f"{conv_rate(d):.1f}%",
        f"{nurt_rate(d):.1f}%",
    ]
    fill = (245, 245, 245) if i % 2 else (255, 255, 255)
    pdf.table_data_row(row, det_widths, fill_color=fill, font_size=8, aligns=['L','C','C','C','C','C','C','C'])

# ── Page 5: Nurturing Deep-Dive ───────────────────────────────────────────────
pdf.add_page()
pdf.section_header('Nurturing Deep-Dive')

pdf.small_text(f'Total nurturing leads: {len(nurturing_leads)} ({100.0*len(nurturing_leads)/total:.1f}% of all MQLs)')
pdf.ln(3)

# 5a: Reason breakdown
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Nurturing Reason Breakdown:', new_x='LMARGIN', new_y='NEXT')
pdf.ln(1)

nr_sorted = sorted(nurturing_reason_counts.keys(), key=nurturing_reason_counts.get, reverse=True)
nr_cols = ['Nurturing Reason', 'Count', '% of Nurturing Leads']
nr_widths = [100, 30, 50]
assert sum(nr_widths) <= 180
pdf.table_header_row(nr_cols, nr_widths)

for i, r in enumerate(nr_sorted):
    cnt = nurturing_reason_counts[r]
    pct = 100.0 * cnt / len(nurturing_leads) if nurturing_leads else 0
    fill = (255, 253, 231) if i % 2 == 0 else (255, 255, 255)
    pdf.table_data_row([trunc(r, 55), cnt, f'{pct:.1f}%'], nr_widths, fill_color=fill, aligns=['L','C','C'])

pdf.ln(5)

# 5b: Reason × Source heatmap (top 5 reasons × top 5 sources)
top5_reasons = nr_sorted[:5]
top5_sources = sorted(source_data.keys(), key=lambda s: source_data[s]['total'], reverse=True)[:5]

if top5_reasons and top5_sources:
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Reason x Source (top 5 reasons x top 5 sources):', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(1)

    hm_reason_col_w = 55
    hm_src_col_w = int((180 - hm_reason_col_w) / len(top5_sources))
    hm_widths = [hm_reason_col_w] + [hm_src_col_w] * len(top5_sources)
    assert sum(hm_widths) <= 180 + 2

    pdf.set_fill_color(204, 204, 204)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.cell(hm_reason_col_w, 7, 'Reason \\ Source', border=1, fill=True)
    for src in top5_sources:
        pdf.cell(hm_src_col_w, 7, trunc(src, 18), border=1, fill=True, align='C')
    pdf.ln()

    for i, r in enumerate(top5_reasons):
        fill = (255, 253, 231) if i % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*fill)
        pdf.set_font('Helvetica', '', 8)
        pdf.cell(hm_reason_col_w, 6, trunc(r, 30), border=1, fill=True)
        for src in top5_sources:
            cnt = reason_source[r].get(src, 0)
            pdf.cell(hm_src_col_w, 6, str(cnt) if cnt > 0 else '-', border=1, fill=True, align='C')
        pdf.ln()

pdf.ln(4)

# 5c: Reason × Segment
if top5_reasons:
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Reason x Segment:', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(1)

    all_segs = sorted(segment_data.keys())
    rs_reason_w = 65
    rs_seg_w = int((180 - rs_reason_w) / max(len(all_segs), 1))
    rs_widths = [rs_reason_w] + [rs_seg_w] * len(all_segs)

    pdf.set_fill_color(204, 204, 204)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(rs_reason_w, 7, 'Reason', border=1, fill=True)
    for seg in all_segs:
        pdf.cell(rs_seg_w, 7, trunc(seg, 15), border=1, fill=True, align='C')
    pdf.ln()

    for i, r in enumerate(top5_reasons):
        fill = (255, 253, 231) if i % 2 == 0 else (255, 255, 255)
        pdf.set_fill_color(*fill)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(rs_reason_w, 6, trunc(r, 35), border=1, fill=True)
        for seg in all_segs:
            cnt = reason_segment[r].get(seg, 0)
            pdf.cell(rs_seg_w, 6, str(cnt) if cnt > 0 else '-', border=1, fill=True, align='C')
        pdf.ln()

pdf.ln(4)
pdf.set_font('Helvetica', 'BI', 9)
pdf.cell(0, 6, 'Key observations:', new_x='LMARGIN', new_y='NEXT')
pdf.set_font('Helvetica', '', 9)
if top5_reasons:
    obs = [
        f"1. '{top5_reasons[0]}' is the dominant nurturing reason — Marketing should investigate whether this reflects intent gaps in lead gen or AE qualification criteria.",
        f"2. Leads without a populated nurturing reason may indicate incomplete CRM data hygiene — consider making this field mandatory.",
        f"3. Sources with high nurturing rates but low disqualification suggest leads are 'not yet ready' rather than wrong-fit — retargeting campaigns may be effective.",
        f"4. High nurturing rates from paid channels suggest ad targeting may be attracting lower-intent audiences.",
    ]
    for o in obs:
        pdf.multi_cell(0, 5, sanitize(o))
        pdf.ln(1)

# ── Page 6: Disqualified Analysis (LANDSCAPE) ────────────────────────────────
pdf.add_page(orientation='L')
pdf.section_header('Disqualified (Not ICP / Lost) Analysis')

pdf.small_text(f'Total disqualified leads: {len(disq_leads)} ({100.0*len(disq_leads)/total:.1f}% of all MQLs)')
pdf.ln(2)

# Source + Country side by side (in text flow)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Source:', new_x='LMARGIN', new_y='NEXT')
pdf.ln(1)

dsq_s_cols = ['Source', 'Disqualified', '% of Disq.']
dsq_s_widths = [90, 40, 40]
pdf.table_header_row(dsq_s_cols, dsq_s_widths)
for i, (src, cnt) in enumerate(sorted(disq_source.items(), key=lambda x: x[1], reverse=True)):
    pct = 100.0 * cnt / len(disq_leads) if disq_leads else 0
    fill = (255, 235, 238) if i % 2 == 0 else (255, 255, 255)
    pdf.table_data_row([trunc(src, 50), cnt, f'{pct:.1f}%'], dsq_s_widths, fill_color=fill, aligns=['L','C','C'])

pdf.ln(4)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Country:', new_x='LMARGIN', new_y='NEXT')
pdf.ln(1)

dsq_c_cols = ['Country', 'Disqualified', '% of Disq.']
dsq_c_widths = [90, 40, 40]
pdf.table_header_row(dsq_c_cols, dsq_c_widths)
for i, (cty, cnt) in enumerate(sorted(disq_country.items(), key=lambda x: x[1], reverse=True)):
    pct = 100.0 * cnt / len(disq_leads) if disq_leads else 0
    fill = (255, 235, 238) if i % 2 == 0 else (255, 255, 255)
    pdf.table_data_row([trunc(cty, 50), cnt, f'{pct:.1f}%'], dsq_c_widths, fill_color=fill, aligns=['L','C','C'])

pdf.ln(4)
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Full Disqualified Lead List:', new_x='LMARGIN', new_y='NEXT')
pdf.ln(1)

# Landscape: 267mm usable
dl_cols = ['AE', 'Email', 'Country', 'Source', 'Stage']
dl_widths = [45, 70, 35, 55, 35]
# total = 240, fits in 267
assert sum(dl_widths) <= 267
pdf.table_header_row(dl_cols, dl_widths, font_size=8)

for i, l in enumerate(sorted(disq_leads, key=lambda x: x['country'])):
    email = trunc(l['email'], 30)
    fill = (255, 235, 238) if i % 2 == 0 else (255, 255, 255)
    pdf.table_data_row([
        trunc(l['ae'], 25),
        email,
        trunc(l['country'], 20),
        trunc(l['source'], 30),
        trunc(l['stage'], 20),
    ], dl_widths, fill_color=fill, font_size=8, aligns=['L','L','L','L','L'])

# ── Page 7: Converted Leads Analysis (LANDSCAPE) ─────────────────────────────
pdf.add_page(orientation='L')
pdf.section_header('Converted Leads Analysis (SQL / Opportunity / Customer)')

pdf.small_text(f'Total converted leads: {len(conv_leads)} ({100.0*len(conv_leads)/total:.1f}% of all MQLs)')
pdf.ln(2)

# Source breakdown
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Source:', new_x='LMARGIN', new_y='NEXT')
pdf.ln(1)

cv_s_cols = ['Source', 'Converted', '% of Converted']
cv_s_widths = [90, 40, 50]
pdf.table_header_row(cv_s_cols, cv_s_widths)
for i, (src, cnt) in enumerate(sorted(conv_source.items(), key=lambda x: x[1], reverse=True)):
    pct = 100.0 * cnt / len(conv_leads) if conv_leads else 0
    fill = (232, 245, 233) if i % 2 == 0 else (255, 255, 255)
    pdf.table_data_row([trunc(src, 50), cnt, f'{pct:.1f}%'], cv_s_widths, fill_color=fill, aligns=['L','C','C'])

pdf.ln(4)

# Country breakdown
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Country:', new_x='LMARGIN', new_y='NEXT')
pdf.ln(1)

cv_c_cols = ['Country', 'Converted', '% of Converted']
cv_c_widths = [90, 40, 50]
pdf.table_header_row(cv_c_cols, cv_c_widths)
for i, (cty, cnt) in enumerate(sorted(conv_country.items(), key=lambda x: x[1], reverse=True)):
    pct = 100.0 * cnt / len(conv_leads) if conv_leads else 0
    fill = (232, 245, 233) if i % 2 == 0 else (255, 255, 255)
    pdf.table_data_row([trunc(cty, 50), cnt, f'{pct:.1f}%'], cv_c_widths, fill_color=fill, aligns=['L','C','C'])

pdf.ln(4)

# Segment breakdown
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Segment:', new_x='LMARGIN', new_y='NEXT')
pdf.ln(1)

cv_seg_cols = ['Segment', 'Converted', '% of Converted']
cv_seg_widths = [90, 40, 50]
pdf.table_header_row(cv_seg_cols, cv_seg_widths)
for i, (seg, cnt) in enumerate(sorted(conv_segment.items(), key=lambda x: x[1], reverse=True)):
    pct = 100.0 * cnt / len(conv_leads) if conv_leads else 0
    fill = (232, 245, 233) if i % 2 == 0 else (255, 255, 255)
    pdf.table_data_row([trunc(seg, 50), cnt, f'{pct:.1f}%'], cv_seg_widths, fill_color=fill, aligns=['L','C','C'])

pdf.ln(4)

# Full converted lead list
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Full Converted Lead List:', new_x='LMARGIN', new_y='NEXT')
pdf.ln(1)

cl_cols = ['AE', 'Email', 'Country', 'Source', 'Stage', 'Units']
cl_widths = [42, 68, 33, 50, 38, 20]
# total = 251 fits in 267
assert sum(cl_widths) <= 267
pdf.table_header_row(cl_cols, cl_widths, font_size=8)

for i, l in enumerate(sorted(conv_leads, key=lambda x: x['stage'])):
    fill = (232, 245, 233) if i % 2 == 0 else (255, 255, 255)
    pdf.table_data_row([
        trunc(l['ae'], 25),
        trunc(l['email'], 30),
        trunc(l['country'], 18),
        trunc(l['source'], 28),
        trunc(l['stage'], 22),
        str(l['units']) if l['units'] else '-',
    ], cl_widths, fill_color=fill, font_size=8, aligns=['L','L','L','L','L','C'])

# ── Page 8: Country × Outcome Matrix (LANDSCAPE) ─────────────────────────────
pdf.add_page(orientation='L')
pdf.section_header('Country x Outcome Matrix (Top 10 Countries)')

pdf.small_text('Note: "Europe" is flagged as a data quality issue (non-specific country) and shown separately.')
pdf.ln(3)

cm_cols = ['Country', 'Total', 'Converted', 'Nurturing', 'Disqualified', 'Active MQL', 'Conv.%']
cm_widths = [55, 25, 30, 30, 35, 32, 30]
# total = 237 fits in 267
assert sum(cm_widths) <= 267
pdf.table_header_row(cm_cols, cm_widths, font_size=9)

for i, cty in enumerate(top10_countries):
    d = country_data[cty]
    flag = ' [DATA QUALITY]' if cty.lower() == 'europe' else ''
    fill = (245, 245, 245) if i % 2 else (255, 255, 255)
    pdf.table_data_row([
        trunc(cty + flag, 30),
        d['total'],
        d.get('CONVERTED', 0),
        d.get('NURTURING', 0),
        d.get('DISQUALIFIED', 0),
        d.get('ACTIVE MQL', 0),
        f"{conv_rate(d):.1f}%",
    ], cm_widths, fill_color=fill, font_size=9, aligns=['L','C','C','C','C','C','C'])

# ── Page 9: Segment Analysis ──────────────────────────────────────────────────
pdf.add_page()
pdf.section_header('Segment Analysis')

seg_cols = ['Segment', 'Total', 'Converted', 'Nurturing', 'Disqualified', 'Active MQL', 'Conv.%']
seg_widths = [40, 22, 28, 28, 32, 28, 22]
# total = 200 — slightly over 180; use 8pt and landscape alt: reduce columns
seg_widths = [38, 22, 27, 27, 32, 27, 22]  # total = 195 still over
# Let's keep it simple for portrait: use 7 columns with smaller widths
seg_widths = [35, 20, 25, 25, 30, 25, 20]  # total = 180 exactly
assert sum(seg_widths) <= 180, f"Segment table: {sum(seg_widths)}"
pdf.table_header_row(seg_cols, seg_widths, font_size=9)

for i, seg in enumerate(sorted(segment_data.keys(), key=lambda s: segment_data[s]['total'], reverse=True)):
    d = segment_data[seg]
    fill = (245, 245, 245) if i % 2 else (255, 255, 255)
    pdf.table_data_row([
        trunc(seg, 20),
        d['total'],
        d.get('CONVERTED', 0),
        d.get('NURTURING', 0),
        d.get('DISQUALIFIED', 0),
        d.get('ACTIVE MQL', 0),
        f"{conv_rate(d):.1f}%",
    ], seg_widths, fill_color=fill, font_size=9, aligns=['L','C','C','C','C','C','C'])

pdf.ln(8)

# AE Performance
if ae_data:
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'AE Performance:', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(1)

    ae_cols = ['AE', 'Total', 'Converted', 'Nurturing', 'Disqualified', 'Conv.%']
    ae_widths = [55, 22, 28, 28, 32, 22]
    # total = 187 slightly over; adjust
    ae_widths = [52, 22, 28, 28, 32, 18]  # = 180
    assert sum(ae_widths) <= 180
    pdf.table_header_row(ae_cols, ae_widths, font_size=9)

    for i, ae in enumerate(sorted(ae_data.keys(), key=lambda a: ae_data[a]['total'], reverse=True)):
        d = ae_data[ae]
        fill = (245, 245, 245) if i % 2 else (255, 255, 255)
        pdf.table_data_row([
            trunc(ae, 30),
            d['total'],
            d.get('CONVERTED', 0),
            d.get('NURTURING', 0),
            d.get('DISQUALIFIED', 0),
            f"{conv_rate(d):.1f}%",
        ], ae_widths, fill_color=fill, font_size=9, aligns=['L','C','C','C','C','C'])

# ── Page 10: Recommendations ──────────────────────────────────────────────────
pdf.add_page()
pdf.section_header('Recommendations for Marketing')

pdf.set_font('Helvetica', '', 10)
recs = []

# Dynamic recommendations based on data
if sorted_sources:
    low_conv_sources = [s for s in sorted_sources if source_data[s]['total'] >= 5 and conv_rate(source_data[s]) < 15]
    for s in low_conv_sources[:2]:
        recs.append(f"LOW CONVERSION — '{s}': {conv_rate(source_data[s]):.1f}% conversion rate with {source_data[s]['total']} leads. Consider adding friction to forms or refining targeting to improve lead quality before investing further.")

    high_conv_sources = [s for s in sorted_sources if conv_rate(source_data[s]) >= 20]
    for s in high_conv_sources[:2]:
        recs.append(f"SCALE UP — '{s}': {conv_rate(source_data[s]):.1f}% conversion rate. This channel produces quality pipeline — consider increasing budget allocation.")

if nurturing_reason_counts:
    top_nr = nr_sorted[0] if nr_sorted else None
    if top_nr:
        recs.append(f"LEAD QUALIFICATION — '{top_nr}' is the top nurturing reason. Add qualifying questions to landing page forms (e.g., property count, business type) to filter out lower-intent leads earlier in the funnel.")

# Europe data quality
europe_count = country_data.get('Europe', {}).get('total', 0)
if europe_count > 0:
    recs.append(f"DATA QUALITY — {europe_count} leads have 'Europe' as country (non-specific). Fix UTM tracking or form country fields to capture specific countries — this blocks accurate regional analysis.")

if disq_leads:
    top_disq_s = max(disq_source, key=disq_source.get)
    recs.append(f"TARGETING — '{top_disq_s}' generates the most disqualified leads ({disq_source[top_disq_s]} Not ICP/Lost). Review audience targeting parameters for this channel to reduce wasted spend.")

if conv_leads and conv_country:
    top_conv_country = max(conv_country, key=conv_country.get)
    recs.append(f"GEO FOCUS — {top_conv_country} generates the most conversions ({conv_country[top_conv_country]}). Prioritize campaigns, localization, and AE coverage in this market.")

# Fill up to 7 recs
if len(recs) < 5:
    recs.append("NURTURE TRACK — Build an automated nurturing email sequence for leads stuck in ACTIVE MQL > 14 days to re-qualify or move to nurturing faster.")
    recs.append("CRM HYGIENE — Ensure 'Nurturing Reason' is a required field in HubSpot when AEs move leads to Nurturing stage — missing reasons reduce analytical accuracy.")

for j, rec in enumerate(recs[:7], 1):
    parts = rec.split(' — ', 1)
    if len(parts) == 2:
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(5, 6, f'{j}.', new_x='RIGHT', new_y='TOP')
        pdf.cell(35, 6, f'[{parts[0]}]', new_x='RIGHT', new_y='TOP')
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 6, sanitize(f' {parts[1]}'))
    else:
        pdf.set_font('Helvetica', '', 10)
        pdf.multi_cell(0, 6, sanitize(f'{j}. {rec}'))
    pdf.ln(2)

# ── Page 11: Appendix — Full Lead List (LANDSCAPE) ───────────────────────────
pdf.add_page(orientation='L')
pdf.section_header('Appendix — Full Lead List')

pdf.small_text(f'All {total} MQL leads sorted by bucket then segment.')
pdf.ln(2)

app_cols = ['Contact ID', 'AE', 'Segment', 'Email', 'Country', 'Source', 'Units', 'Stage', 'Nurt. Reason']
app_widths = [25, 38, 22, 58, 28, 38, 14, 28, 38]
# total = 289 — over 267. Reduce.
app_widths = [22, 35, 20, 55, 25, 35, 12, 28, 35]
# total = 267 exactly
assert sum(app_widths) <= 267, f"Appendix table: {sum(app_widths)}"
pdf.table_header_row(app_cols, app_widths, font_size=7)

sorted_leads = sorted(leads, key=lambda l: (l['bucket'], l['segment'], l['country']))

for i, l in enumerate(sorted_leads):
    b = l['bucket']
    color = BUCKET_COLORS.get(b, (255, 255, 255))
    fill = color if i % 2 == 0 else tuple(min(255, c + 10) for c in color)
    pdf.table_data_row([
        trunc(l['contact_id'], 14),
        trunc(l['ae'], 20),
        trunc(l['segment'], 12),
        trunc(l['email'], 30),
        trunc(l['country'], 15),
        trunc(l['source'], 22),
        str(l['units']) if l['units'] else '-',
        trunc(l['stage'], 18),
        trunc(l['nurturing_reason'], 22),
    ], app_widths, fill_color=fill, font_size=7, aligns=['C','L','L','L','L','L','C','L','L'])

# ── Save PDF ──────────────────────────────────────────────────────────────────
pdf.output(output_path)
print(f"\nPDF saved to: {output_path}")
print(f"Total pages: {pdf.page}")
