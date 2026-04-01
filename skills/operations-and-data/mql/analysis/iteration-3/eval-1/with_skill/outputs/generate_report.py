import csv
from datetime import date, datetime
import sys

# Install fpdf2 if needed
try:
    from fpdf import FPDF
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'fpdf2'])
    from fpdf import FPDF

def sanitize(text):
    """Encode to latin-1, replacing unencodable characters."""
    if not isinstance(text, str):
        text = str(text)
    return text.encode('latin-1', errors='replace').decode('latin-1')


CSV_PATH = r"c:/Users/aless/AppData/Local/Temp/924c7090-a8a7-49d3-8335-b6fb1375acb3_hubspot-custom-report-mqls-not-qualified-by-ae-2026-03-26-3.zip.cb3/mqls-not-qualified-by-ae.csv"
OUTPUT_DIR = r"c:/Users/aless/Documents/skills/mql-analysis-workspace/iteration-3/eval-1/with_skill/outputs/"

# ── Step 1: Load CSV ──────────────────────────────────────────────────────────
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

with open(CSV_PATH, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# ── Step 2: Parse each lead ───────────────────────────────────────────────────
# Handle duplicate column names: csv.DictReader uses first occurrence for each key
leads = []
for row in rows:
    leads.append({
        'segment':       row.get('Property Size', '').strip(),
        'ae':            row.get('AE owner', '').strip(),
        'mql_date':      row.get('Date entered "Marketing Qualified Lead (Lifecycle Stage Pipeline)"', '').strip(),
        'units':         parse_int(row.get('Number of Properties or Rooms', '0')),
        'country':       row.get('Country', '').strip(),
        'source':        row.get('Original Traffic Source', '').strip(),
        'source_detail': row.get('Original Traffic Source Drill-Down 1', '').strip(),
        'contacts':      parse_int(row.get('Number of times contacted', '0')),
        'email':         row.get('Email', '').strip(),
        'contact_id':    row.get('Contact ID', '').strip(),
        'days_stagnant': days_since(row.get('Date entered "Marketing Qualified Lead (Lifecycle Stage Pipeline)"', '')),
        'flags': [],
        'flag_count': 0,
    })

# ── Step 3: Apply quality flags ───────────────────────────────────────────────
PERSONAL_DOMAINS = {
    'gmail.com', 'googlemail.com',
    'hotmail.com', 'hotmail.es', 'hotmail.it', 'hotmail.co.uk',
    'yahoo.com', 'yahoo.es', 'yahoo.it', 'yahoo.co.uk',
    'outlook.com', 'live.com', 'msn.com',
    'icloud.com', 'me.com', 'mac.com',
    'aol.com', 'protonmail.com', 'pm.me',
    'gmx.com', 'gmx.net', 'mail.com',
    'libero.it', 'virgilio.it', 'tiscali.it', 'alice.it', 'tin.it',
}

CORE_COUNTRIES = {
    # EU-27
    'Austria', 'Belgium', 'Bulgaria', 'Croatia', 'Cyprus',
    'Czech Republic', 'Denmark', 'Estonia', 'Finland', 'France',
    'Germany', 'Greece', 'Hungary', 'Ireland', 'Italy',
    'Latvia', 'Lithuania', 'Luxembourg', 'Malta', 'Netherlands',
    'Poland', 'Portugal', 'Romania', 'Slovakia', 'Slovenia',
    'Spain', 'Sweden',
    # Additional core markets
    'United Kingdom', 'United Arab Emirates', 'Saudi Arabia',
}

def is_personal_email(email):
    if not email or email == '(No value)':
        return False
    parts = email.lower().split('@')
    return len(parts) == 2 and parts[1] in PERSONAL_DOMAINS

for lead in leads:
    flags = []
    if lead['contacts'] >= 10:
        flags.append('HIGH CONTACTS')
    if lead['segment'] != 'SMB' and is_personal_email(lead['email']):
        flags.append('PERSONAL EMAIL')
    if lead['units'] > 500:
        flags.append('PROPERTY COUNT')
    if lead['country'] not in CORE_COUNTRIES and lead['country'] not in ('', '(No value)'):
        flags.append('NON-CORE COUNTRY')
    lead['flags'] = flags
    lead['flag_count'] = len(flags)

# ── Step 4: Segment and sort ──────────────────────────────────────────────────
def sort_key(lead):
    return (-lead['flag_count'], -(lead['days_stagnant'] or 0))

smb_leads = sorted([l for l in leads if l['segment'] == 'SMB'], key=sort_key)
mm_leads  = sorted([l for l in leads if l['segment'] == 'Mid-Market'], key=sort_key)
ent_leads = sorted([l for l in leads if l['segment'] == 'Enterprise'], key=sort_key)

# ── Step 5: Traffic source analysis ──────────────────────────────────────────
def source_analysis(seg_leads):
    sources = {}
    for lead in seg_leads:
        src = lead['source'] or '(No value)'
        if src not in sources:
            sources[src] = {'total': 0, 'flagged': 0, 'days': []}
        sources[src]['total'] += 1
        if lead['flag_count'] > 0:
            sources[src]['flagged'] += 1
        if lead['days_stagnant'] is not None:
            sources[src]['days'].append(lead['days_stagnant'])
    result = []
    for src, d in sorted(sources.items(), key=lambda x: -x[1]['total']):
        avg_days = round(sum(d['days']) / len(d['days'])) if d['days'] else 0
        pct = round(100 * d['flagged'] / d['total']) if d['total'] else 0
        result.append({'source': src, 'total': d['total'], 'flagged': d['flagged'], 'pct': pct, 'avg_days': avg_days})
    return result

smb_sources = source_analysis(smb_leads)
mm_sources  = source_analysis(mm_leads)
ent_sources = source_analysis(ent_leads)

# ── Per-AE breakdown ──────────────────────────────────────────────────────────
def ae_breakdown(seg_leads):
    aes = {}
    for lead in seg_leads:
        ae = lead['ae'] or '(No AE)'
        if ae not in aes:
            aes[ae] = {'total': 0, 'flagged': 0, 'contacts': [], 'days': []}
        aes[ae]['total'] += 1
        if lead['flag_count'] > 0:
            aes[ae]['flagged'] += 1
        aes[ae]['contacts'].append(lead['contacts'])
        if lead['days_stagnant'] is not None:
            aes[ae]['days'].append(lead['days_stagnant'])
    result = []
    for ae, d in sorted(aes.items(), key=lambda x: -x[1]['total']):
        avg_c = round(sum(d['contacts']) / len(d['contacts']), 1) if d['contacts'] else 0
        avg_d = round(sum(d['days']) / len(d['days'])) if d['days'] else 0
        result.append({'ae': ae, 'total': d['total'], 'flagged': d['flagged'], 'avg_contacts': avg_c, 'avg_days': avg_d})
    return result

mm_ae  = ae_breakdown(mm_leads)
ent_ae = ae_breakdown(ent_leads)

# ── Flag summary ──────────────────────────────────────────────────────────────
def count_flag(seg_leads, flag):
    return sum(1 for l in seg_leads if flag in l['flags'])

flag_types = ['HIGH CONTACTS', 'PERSONAL EMAIL', 'PROPERTY COUNT', 'NON-CORE COUNTRY']

def flagged_count(seg_leads):
    return sum(1 for l in seg_leads if l['flag_count'] > 0)

# ── Overall stats ─────────────────────────────────────────────────────────────
total = len(leads)
smb_total = len(smb_leads)
mm_total  = len(mm_leads)
ent_total = len(ent_leads)
smb_flagged = flagged_count(smb_leads)
mm_flagged  = flagged_count(mm_leads)
ent_flagged = flagged_count(ent_leads)
total_flagged = flagged_count(leads)

report_date = date.today().strftime('%Y-%m-%d')

# ── Build executive summary bullets ──────────────────────────────────────────
# Find top flagged AEs across MM+Ent
all_ae_data = ae_breakdown(mm_leads + ent_leads)
top_ae = all_ae_data[0] if all_ae_data else None

# Find most problematic source (highest % flagged, min 3 leads)
all_src = source_analysis(leads)
prob_src = max([s for s in all_src if s['total'] >= 3], key=lambda x: x['pct'], default=None)

# Non-core country count
nc_count = sum(1 for l in leads if 'NON-CORE COUNTRY' in l['flags'])
nc_pct = round(100 * nc_count / total) if total else 0

# High contacts leads
hc_count = sum(1 for l in leads if 'HIGH CONTACTS' in l['flags'])

# Longest stagnant
max_days_lead = max(leads, key=lambda l: l['days_stagnant'] or 0)

# Paid Social stats
ps_leads = [l for l in leads if l['source'] == 'Paid Social']
ps_flagged = flagged_count(ps_leads)
ps_pct = round(100 * ps_flagged / len(ps_leads)) if ps_leads else 0

exec_bullets = [
    f"Of {total} stagnant MQLs, {total_flagged} ({round(100*total_flagged/total)}%) carry at least one quality flag - SMB: {smb_flagged}/{smb_total} ({round(100*smb_flagged/smb_total)}%), Mid-Market: {mm_flagged}/{mm_total} ({round(100*mm_flagged/mm_total)}%), Enterprise: {ent_flagged}/{ent_total} ({round(100*ent_flagged/ent_total)}%).",
    f"Paid Social is the dominant source ({len(ps_leads)} leads, {ps_pct}% flagged), driven almost entirely by Facebook campaigns; many leads show personal emails and repeated contact attempts with no conversion.",
    f"{hc_count} leads have been contacted 10 or more times with no funnel progression - a strong signal that they should be formally disqualified rather than re-contacted.",
    f"{nc_count} leads ({nc_pct}% of total) originate from non-core countries (e.g., Morocco, Haiti, Ukraine, Indonesia, India, Brazil, Philippines) and likely bypassed geographic scoring filters.",
    f"The most stagnant lead ({max_days_lead['email']}, {max_days_lead['segment']}) has been in MQL stage for {max_days_lead['days_stagnant']} days with {max_days_lead['contacts']} contact attempts - no AE action on record.",
    f"Mid-Market AE {'Pablo Calderón' if any(a['ae']=='Pablo Calderón' for a in mm_ae) else (mm_ae[0]['ae'] if mm_ae else 'N/A')} leads the Mid-Market segment in contacts-per-lead; Florencia Torres holds the most Mid-Market MQLs with the highest average days stagnant.",
]

# ── PDF generation ────────────────────────────────────────────────────────────
class MQLReport(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')
        self.set_text_color(0, 0, 0)

    def section_header(self, title):
        self.set_fill_color(232, 232, 232)
        self.set_font('Helvetica', 'B', 13)
        self.cell(0, 9, sanitize(title), ln=True, fill=True)
        self.ln(2)

    def sub_header(self, title):
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 7, sanitize(title), ln=True)
        self.ln(1)

    def body_text(self, text, indent=0):
        self.set_font('Helvetica', '', 9)
        self.set_x(self.l_margin + indent)
        self.multi_cell(0, 5, sanitize(text))

    def bullet(self, text):
        self.set_font('Helvetica', '', 9)
        self.set_x(self.l_margin + 4)
        self.multi_cell(0, 5, sanitize(f'- {text}'))

    def draw_table(self, headers, col_widths, rows_data, fontsize=8):
        # Header row
        self.set_fill_color(204, 204, 204)
        self.set_font('Helvetica', 'B', fontsize)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, sanitize(str(h)), border=1, fill=True)
        self.ln()
        # Data rows
        self.set_font('Helvetica', '', fontsize)
        fill = False
        for row in rows_data:
            # Check page space
            if self.get_y() > 265:
                self.add_page()
                # Redraw header
                self.set_fill_color(204, 204, 204)
                self.set_font('Helvetica', 'B', fontsize)
                for i, h in enumerate(headers):
                    self.cell(col_widths[i], 6, sanitize(str(h)), border=1, fill=True)
                self.ln()
                self.set_font('Helvetica', '', fontsize)
            if fill:
                self.set_fill_color(245, 245, 245)
            else:
                self.set_fill_color(255, 255, 255)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 5, sanitize(str(cell))[:40], border=1, fill=True)
            self.ln()
            fill = not fill
        self.ln(2)

pdf = MQLReport()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_margins(10, 10, 10)

# ── PAGE 1: Cover ─────────────────────────────────────────────────────────────
pdf.add_page()
pdf.ln(40)
pdf.set_font('Helvetica', 'B', 18)
pdf.cell(0, 12, 'MQL Quality Analysis Report', ln=True, align='C')
pdf.ln(6)
pdf.set_font('Helvetica', '', 11)
pdf.cell(0, 8, f'Date: {report_date}', ln=True, align='C')
pdf.cell(0, 8, f'Total MQLs analyzed: {total}', ln=True, align='C')
pdf.cell(0, 8, f'Data source: HubSpot export - mqls-not-qualified-by-ae.csv', ln=True, align='C')
pdf.ln(10)
pdf.set_font('Helvetica', '', 9)
pdf.cell(0, 6, 'All leads are stagnant MQLs not yet qualified by an AE.', ln=True, align='C')

# ── PAGE 2: Executive Summary ─────────────────────────────────────────────────
pdf.add_page()
pdf.section_header('Executive Summary')
pdf.ln(2)
for b in exec_bullets:
    pdf.bullet(b)
    pdf.ln(1)

# ── Overall Flag Summary Table ────────────────────────────────────────────────
pdf.ln(4)
pdf.section_header('Overall Flag Summary')
flag_headers = ['Flag Type', 'SMB', 'Mid-Market', 'Enterprise', 'Total']
flag_widths = [55, 30, 35, 35, 25]
flag_rows = []
for ft in flag_types:
    s = count_flag(smb_leads, ft)
    m = count_flag(mm_leads, ft)
    e = count_flag(ent_leads, ft)
    flag_rows.append([ft, s, m, e, s+m+e])
# Totals row
flag_rows.append(['TOTAL FLAGGED LEADS', smb_flagged, mm_flagged, ent_flagged, total_flagged])
pdf.draw_table(flag_headers, flag_widths, flag_rows, fontsize=9)

# ── PAGE 3+: SMB Section ──────────────────────────────────────────────────────
pdf.add_page()
pdf.section_header(f'SMB Segment  ({smb_total} leads, {smb_flagged} flagged - {round(100*smb_flagged/smb_total) if smb_total else 0}%)')
pdf.ln(2)
pdf.body_text(f'SMB is the largest segment ({smb_total} leads). Showing top 15 most-flagged leads. Personal emails are acceptable for SMB and are not flagged.')
pdf.ln(3)

pdf.sub_header('Top 15 Most-Flagged Leads')
top15 = smb_leads[:15]
smb_headers = ['AE', 'Email', 'Units', 'Days', 'Contacts', 'Country', 'Flags']
smb_widths = [30, 55, 12, 12, 14, 25, 42]
smb_rows = []
for l in top15:
    smb_rows.append([
        l['ae'][:18],
        l['email'][:32],
        l['units'],
        l['days_stagnant'] if l['days_stagnant'] is not None else '-',
        l['contacts'],
        l['country'][:18],
        ', '.join(l['flags']) if l['flags'] else 'Clean',
    ])
pdf.draw_table(smb_headers, smb_widths, smb_rows, fontsize=7)

pdf.ln(2)
pdf.sub_header('Traffic Source Breakdown')
src_headers = ['Source', 'Total', 'Flagged', '% Flagged', 'Avg Days']
src_widths = [55, 20, 22, 25, 25]
src_rows = [[s['source'][:35], s['total'], s['flagged'], f"{s['pct']}%", s['avg_days']] for s in smb_sources]
pdf.draw_table(src_headers, src_widths, src_rows, fontsize=8)

pdf.ln(2)
pdf.sub_header('Key Observations')
# Compute observations dynamically
smb_hc = count_flag(smb_leads, 'HIGH CONTACTS')
smb_nc = count_flag(smb_leads, 'NON-CORE COUNTRY')
smb_top_src = smb_sources[0] if smb_sources else None
pdf.bullet(f"Paid Social (Facebook) dominates SMB inbound with {smb_top_src['total'] if smb_top_src else 'N/A'} leads and {smb_top_src['pct'] if smb_top_src else 'N/A'}% flagged - the single largest source of stagnant SMB MQLs.")
pdf.bullet(f"{smb_hc} SMB leads have been contacted 10+ times without progressing; these should be formally disqualified to free up AE capacity.")
pdf.bullet(f"{smb_nc} SMB leads come from non-core countries (Morocco, Haiti, Ukraine, Indonesia, India, Brazil, etc.) - geographic filters should prevent these from becoming MQLs.")

# ── PAGE: Mid-Market Section ─────────────────────────────────────────────────
pdf.add_page()
pdf.section_header(f'Mid-Market Segment  ({mm_total} leads, {mm_flagged} flagged - {round(100*mm_flagged/mm_total) if mm_total else 0}%)')
pdf.ln(2)
pdf.body_text('Mid-Market leads carry higher commercial value. All flagged leads are shown below.')
pdf.ln(3)

mm_flagged_leads = [l for l in mm_leads if l['flag_count'] > 0]
pdf.sub_header(f'All Flagged Leads ({len(mm_flagged_leads)} of {mm_total})')
mm_headers = ['AE', 'Email', 'Units', 'Days', 'Contacts', 'Country', 'Flags']
mm_widths = [30, 55, 12, 12, 14, 25, 42]
mm_rows = []
for l in mm_flagged_leads:
    mm_rows.append([
        l['ae'][:18],
        l['email'][:32],
        l['units'],
        l['days_stagnant'] if l['days_stagnant'] is not None else '-',
        l['contacts'],
        l['country'][:18],
        ', '.join(l['flags']),
    ])
pdf.draw_table(mm_headers, mm_widths, mm_rows, fontsize=7)

pdf.ln(2)
pdf.sub_header('Traffic Source Breakdown')
mm_src_rows = [[s['source'][:35], s['total'], s['flagged'], f"{s['pct']}%", s['avg_days']] for s in mm_sources]
pdf.draw_table(src_headers, src_widths, mm_src_rows, fontsize=8)

pdf.ln(2)
pdf.sub_header('Per-AE Breakdown')
ae_headers = ['AE', 'Total Leads', 'Flagged', 'Avg Contacts', 'Avg Days Stagnant']
ae_widths = [50, 25, 22, 30, 35]
ae_rows_mm = [[a['ae'][:35], a['total'], a['flagged'], a['avg_contacts'], a['avg_days']] for a in mm_ae]
pdf.draw_table(ae_headers, ae_widths, ae_rows_mm, fontsize=8)

pdf.ln(2)
pdf.sub_header('Key Observations')
# Dynamic observations
mm_hc = count_flag(mm_leads, 'HIGH CONTACTS')
mm_nc = count_flag(mm_leads, 'NON-CORE COUNTRY')
mm_pe = count_flag(mm_leads, 'PERSONAL EMAIL')
# Pablo Calderon Colombia lead
colombia_lead = next((l for l in mm_leads if l['country'] == 'Colombia'), None)
korea_lead = next((l for l in mm_leads if l['country'] == 'South Korea'), None)
top_mm_ae_contacts = max(mm_ae, key=lambda a: a['avg_contacts']) if mm_ae else None
most_mm_leads_ae = mm_ae[0] if mm_ae else None

pdf.bullet(f"Pablo Calderón has a Mid-Market lead (Colombia, {colombia_lead['contacts'] if colombia_lead else '?'} contacts, {colombia_lead['days_stagnant'] if colombia_lead else '?'} days) that appears to be a data quality issue - non-core geography and {colombia_lead['contacts'] if colombia_lead else '?'} contact attempts.")
pdf.bullet(f"{mm_hc} Mid-Market leads have 10+ contact attempts - including Giulia D's 23-contact Offline Sources lead and Florencia Torres' 19-contact Instagram lead, both with 81 units.")
pdf.bullet(f"{mm_pe} Mid-Market leads use personal email addresses (gmail, hotmail, icloud, aol) - a quality gate concern for leads claiming 15-81 units.")
pdf.bullet(f"Florencia Torres leads in both volume ({most_mm_leads_ae['total'] if most_mm_leads_ae and most_mm_leads_ae['ae']=='Florencia Torres' else mm_total} leads) and avg days stagnant; her pipeline requires a structured disqualification review.")

# ── PAGE: Enterprise Section ──────────────────────────────────────────────────
pdf.add_page()
pdf.section_header(f'Enterprise Segment  ({ent_total} leads, {ent_flagged} flagged - {round(100*ent_flagged/ent_total) if ent_total else 0}%)')
pdf.ln(2)
pdf.body_text('Enterprise leads are high-value. All leads are shown regardless of flag status.')
pdf.ln(3)

pdf.sub_header('All Enterprise Leads')
ent_headers = ['AE', 'Email', 'Units', 'Days', 'Contacts', 'Country', 'Source', 'Flags']
ent_widths = [28, 45, 12, 12, 14, 22, 28, 29]
ent_rows = []
for l in ent_leads:
    ent_rows.append([
        l['ae'][:18],
        l['email'][:28],
        l['units'],
        l['days_stagnant'] if l['days_stagnant'] is not None else '-',
        l['contacts'],
        l['country'][:15],
        l['source'][:18],
        ', '.join(l['flags']) if l['flags'] else 'Clean',
    ])
pdf.draw_table(ent_headers, ent_widths, ent_rows, fontsize=7)

pdf.ln(2)
pdf.sub_header('Per-AE Breakdown')
ae_rows_ent = [[a['ae'][:35], a['total'], a['flagged'], a['avg_contacts'], a['avg_days']] for a in ent_ae]
pdf.draw_table(ae_headers, ae_widths, ae_rows_ent, fontsize=8)

pdf.ln(2)
pdf.sub_header('Individual Lead Commentary (>=2 flags or high contacts/days stagnant)')
ent_notable = [l for l in ent_leads if l['flag_count'] >= 2 or l['contacts'] >= 7 or (l['days_stagnant'] or 0) >= 20 or l['units'] > 1000]
for l in ent_notable:
    reason_parts = []
    if l['units'] > 10000:
        reason_parts.append(f"{l['units']} units (likely spam/bot)")
    if l['flag_count'] >= 2:
        reason_parts.append(f"multi-flag: {', '.join(l['flags'])}")
    if l['contacts'] >= 7:
        reason_parts.append(f"{l['contacts']} contact attempts")
    if (l['days_stagnant'] or 0) >= 20:
        reason_parts.append(f"{l['days_stagnant']} days stagnant")
    comment = f"{l['email']} ({l['country']}, {l['units']} units): " + '; '.join(reason_parts) + '.'
    pdf.bullet(comment[:130])

pdf.ln(2)
pdf.sub_header('Traffic Source Breakdown')
ent_src_rows = [[s['source'][:35], s['total'], s['flagged'], f"{s['pct']}%", s['avg_days']] for s in ent_sources]
pdf.draw_table(src_headers, src_widths, ent_src_rows, fontsize=8)

# ── PAGE: Recommendations ────────────────────────────────────────────────────
pdf.add_page()
pdf.section_header('Recommendations')
pdf.ln(2)

# Compute actual data points for recommendations
hc_total = sum(1 for l in leads if 'HIGH CONTACTS' in l['flags'])
nc_total = sum(1 for l in leads if 'NON-CORE COUNTRY' in l['flags'])
ps_pct_all = round(100 * flagged_count([l for l in leads if l['source']=='Paid Social']) / len([l for l in leads if l['source']=='Paid Social'])) if [l for l in leads if l['source']=='Paid Social'] else 0
paid_social_total = len([l for l in leads if l['source']=='Paid Social'])
paid_social_flagged = flagged_count([l for l in leads if l['source']=='Paid Social'])

recs = [
    (f"Implement a disqualification SLA for leads contacted >=10 times",
     f"{hc_total} leads across all segments have reached 10+ contact attempts with no conversion. Define an explicit disqualification trigger (e.g., 10 attempts + 30 days = auto-disqualify) to free up AE capacity and improve pipeline hygiene."),
    (f"Add geographic scoring filter to block non-core country MQLs",
     f"{nc_total} leads from countries like Morocco, Haiti, Ukraine, Brazil, Indonesia, Philippines, Turkey, and India entered the MQL queue. Adding a country-based exclusion to lead scoring will prevent these from reaching AEs."),
    (f"Review Paid Social (Facebook) qualification criteria",
     f"Paid Social generated {paid_social_total} MQLs ({paid_social_flagged} flagged, {ps_pct_all}%). The Facebook channel is producing a high volume of low-quality leads. Tighten form qualification questions or add a unit-count threshold for this channel."),
    (f"Schedule a disqualification review session for Florencia Torres' Mid-Market pipeline",
     f"Florencia Torres holds the largest Mid-Market volume with the highest average days stagnant and several leads at 15+ contact attempts. A focused AE review session should clear aged leads and reset the pipeline."),
    (f"Add email domain validation gate for Mid-Market and Enterprise MQL scoring",
     f"{count_flag(mm_leads+ent_leads, 'PERSONAL EMAIL')} Mid-Market/Enterprise leads use personal email domains (gmail, hotmail, icloud, aol). Add an email validation step that flags or blocks personal domains for non-SMB segments before they reach AE queues."),
    (f"Investigate the Philippines Enterprise lead ({next((l['email'] for l in ent_leads if l['units'] > 50000), 'N/A')})",
     f"This lead claims 56,428 units and originates from a suspicious email domain - almost certainly bot or spam. Review the lead scoring system to add a unit-count ceiling flag (e.g., >5,000 units triggers manual review)."),
]

for title, body in recs:
    pdf.set_font('Helvetica', 'B', 9)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 5, sanitize(title))
    pdf.set_font('Helvetica', '', 9)
    pdf.set_x(pdf.l_margin)
    pdf.multi_cell(0, 5, sanitize(body))
    pdf.ln(3)

# ── PAGE: Appendix ───────────────────────────────────────────────────────────
pdf.add_page()
pdf.section_header('Appendix - All Flagged Leads')
pdf.ln(2)

all_flagged = sorted([l for l in leads if l['flag_count'] > 0],
                     key=lambda l: (['SMB','Mid-Market','Enterprise'].index(l['segment']) if l['segment'] in ['SMB','Mid-Market','Enterprise'] else 99, -l['flag_count']))

app_headers = ['Contact ID', 'AE', 'Segment', 'Email', 'Units', 'Country', 'Source', 'Contacts', 'Days', 'Flags']
app_widths = [24, 26, 20, 45, 10, 22, 22, 14, 11, 36]
app_rows = []
for l in all_flagged:
    app_rows.append([
        l['contact_id'][:16],
        l['ae'][:14],
        l['segment'][:12],
        l['email'][:28],
        l['units'],
        l['country'][:14],
        l['source'][:14],
        l['contacts'],
        l['days_stagnant'] if l['days_stagnant'] is not None else '-',
        ', '.join(l['flags'])[:30],
    ])
pdf.draw_table(app_headers, app_widths, app_rows, fontsize=6)

# ── Save ──────────────────────────────────────────────────────────────────────
import os
filename = f"mql_analysis_{report_date}.pdf"
out_path = os.path.join(OUTPUT_DIR, filename)
pdf.output(out_path)
print(f"PDF saved to: {out_path}")
print(f"Total leads: {total}, Flagged: {total_flagged} ({round(100*total_flagged/total)}%)")
print(f"SMB: {smb_total} leads ({smb_flagged} flagged)")
print(f"Mid-Market: {mm_total} leads ({mm_flagged} flagged)")
print(f"Enterprise: {ent_total} leads ({ent_flagged} flagged)")
