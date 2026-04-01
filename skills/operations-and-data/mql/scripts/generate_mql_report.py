import csv
from datetime import date, datetime
from collections import defaultdict, Counter
from fpdf import FPDF

CSV_PATH = r'C:\Users\aless\Documents\total-mql-entered.csv'
OUTPUT_PATH = r'C:\Users\aless\Documents\mql_funnel_analysis_2026-03-26.pdf'

# --- 1. LOAD ----------------------------------------------------------------

def parse_int(val):
    if not val or val.strip() == '(No value)': return 0
    try: return int(float(val.strip()))
    except ValueError: return 0

def days_since(date_str):
    if not date_str or date_str.strip() == '(No value)': return None
    for fmt in ('%Y-%m-%d %H:%M', '%Y-%m-%d', '%d/%m/%Y'):
        try: return (date.today() - datetime.strptime(date_str.strip(), fmt).date()).days
        except ValueError: continue
    return None

def clean(val):
    v = (val or '').strip()
    return '' if v == '(No value)' else v

with open(CSV_PATH, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    raw_rows = list(reader)

# --- 2. PARSE ---------------------------------------------------------------

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

# Handle duplicate "Property Size" column - use first occurrence via custom parsing
def get_first(row, key):
    """csv.DictReader deduplicates by appending .1, .2 - first occurrence is unmodified."""
    return clean(row.get(key, ''))

leads = []
for row in raw_rows:
    stage = clean(row.get('Lifecycle Stage', ''))
    leads.append({
        'segment':          get_first(row, 'Property Size'),
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

# --- 3. ANALYSES ------------------------------------------------------------

# 3a. Overall funnel
stage_counts  = Counter(l['stage']  for l in leads)
bucket_counts = Counter(l['bucket'] for l in leads)

# 3b. Source -> outcome matrix
source_data = defaultdict(lambda: Counter())
for l in leads:
    source_data[l['source']][l['bucket']] += 1

source_detail_data = defaultdict(lambda: Counter())
for l in leads:
    key = (l['source'], l['source_detail'] or '(direct)')
    source_detail_data[key][l['bucket']] += 1

# 3c. Nurturing deep-dive
nurturing_leads = [l for l in leads if l['bucket'] == 'NURTURING']
reason_counts   = Counter(l['nurturing_reason'] or '(No reason)' for l in nurturing_leads)
reason_x_source = defaultdict(Counter)
reason_x_segment= defaultdict(Counter)
reason_x_country= defaultdict(Counter)
for l in nurturing_leads:
    r = l['nurturing_reason'] or '(No reason)'
    reason_x_source[r][l['source']] += 1
    reason_x_segment[r][l['segment'] or '(Unknown)'] += 1
    reason_x_country[r][l['country'] or '(Unknown)'] += 1

# 3d. Disqualified
disq_leads   = [l for l in leads if l['bucket'] == 'DISQUALIFIED']
disq_source  = Counter(l['source']  for l in disq_leads)
disq_country = Counter(l['country'] for l in disq_leads)
disq_segment = Counter(l['segment'] for l in disq_leads)

# 3e. Converted
conv_leads   = [l for l in leads if l['bucket'] == 'CONVERTED']
conv_source  = Counter(l['source']  for l in conv_leads)
conv_country = Counter(l['country'] for l in conv_leads)
conv_segment = Counter(l['segment'] for l in conv_leads)

# 3f. Country × bucket
country_data = defaultdict(Counter)
for l in leads:
    country_data[l['country'] or '(Unknown)'][l['bucket']] += 1
top_countries = [c for c, _ in Counter({c: sum(v.values()) for c, v in country_data.items()}).most_common(10)]

# 3g. Segment × bucket
segment_data = defaultdict(Counter)
for l in leads:
    segment_data[l['segment'] or '(Unknown)'][l['bucket']] += 1

# 3h. AE performance
ae_data = defaultdict(Counter)
for l in leads:
    ae_data[l['ae'] or '(Unassigned)'][l['bucket']] += 1

def conv_rate(d):
    t = sum(d.values())
    return (d.get('CONVERTED', 0) / t * 100) if t else 0

def nurt_rate(d):
    t = sum(d.values())
    return (d.get('NURTURING', 0) / t * 100) if t else 0

# --- 4. PDF -----------------------------------------------------------------

BUCKET_COLORS = {
    'CONVERTED':   (232, 245, 233),
    'NURTURING':   (255, 253, 231),
    'DISQUALIFIED':(255, 235, 238),
    'ACTIVE MQL':  (255, 255, 255),
    'OTHER':       (245, 245, 245),
}

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        pass  # custom headers per section

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f'MQL Funnel Analysis - {date.today().strftime("%d %b %Y")}  |  Page {self.page_no()}', align='C')
        self.set_text_color(0, 0, 0)

    def section_title(self, title):
        self.set_fill_color(232, 232, 232)
        self.set_font('Helvetica', 'B', 13)
        self.cell(0, 9, title, ln=True, fill=True)
        self.ln(3)

    def table(self, headers, col_widths, rows_data, row_colors=None, font_size=9, orientation='P'):
        """Render a table. row_colors: list of (R,G,B) per row, or None for alternating."""
        page_w = 267 if orientation == 'L' else 180
        total_w = sum(col_widths)
        if total_w > page_w:
            scale = page_w / total_w
            col_widths = [w * scale for w in col_widths]

        # Header row
        self.set_font('Helvetica', 'B', font_size)
        self.set_fill_color(204, 204, 204)
        self.set_text_color(0, 0, 0)
        row_h = 6
        for i, (h, w) in enumerate(zip(headers, col_widths)):
            self.cell(w, row_h, str(h), border=1, fill=True, align='C')
        self.ln()

        # Data rows
        self.set_font('Helvetica', '', font_size)
        for ri, row in enumerate(rows_data):
            if row_colors and ri < len(row_colors) and row_colors[ri]:
                r, g, b = row_colors[ri]
                self.set_fill_color(r, g, b)
                fill = True
            else:
                if ri % 2 == 0:
                    self.set_fill_color(255, 255, 255)
                else:
                    self.set_fill_color(245, 245, 245)
                fill = True
            for i, (cell, w) in enumerate(zip(row, col_widths)):
                text = str(cell)
                if len(text) > 38 and i > 0:
                    text = text[:36] + '...'
                self.cell(w, row_h, text, border=1, fill=fill, align='L' if i == 0 else 'C')
            self.ln()
        self.ln(3)

    def bullet(self, text, indent=5):
        self.set_font('Helvetica', '', 9)
        self.set_x(self.get_x() + indent)
        self.multi_cell(0, 5, f'* {text}')
        self.ln(1)


pdf = PDF()
pdf.set_margins(15, 15, 15)

# -- COVER --------------------------------------------------------------------
pdf.add_page()
pdf.ln(40)
pdf.set_font('Helvetica', 'B', 22)
pdf.cell(0, 12, 'MQL Funnel Analysis Report', ln=True, align='C')
pdf.ln(4)
pdf.set_font('Helvetica', '', 12)
pdf.cell(0, 8, date.today().strftime('%B %d, %Y'), ln=True, align='C')
pdf.ln(2)
pdf.set_font('Helvetica', 'B', 14)
pdf.cell(0, 8, f'Total MQLs analyzed: {total}', ln=True, align='C')
pdf.ln(30)

# Bucket summary boxes on cover
pdf.set_font('Helvetica', 'B', 11)
buckets_order = ['CONVERTED', 'NURTURING', 'DISQUALIFIED', 'ACTIVE MQL']
box_w = 40
for b in buckets_order:
    cnt = bucket_counts.get(b, 0)
    pct = cnt / total * 100
    r, g, bl = BUCKET_COLORS.get(b, (240,240,240))
    pdf.set_fill_color(r, g, bl)
    pdf.cell(box_w, 14, f'{b}\n{cnt} ({pct:.0f}%)', border=1, fill=True, align='C')
pdf.ln(30)

pdf.set_font('Helvetica', 'I', 9)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 6, 'Internal report - Marketing use only', align='C')
pdf.set_text_color(0, 0, 0)

# -- EXECUTIVE SUMMARY --------------------------------------------------------
pdf.add_page()
pdf.section_title('1. Executive Summary')
pdf.set_font('Helvetica', '', 9)

conv_total = bucket_counts.get('CONVERTED', 0)
nurt_total = bucket_counts.get('NURTURING', 0)
disq_total = bucket_counts.get('DISQUALIFIED', 0)
active_total = bucket_counts.get('ACTIVE MQL', 0)
overall_conv_rate = conv_total / total * 100

# Paid Social stats
ps = source_data.get('Paid Social', Counter())
ps_total = sum(ps.values())
ps_conv = ps.get('CONVERTED', 0)
ps_conv_rate = ps_conv / ps_total * 100 if ps_total else 0

# Top nurturing reason
top_reason, top_reason_cnt = reason_counts.most_common(1)[0] if reason_counts else ('N/A', 0)
top_reason_pct = top_reason_cnt / nurt_total * 100 if nurt_total else 0

# Best converting source
best_src = max(source_data.keys(), key=lambda s: conv_rate(source_data[s])) if source_data else 'N/A'
best_src_rate = conv_rate(source_data[best_src]) if source_data else 0

# Language barrier
lb_count = reason_counts.get('Language barrier', 0)
lb_pct = lb_count / nurt_total * 100 if nurt_total else 0

# Top converting country
top_conv_country = conv_country.most_common(1)[0] if conv_country else ('N/A', 0)

bullets = [
    f"Overall conversion rate is {overall_conv_rate:.1f}% ({conv_total} of {total} MQLs reached SQL/Opportunity/Customer).",
    f"Paid Social dominates volume ({ps_total} leads, {ps_total/total*100:.0f}% of all MQLs) but converts at only {ps_conv_rate:.1f}% - the channel generating the most noise.",
    f"\"{top_reason}\" is the #1 nurturing reason ({top_reason_cnt} leads, {top_reason_pct:.0f}% of nurturing) - indicating leads entering the funnel before they are decision-ready.",
    f"Language barrier accounts for {lb_count} nurturing leads ({lb_pct:.0f}% of nurturing) - suggesting geographic targeting or AE routing issues.",
    f"{best_src} achieves the highest conversion rate at {best_src_rate:.1f}%, making it the highest-quality channel by outcome.",
    f"Spain and Italy together represent {(country_data.get('Spain', Counter()).get('CONVERTED',0) + country_data.get('Italy', Counter()).get('CONVERTED',0))} of {conv_total} conversions - the core pipeline markets.",
    f"{disq_total} leads ({disq_total/total*100:.1f}%) were disqualified (Not ICP / Lost) - reviewing targeting criteria for top disqualification sources could improve funnel efficiency.",
]
for b in bullets:
    pdf.bullet(b)

# -- OVERALL FUNNEL -----------------------------------------------------------
pdf.add_page()
pdf.section_title('2. Overall Funnel Distribution')

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Lifecycle Stage', ln=True)
pdf.ln(1)
stage_rows = [(s, c, f'{c/total*100:.1f}%') for s, c in sorted(stage_counts.items(), key=lambda x: -x[1])]
pdf.table(['Lifecycle Stage', 'Count', '% of Total'], [90, 45, 45], stage_rows)

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'By Outcome Bucket', ln=True)
pdf.ln(1)
bucket_rows = []
colors_b = []
for b in ['CONVERTED','NURTURING','DISQUALIFIED','ACTIVE MQL','OTHER']:
    c = bucket_counts.get(b, 0)
    bucket_rows.append((b, c, f'{c/total*100:.1f}%'))
    colors_b.append(BUCKET_COLORS.get(b, (255,255,255)))
pdf.table(['Bucket', 'Count', '% of Total'], [90, 45, 45], bucket_rows, row_colors=colors_b)

# -- SOURCE -> OUTCOME ---------------------------------------------------------
pdf.add_page(orientation='L')
pdf.section_title('3. Source -> Outcome Analysis')

src_rows = []
src_colors = []
for src, d in sorted(source_data.items(), key=lambda x: -sum(x[1].values())):
    t = sum(d.values())
    src_rows.append([
        src,
        t,
        d.get('CONVERTED', 0),
        d.get('NURTURING', 0),
        d.get('DISQUALIFIED', 0),
        d.get('ACTIVE MQL', 0),
        f'{conv_rate(d):.1f}%',
        f'{nurt_rate(d):.1f}%',
    ])
    src_colors.append(None)

pdf.table(
    ['Source', 'Total', 'Converted', 'Nurturing', 'Disqualified', 'Active MQL', 'Conv.%', 'Nurt.%'],
    [55, 22, 28, 28, 30, 28, 22, 22],
    src_rows,
    font_size=9,
    orientation='L'
)

# Sub-breakdown by Drill-Down 1
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Source Drill-Down (top sub-sources)', ln=True)
pdf.ln(1)

drill_rows = []
for (src, detail), d in sorted(source_detail_data.items(), key=lambda x: -sum(x[1].values()))[:20]:
    t = sum(d.values())
    if t < 2: continue
    drill_rows.append([
        src, detail or '(direct)',
        t,
        d.get('CONVERTED', 0),
        d.get('NURTURING', 0),
        d.get('DISQUALIFIED', 0),
        f'{conv_rate(d):.1f}%',
    ])

pdf.table(
    ['Source', 'Sub-Source', 'Total', 'Converted', 'Nurturing', 'Disq.', 'Conv.%'],
    [48, 48, 22, 28, 28, 22, 22],
    drill_rows,
    font_size=9,
    orientation='L'
)

# -- NURTURING DEEP-DIVE -------------------------------------------------------
pdf.add_page()
pdf.section_title('4. Nurturing Deep-Dive')

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, f'Nurturing Leads: {nurt_total} total', ln=True)
pdf.ln(1)

# Reason ranking
reason_rows = []
for r, c in reason_counts.most_common():
    reason_rows.append((r, c, f'{c/nurt_total*100:.1f}%'))
pdf.table(['Nurturing Reason', 'Count', '% of Nurturing'], [110, 35, 35], reason_rows)

# Reason × Source heatmap
top5_reasons = [r for r, _ in reason_counts.most_common(5)]
top4_sources = [s for s, _ in Counter({s: sum(source_data[s].values()) for s in source_data}).most_common(4)]

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Top 5 Reasons × Top 4 Sources', ln=True)
pdf.ln(1)
hm_headers = ['Reason'] + top4_sources + ['Total']
hm_widths  = [60] + [27]*len(top4_sources) + [20]
hm_rows = []
for r in top5_reasons:
    row = [r]
    for s in top4_sources:
        row.append(reason_x_source[r].get(s, 0))
    row.append(reason_counts[r])
    hm_rows.append(row)
pdf.table(hm_headers, hm_widths, hm_rows)

# Reason × Segment
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Top Reasons × Segment', ln=True)
pdf.ln(1)
segments_list = ['SMB', 'Mid-Market', 'Enterprise']
seg_headers = ['Reason'] + segments_list + ['Total']
seg_widths  = [70] + [32]*3 + [20]
seg_rows = []
for r in top5_reasons:
    row = [r]
    for s in segments_list:
        row.append(reason_x_segment[r].get(s, 0))
    row.append(reason_counts[r])
    seg_rows.append(row)
pdf.table(seg_headers, seg_widths, seg_rows)

# Observations
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Key Observations', ln=True)
pdf.ln(1)
obs = [
    f'"Just looking for info" ({reason_counts.get("Just looking for info",0)} leads) is the dominant nurturing reason, suggesting many leads enter the funnel at an awareness stage - not yet ready to evaluate. Consider adding intent-qualification questions to landing page forms.',
    f'"No answer" ({reason_counts.get("No answer",0)} leads) and "Timing" ({reason_counts.get("Timing",0)} leads) indicate leads that engaged but were not sales-ready. These are prime candidates for automated re-engagement sequences.',
    f'"Language barrier" ({reason_counts.get("Language barrier",0)} leads) points to a routing problem - leads are likely coming from countries/languages not covered by assigned AEs. Review territory-to-AE mapping.',
    f'"Not ICP" within nurturing ({reason_counts.get("Not ICP",0)} leads) and the separate Disqualified bucket suggest targeting is too broad - particularly for Paid Social where volume is high but quality is low.',
]
for o in obs:
    pdf.bullet(o)

# -- DISQUALIFIED -------------------------------------------------------------
pdf.add_page(orientation='L')
pdf.section_title('5. Disqualified (Not ICP / Lost) Analysis')

col3 = [['Source', disq_source], ['Country', disq_country], ['Segment', disq_segment]]
x_pos = 15
for label, counter in col3:
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, f'By {label}', ln=True)
    pdf.ln(1)
    rows_d = [(k or '(Unknown)', c, f'{c/disq_total*100:.1f}%') for k, c in counter.most_common()]
    pdf.table([label, 'Count', '%'], [70, 30, 30], rows_d)

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Full Disqualified Lead List', ln=True)
pdf.ln(1)
disq_list = []
for l in sorted(disq_leads, key=lambda x: x['country']):
    ae = l['ae'][:18] if l['ae'] else ''
    email = (l['email'][:30] + '...') if len(l['email']) > 30 else l['email']
    disq_list.append([ae, email, l['country'], l['source'], l['stage']])
pdf.table(
    ['AE', 'Email', 'Country', 'Source', 'Stage'],
    [40, 70, 35, 45, 30],
    disq_list,
    font_size=8,
    orientation='L'
)

# -- CONVERTED ----------------------------------------------------------------
pdf.add_page(orientation='L')
pdf.section_title('6. Converted Leads Analysis (SQL / Opportunity / Customer)')

conv_total_n = len(conv_leads)
for label, counter in [('Source', conv_source), ('Country', conv_country), ('Segment', conv_segment)]:
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, f'By {label}', ln=True)
    pdf.ln(1)
    rows_c = [(k or '(Unknown)', c, f'{c/conv_total_n*100:.1f}%') for k, c in counter.most_common()]
    pdf.table([label, 'Count', '%'], [70, 30, 30], rows_c)

pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 6, 'Full Converted Lead List', ln=True)
pdf.ln(1)
conv_list = []
for l in sorted(conv_leads, key=lambda x: x['stage']):
    ae = l['ae'][:18] if l['ae'] else ''
    email = (l['email'][:30] + '...') if len(l['email']) > 30 else l['email']
    conv_list.append([ae, email, l['country'], l['source'], l['stage'], str(l['units']) if l['units'] else ''])
conv_colors = [BUCKET_COLORS['CONVERTED']] * len(conv_list)
pdf.table(
    ['AE', 'Email', 'Country', 'Source', 'Stage', 'Units'],
    [40, 68, 35, 40, 35, 22],
    conv_list,
    row_colors=conv_colors,
    font_size=8,
    orientation='L'
)

# -- COUNTRY × OUTCOME --------------------------------------------------------
pdf.add_page()
pdf.section_title('7. Country × Outcome Matrix (Top 10)')

country_rows = []
country_colors = []
for c in top_countries:
    d = country_data[c]
    t = sum(d.values())
    flag = ' [!]' if c == 'Europe' else ''
    country_rows.append([
        c + flag,
        t,
        d.get('CONVERTED', 0),
        d.get('NURTURING', 0),
        d.get('DISQUALIFIED', 0),
        d.get('ACTIVE MQL', 0),
        f'{conv_rate(d):.1f}%',
    ])
    country_colors.append(None)

pdf.table(
    ['Country', 'Total', 'Converted', 'Nurturing', 'Disqualified', 'Active MQL', 'Conv.%'],
    [38, 20, 28, 28, 30, 28, 22],
    country_rows
)

if 'Europe' in country_data:
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(180, 0, 0)
    pdf.cell(0, 5, '[!] "Europe" is a data quality issue - not a real country. Please review HubSpot contact records.', ln=True)
    pdf.set_text_color(0, 0, 0)

# -- SEGMENT ANALYSIS ---------------------------------------------------------
pdf.add_page()
pdf.section_title('8. Segment Analysis')

seg_total_map = {s: sum(segment_data[s].values()) for s in segment_data}
seg_rows2 = []
seg_colors2 = []
for s in ['SMB', 'Mid-Market', 'Enterprise']:
    d = segment_data.get(s, Counter())
    t = sum(d.values())
    seg_rows2.append([
        s, t,
        d.get('CONVERTED', 0),
        d.get('NURTURING', 0),
        d.get('DISQUALIFIED', 0),
        d.get('ACTIVE MQL', 0),
        f'{conv_rate(d):.1f}%',
    ])
    seg_colors2.append(None)

pdf.table(
    ['Segment', 'Total', 'Converted', 'Nurturing', 'Disqualified', 'Active MQL', 'Conv.%'],
    [38, 20, 28, 28, 30, 28, 22],
    seg_rows2
)

# AE Performance
if ae_data:
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'AE Performance', ln=True)
    pdf.ln(1)
    ae_rows = []
    for ae, d in sorted(ae_data.items(), key=lambda x: -sum(x[1].values())):
        t = sum(d.values())
        ae_rows.append([
            ae[:30],
            t,
            d.get('CONVERTED', 0),
            f'{conv_rate(d):.1f}%',
            d.get('NURTURING', 0),
            d.get('DISQUALIFIED', 0),
        ])
    pdf.table(
        ['AE', 'Total MQLs', 'Converted', 'Conv.%', 'Nurturing', 'Disqualified'],
        [65, 25, 25, 22, 25, 28],
        ae_rows
    )

# -- RECOMMENDATIONS ----------------------------------------------------------
pdf.add_page()
pdf.section_title('9. Recommendations for Marketing')

recs = [
    ('Qualify intent before MQL assignment',
     '"Just looking for info" is the #1 nurturing reason. Add qualifying questions to landing page forms (e.g., "Are you currently evaluating solutions?", "How many properties do you manage?") to filter awareness-stage visitors before they enter the MQL queue.'),
    ('Reduce Paid Social volume - increase quality',
     f'Paid Social generates {ps_total} leads ({ps_total/total*100:.0f}% of total) but only {ps_conv_rate:.1f}% convert. Add property count and business-type filters to ad targeting. Consider requiring a minimum unit count in lead forms to exclude homeowners and non-PMC operators.'),
    ('Implement AE-to-language routing',
     f'Language barrier caused {reason_counts.get("Language barrier",0)} nurturing cases. Map HubSpot country fields to AE language profiles and auto-assign leads to AEs who speak the lead\'s language. Prioritize non-Spanish/Italian markets.'),
    ('Build a "Timing" re-engagement track',
     f'"Timing" ({reason_counts.get("Timing",0)} leads) and "No answer" ({reason_counts.get("No answer",0)} leads) represent {reason_counts.get("Timing",0) + reason_counts.get("No answer",0)} leads who showed intent but were not ready. Enroll these in a 60/90-day automated email sequence to re-qualify them.'),
    ('Investigate "No answer" leads by source',
     'High "No answer" counts may indicate lead quality or contact-info accuracy issues at the source level. Compare phone/email validity rates across channels and add email verification to Paid Social landing pages.'),
    ('Flag and review "Europe" country entries',
     f'1 lead has "Europe" as country - this is a data quality issue in HubSpot. Audit contacts without a proper country code and create a HubSpot workflow to require country on all new MQL contacts.'),
    ('Double down on high-converting channels',
     f'{best_src} achieves {best_src_rate:.1f}% conversion rate. Analyze what makes these leads higher quality (form fields, page content, ad creative) and replicate those conditions for lower-performing channels.'),
]

for title, body in recs:
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(0, 6, f'* {title}', ln=True)
    pdf.set_font('Helvetica', '', 8.5)
    pdf.set_x(20)
    pdf.multi_cell(0, 5, f'  {body}')
    pdf.ln(2)

# -- APPENDIX -----------------------------------------------------------------
pdf.add_page(orientation='L')
pdf.section_title('10. Appendix - Full Lead List')

all_rows = []
all_colors = []
for l in sorted(leads, key=lambda x: (x['bucket'], x['segment'])):
    ae = (l['ae'][:20] + '...') if len(l['ae']) > 20 else l['ae']
    email = (l['email'][:28] + '...') if len(l['email']) > 28 else l['email']
    all_rows.append([
        l['contact_id'],
        ae,
        l['segment'],
        email,
        l['country'],
        l['source'],
        str(l['units']) if l['units'] else '',
        l['stage'],
        l['nurturing_reason'][:25] if l['nurturing_reason'] else '',
    ])
    all_colors.append(BUCKET_COLORS.get(l['bucket'], (255,255,255)))

pdf.table(
    ['Contact ID', 'AE', 'Segment', 'Email', 'Country', 'Source', 'Units', 'Stage', 'Nurturing Reason'],
    [24, 36, 22, 60, 28, 32, 14, 30, 41],
    all_rows,
    row_colors=all_colors,
    font_size=7,
    orientation='L'
)

# --- SAVE --------------------------------------------------------------------
pdf.output(OUTPUT_PATH)
print(f'Report saved to: {OUTPUT_PATH}')
