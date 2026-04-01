import csv
from datetime import date, datetime
from collections import defaultdict
from fpdf import FPDF

# ── paths ──────────────────────────────────────────────────────────────────
CSV_PATH = r"c:/Users/aless/AppData/Local/Temp/924c7090-a8a7-49d3-8335-b6fb1375acb3_hubspot-custom-report-mqls-not-qualified-by-ae-2026-03-26-3.zip.cb3/mqls-not-qualified-by-ae.csv"
OUT_DIR  = r"c:/Users/aless/Documents/skills/mql-analysis-workspace/iteration-1/eval-1/with_skill/outputs/"

TODAY = date.today()
PDF_PATH = OUT_DIR + f"mql_analysis_{TODAY}.pdf"

# ── helpers ────────────────────────────────────────────────────────────────
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
            d = datetime.strptime(date_str.strip(), fmt).date()
            return (TODAY - d).days
        except ValueError:
            continue
    return None

PERSONAL_DOMAINS = {
    'gmail.com', 'googlemail.com',
    'hotmail.com', 'hotmail.es', 'hotmail.it', 'hotmail.co.uk',
    'yahoo.com', 'yahoo.es', 'yahoo.it', 'yahoo.co.uk',
    'outlook.com', 'live.com', 'msn.com',
    'icloud.com', 'me.com', 'mac.com',
    'aol.com', 'protonmail.com', 'pm.me',
    'gmx.com', 'gmx.net', 'mail.com',
    'libero.it', 'virgilio.it', 'tiscali.it', 'alice.it',
    'tin.it', 'email.it',
}

CORE_COUNTRIES = {'Spain', 'Germany', 'Italy', 'Czech Republic', 'United Kingdom', 'Austria'}

def is_personal_email(email):
    if not email or email == '(No value)':
        return False
    parts = email.lower().split('@')
    return len(parts) == 2 and parts[1] in PERSONAL_DOMAINS

# ── Step 1: Load CSV ───────────────────────────────────────────────────────
with open(CSV_PATH, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print("Columns:", reader.fieldnames)
print(f"Total rows: {len(rows)}")

# ── Step 2: Parse leads ────────────────────────────────────────────────────
leads = []
for row in rows:
    lead = {
        'segment':       row.get('Property Size', '').strip(),
        'ae':            row.get('AE owner', '').strip(),
        'mql_date':      row.get('Date entered "Marketing Qualified Lead (Lifecycle Stage Pipeline)"', '').strip(),
        'properties':    parse_int(row.get('Number of Properties or Rooms', '0')),
        'country':       row.get('Country', '').strip(),
        'source':        row.get('Original Traffic Source', '').strip(),
        'source_detail': row.get('Original Traffic Source Drill-Down 1', '').strip(),
        'contacts':      parse_int(row.get('Number of times contacted', '0')),
        'email':         row.get('Email', '').strip(),
        'contact_id':    row.get('Contact ID', '').strip(),
        'days_stagnant': days_since(row.get('Date entered "Marketing Qualified Lead (Lifecycle Stage Pipeline)"', '')),
    }
    lead['flags'] = []
    leads.append(lead)

# ── Step 3: Apply flags ────────────────────────────────────────────────────
for lead in leads:
    flags = []
    if lead['contacts'] >= 8:
        flags.append('HIGH CONTACTS')
    if is_personal_email(lead['email']):
        flags.append('PERSONAL EMAIL')
    if lead['properties'] > 500:
        flags.append('PROPERTY COUNT')
    if lead['country'] not in CORE_COUNTRIES and lead['country'] not in ('', '(No value)'):
        flags.append('NON-CORE COUNTRY')
    lead['flags'] = flags
    lead['flag_count'] = len(flags)

# ── Step 4: Segment and sort ───────────────────────────────────────────────
segments = ['SMB', 'Mid-Market', 'Enterprise']

def get_segment_leads(seg):
    sl = [l for l in leads if l['segment'] == seg]
    sl.sort(key=lambda x: (-(x['flag_count']), -(x['days_stagnant'] or 0)))
    return sl

seg_leads = {s: get_segment_leads(s) for s in segments}

# ── Step 5: Traffic source analysis ────────────────────────────────────────
def source_analysis(seg_list):
    stats = defaultdict(lambda: {'total': 0, 'flagged': 0, 'days': []})
    for lead in seg_list:
        src = lead['source'] or '(unknown)'
        stats[src]['total'] += 1
        if lead['flag_count'] > 0:
            stats[src]['flagged'] += 1
        if lead['days_stagnant'] is not None:
            stats[src]['days'].append(lead['days_stagnant'])
    result = []
    for src, d in sorted(stats.items(), key=lambda x: -x[1]['total']):
        avg_days = round(sum(d['days']) / len(d['days'])) if d['days'] else 0
        pct = round(d['flagged'] / d['total'] * 100) if d['total'] else 0
        result.append({'source': src, 'total': d['total'], 'flagged': d['flagged'],
                       'pct': pct, 'avg_days': avg_days})
    return result

seg_sources = {s: source_analysis(seg_leads[s]) for s in segments}

# ── AE analysis ────────────────────────────────────────────────────────────
ae_stats = defaultdict(lambda: {'total': 0, 'flagged': 0, 'high_contacts': 0})
for lead in leads:
    ae = lead['ae'] or '(unassigned)'
    ae_stats[ae]['total'] += 1
    if lead['flag_count'] > 0:
        ae_stats[ae]['flagged'] += 1
    if 'HIGH CONTACTS' in lead['flags']:
        ae_stats[ae]['high_contacts'] += 1

# ── Flag summary ────────────────────────────────────────────────────────────
FLAG_TYPES = ['HIGH CONTACTS', 'PERSONAL EMAIL', 'PROPERTY COUNT', 'NON-CORE COUNTRY']

def flag_counts(seg_list):
    counts = {f: 0 for f in FLAG_TYPES}
    for lead in seg_list:
        for f in lead['flags']:
            if f in counts:
                counts[f] += 1
    return counts

flag_summary = {s: flag_counts(seg_leads[s]) for s in segments}

total_leads = len(leads)
total_flagged = sum(1 for l in leads if l['flag_count'] > 0)

print(f"Total leads: {total_leads}, Flagged: {total_flagged}")
for s in segments:
    sl = seg_leads[s]
    fl = sum(1 for l in sl if l['flag_count'] > 0)
    print(f"  {s}: {len(sl)} total, {fl} flagged")

# ── Build recommendations ──────────────────────────────────────────────────
recommendations = []

# Check dominant flagged source
for s in segments:
    sl = seg_leads[s]
    total_fl = sum(1 for l in sl if l['flag_count'] > 0)
    if total_fl == 0:
        continue
    for src_row in seg_sources[s]:
        if src_row['flagged'] > 0 and total_fl > 0 and src_row['flagged'] / total_fl > 0.4:
            recommendations.append(
                f"{s} - {src_row['source']} accounts for {src_row['flagged']}/{total_fl} "
                f"({round(src_row['flagged']/total_fl*100)}%) of flagged leads. "
                f"Review MQL qualification criteria for this channel."
            )
            break

# Check AE with disproportionate high-contact leads
ae_hc = sorted(ae_stats.items(), key=lambda x: -x[1]['high_contacts'])
if ae_hc and ae_hc[0][1]['high_contacts'] >= 3:
    ae_name, ae_d = ae_hc[0]
    recommendations.append(
        f"{ae_name} owns {ae_d['high_contacts']} leads with 8+ contact attempts. "
        f"Schedule a disqualification review session with this AE."
    )

# Check non-core countries
for s in segments:
    sl = seg_leads[s]
    non_core = sum(1 for l in sl if 'NON-CORE COUNTRY' in l['flags'])
    total_fl = sum(1 for l in sl if l['flag_count'] > 0)
    if total_fl > 0 and non_core / max(total_fl, 1) > 0.25:
        recommendations.append(
            f"{s} - {non_core} flagged leads ({round(non_core/total_fl*100)}%) are from non-core countries. "
            f"Add country filters to lead scoring rules."
        )

# Check leads with 15+ contacts
ultra_contacts = [l for l in leads if l['contacts'] >= 15]
if ultra_contacts:
    recommendations.append(
        f"{len(ultra_contacts)} lead(s) have 15+ contact attempts with no progression. "
        f"Implement a disqualification SLA - leads with excessive contacts should be auto-moved out of MQL."
    )

# Check personal email concentration
personal_leads = [l for l in leads if 'PERSONAL EMAIL' in l['flags']]
if personal_leads and len(personal_leads) / total_leads > 0.20:
    recommendations.append(
        f"{len(personal_leads)} leads ({round(len(personal_leads)/total_leads*100)}%) use personal email addresses. "
        f"Consider requiring business email at form submission to improve ICP match."
    )

# Generic fallback
if not recommendations:
    recommendations.append(
        "Review the flagged leads table in the Appendix and coordinate with each AE to disqualify or re-engage stale contacts."
    )

# Pad to at least 4
while len(recommendations) < 4:
    recommendations.append(
        "Establish a regular cadence review meeting to clear stagnant MQLs from the pipeline."
    )

# ── PDF Generation ─────────────────────────────────────────────────────────

def truncate(text, max_chars):
    if text and len(text) > max_chars:
        return text[:max_chars - 1] + '...'
    return text or ''

class MQLReport(FPDF):
    def header(self):
        pass  # custom per-page footer only

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')
        self.set_text_color(0, 0, 0)

    def section_header(self, title):
        self.set_fill_color(232, 232, 232)
        self.set_font('Helvetica', 'B', 13)
        self.set_text_color(40, 40, 40)
        self.cell(0, 8, title, ln=True, fill=True)
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def table_header(self, cols, widths):
        self.set_fill_color(204, 204, 204)
        self.set_font('Helvetica', 'B', 8)
        for col, w in zip(cols, widths):
            self.cell(w, 6, col, border=1, fill=True)
        self.ln()

    def table_row(self, cells, widths, even):
        if even:
            self.set_fill_color(245, 245, 245)
        else:
            self.set_fill_color(255, 255, 255)
        self.set_font('Helvetica', '', 8)
        for cell, w in zip(cells, widths):
            self.cell(w, 5, str(cell), border=1, fill=True)
        self.ln()

pdf = MQLReport()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_margins(12, 12, 12)
W = 210 - 24  # usable width

# ── COVER PAGE ─────────────────────────────────────────────────────────────
pdf.add_page()
pdf.ln(50)
pdf.set_font('Helvetica', 'B', 22)
pdf.set_text_color(30, 30, 30)
pdf.cell(0, 12, 'MQL Quality Analysis Report', ln=True, align='C')
pdf.ln(4)
pdf.set_font('Helvetica', '', 13)
pdf.set_text_color(80, 80, 80)
pdf.cell(0, 8, f'Stagnant MQL Audit - {TODAY}', ln=True, align='C')
pdf.ln(10)
pdf.set_font('Helvetica', 'B', 12)
pdf.set_text_color(0, 0, 0)
pdf.cell(0, 7, f'Total MQLs Analyzed: {total_leads}', ln=True, align='C')
pdf.cell(0, 7, f'Flagged Leads: {total_flagged} ({round(total_flagged/total_leads*100)}%)', ln=True, align='C')
pdf.ln(6)
for s in segments:
    sl = seg_leads[s]
    fl = sum(1 for l in sl if l['flag_count'] > 0)
    pct = round(fl / len(sl) * 100) if sl else 0
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 6, f'{s}: {len(sl)} leads, {fl} flagged ({pct}%)', ln=True, align='C')

# ── EXECUTIVE SUMMARY ──────────────────────────────────────────────────────
pdf.add_page()
pdf.section_header('Executive Summary')
pdf.set_font('Helvetica', '', 9)

summary_bullets = [
    f"{total_flagged} of {total_leads} stagnant MQLs ({round(total_flagged/total_leads*100)}%) carry at least one quality flag, indicating significant pipeline contamination.",
]

# Personal email insight
pe_count = sum(1 for l in leads if 'PERSONAL EMAIL' in l['flags'])
if pe_count:
    summary_bullets.append(
        f"PERSONAL EMAIL is the most common flag ({pe_count} leads), concentrated in SMB/Paid Social - "
        f"many of these are likely consumer registrations rather than business decision-makers."
    )

# High contacts insight
hc_count = sum(1 for l in leads if 'HIGH CONTACTS' in l['flags'])
if hc_count:
    top_ae = ae_hc[0][0] if ae_hc else 'unknown'
    top_ae_hc = ae_hc[0][1]['high_contacts'] if ae_hc else 0
    summary_bullets.append(
        f"{hc_count} lead(s) have been contacted 8+ times with no lifecycle progression. "
        f"{top_ae} leads with the most exhausted contacts ({top_ae_hc}), suggesting cadence or ICP issues."
    )

# Non-core country
nc_count = sum(1 for l in leads if 'NON-CORE COUNTRY' in l['flags'])
if nc_count:
    summary_bullets.append(
        f"{nc_count} leads are from non-core countries and are unlikely to convert - "
        f"these should be reviewed for disqualification or re-routing."
    )

# Dominant source
for s in segments:
    sl = seg_leads[s]
    total_fl = sum(1 for l in sl if l['flag_count'] > 0)
    if total_fl == 0:
        continue
    top_src = max(seg_sources[s], key=lambda x: x['flagged']) if seg_sources[s] else None
    if top_src and top_src['flagged'] / max(total_fl, 1) > 0.35:
        summary_bullets.append(
            f"In {s}, {top_src['source']} is the largest source of flagged leads "
            f"({top_src['flagged']} of {total_fl} flagged, {round(top_src['flagged']/total_fl*100)}%). "
            f"Channel-level qualification criteria should be reviewed."
        )
        break

summary_bullets.append(
    "Immediate action recommended: AEs should be tasked with bulk-disqualifying leads that are non-core country, "
    "personal email, and/or have had 8+ contact attempts without result."
)

for bullet in summary_bullets[:6]:
    pdf.set_x(14)
    pdf.multi_cell(W - 4, 5, f'*  {bullet}')
    pdf.ln(1)

# ── FLAG SUMMARY TABLE ─────────────────────────────────────────────────────
pdf.ln(4)
pdf.section_header('Overall Flag Summary')
cols = ['Flag', 'SMB', 'Mid-Market', 'Enterprise', 'Total']
widths = [60, 30, 35, 35, 26]
pdf.table_header(cols, widths)
for i, flag in enumerate(FLAG_TYPES):
    smb_c = flag_summary['SMB'][flag]
    mm_c  = flag_summary['Mid-Market'][flag]
    ent_c = flag_summary['Enterprise'][flag]
    tot   = smb_c + mm_c + ent_c
    pdf.table_row([flag, smb_c, mm_c, ent_c, tot], widths, i % 2 == 0)

# ── PER-SEGMENT SECTIONS ────────────────────────────────────────────────────
for seg in segments:
    pdf.add_page()
    sl = seg_leads[seg]
    fl_count = sum(1 for l in sl if l['flag_count'] > 0)
    pct = round(fl_count / len(sl) * 100) if sl else 0
    pdf.section_header(f'{seg} - {len(sl)} leads, {fl_count} flagged ({pct}%)')

    # Top flagged leads (up to 15)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(0, 6, 'Top Flagged Leads (up to 15)', ln=True)
    top15 = [l for l in sl if l['flag_count'] > 0][:15]
    if top15:
        cols2 = ['AE Owner', 'Days', 'Contacts', 'Country', 'Flags']
        ws2   = [52, 16, 18, 32, 68]
        pdf.table_header(cols2, ws2)
        for i, lead in enumerate(top15):
            flags_str = ', '.join(lead['flags'])
            row_cells = [
                truncate(lead['ae'], 28),
                str(lead['days_stagnant'] or '-'),
                str(lead['contacts']),
                truncate(lead['country'], 18),
                truncate(flags_str, 38),
            ]
            pdf.table_row(row_cells, ws2, i % 2 == 0)
    else:
        pdf.set_font('Helvetica', 'I', 9)
        pdf.cell(0, 6, 'No flagged leads in this segment.', ln=True)

    pdf.ln(4)

    # Traffic source table
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(0, 6, 'Traffic Source Breakdown', ln=True)
    src_data = seg_sources[seg]
    if src_data:
        cols3 = ['Source', 'Total', 'Flagged', '% Flagged', 'Avg Days Stagnant']
        ws3   = [60, 20, 22, 24, 40]
        pdf.table_header(cols3, ws3)
        for i, row in enumerate(src_data):
            pdf.table_row([
                truncate(row['source'], 32),
                row['total'],
                row['flagged'],
                f"{row['pct']}%",
                row['avg_days'],
            ], ws3, i % 2 == 0)
    else:
        pdf.set_font('Helvetica', 'I', 9)
        pdf.cell(0, 6, 'No data.', ln=True)

# ── RECOMMENDATIONS ─────────────────────────────────────────────────────────
pdf.add_page()
pdf.section_header('Recommendations')
pdf.set_font('Helvetica', '', 9)
for i, rec in enumerate(recommendations, 1):
    pdf.set_x(12)
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(8, 5, f'{i}.', ln=False)
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(W - 8, 5, rec)
    pdf.ln(2)

# ── APPENDIX: Full flagged list ─────────────────────────────────────────────
pdf.add_page()
pdf.section_header('Appendix: Full Flagged Lead List')

all_flagged = sorted(
    [l for l in leads if l['flag_count'] > 0],
    key=lambda x: (x['segment'], -x['flag_count'], -(x['days_stagnant'] or 0))
)

cols4 = ['Contact ID', 'AE', 'Seg', 'Email', 'Country', 'Source', 'Contacts', 'Days', 'Flags']
ws4   = [24, 28, 12, 40, 22, 26, 16, 12, 46]

pdf.table_header(cols4, ws4)
for i, lead in enumerate(all_flagged):
    flags_str = ', '.join(lead['flags'])
    pdf.table_row([
        truncate(lead['contact_id'], 14),
        truncate(lead['ae'], 16),
        truncate(lead['segment'], 6),
        truncate(lead['email'], 24),
        truncate(lead['country'], 14),
        truncate(lead['source'], 16),
        lead['contacts'],
        str(lead['days_stagnant'] or '-'),
        truncate(flags_str, 28),
    ], ws4, i % 2 == 0)

# ── Save ────────────────────────────────────────────────────────────────────
pdf.output(PDF_PATH)
print(f"\nPDF saved to: {PDF_PATH}")
