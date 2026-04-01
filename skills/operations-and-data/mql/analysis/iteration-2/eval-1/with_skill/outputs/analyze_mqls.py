import csv
from datetime import date, datetime
from collections import defaultdict

# ── helpers ──────────────────────────────────────────────────────────────────

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
    'Spain', 'Germany', 'Italy', 'Czech Republic',
    'United Kingdom', 'Austria', 'United Arab Emirates', 'Saudi Arabia'
}

def safe(txt):
    """Encode string to latin-1 safe representation for fpdf Helvetica."""
    if not txt:
        return ''
    return txt.encode('latin-1', errors='replace').decode('latin-1')

def is_personal_email(email):
    if not email or email == '(No value)':
        return False
    parts = email.lower().split('@')
    return len(parts) == 2 and parts[1] in PERSONAL_DOMAINS

# ── load CSV ──────────────────────────────────────────────────────────────────

csv_path = r"c:/Users/aless/AppData/Local/Temp/924c7090-a8a7-49d3-8335-b6fb1375acb3_hubspot-custom-report-mqls-not-qualified-by-ae-2026-03-26-3.zip.cb3/mqls-not-qualified-by-ae.csv"

with open(csv_path, encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

print(f"Total rows: {len(rows)}")
print(f"Columns: {list(rows[0].keys()) if rows else 'N/A'}")

# ── parse leads ───────────────────────────────────────────────────────────────

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
    })

# ── apply flags ───────────────────────────────────────────────────────────────

for lead in leads:
    flags = []
    if lead['contacts'] >= 10:
        flags.append('HIGH CONTACTS')
    # Personal email: only flag for Mid-Market and Enterprise (SMB accepted)
    if lead['segment'] != 'SMB' and is_personal_email(lead['email']):
        flags.append('PERSONAL EMAIL')
    if lead['units'] > 500:
        flags.append('PROPERTY COUNT')
    if lead['country'] not in CORE_COUNTRIES and lead['country'] not in ('', '(No value)'):
        flags.append('NON-CORE COUNTRY')
    lead['flags'] = flags
    lead['flag_count'] = len(flags)

# ── split and sort ────────────────────────────────────────────────────────────

def sort_key(l):
    return (-l['flag_count'], -(l['days_stagnant'] or 0))

smb        = sorted([l for l in leads if l['segment'] == 'SMB'],        key=sort_key)
midmarket  = sorted([l for l in leads if l['segment'] == 'Mid-Market'], key=sort_key)
enterprise = sorted([l for l in leads if l['segment'] == 'Enterprise'], key=sort_key)

print(f"\nSMB: {len(smb)}, Mid-Market: {len(midmarket)}, Enterprise: {len(enterprise)}")
print(f"Total flagged - SMB: {sum(1 for l in smb if l['flag_count']>0)}, "
      f"MM: {sum(1 for l in midmarket if l['flag_count']>0)}, "
      f"Ent: {sum(1 for l in enterprise if l['flag_count']>0)}")

# ── traffic source analysis ───────────────────────────────────────────────────

def source_breakdown(seg_leads):
    by_source = defaultdict(list)
    for l in seg_leads:
        key = l['source'] or '(No value)'
        by_source[key].append(l)
    result = []
    for src, lst in sorted(by_source.items(), key=lambda x: -len(x[1])):
        total   = len(lst)
        flagged = sum(1 for l in lst if l['flag_count'] > 0)
        avg_days = sum(l['days_stagnant'] or 0 for l in lst) / total if total else 0
        result.append({
            'source':   src,
            'total':    total,
            'flagged':  flagged,
            'pct':      100 * flagged / total if total else 0,
            'avg_days': avg_days,
        })
    return result

smb_sources  = source_breakdown(smb)
mm_sources   = source_breakdown(midmarket)
ent_sources  = source_breakdown(enterprise)

# ── per-AE breakdown ──────────────────────────────────────────────────────────

def ae_breakdown(seg_leads):
    by_ae = defaultdict(list)
    for l in seg_leads:
        key = l['ae'] or '(No AE)'
        by_ae[key].append(l)
    result = []
    for ae, lst in sorted(by_ae.items(), key=lambda x: -len(x[1])):
        total   = len(lst)
        flagged = sum(1 for l in lst if l['flag_count'] > 0)
        avg_contacts = sum(l['contacts'] for l in lst) / total if total else 0
        avg_days     = sum(l['days_stagnant'] or 0 for l in lst) / total if total else 0
        result.append({
            'ae':          ae,
            'total':       total,
            'flagged':     flagged,
            'pct':         100 * flagged / total if total else 0,
            'avg_contacts': avg_contacts,
            'avg_days':    avg_days,
        })
    return result

mm_ae  = ae_breakdown(midmarket)
ent_ae = ae_breakdown(enterprise)

# ── flag summary ──────────────────────────────────────────────────────────────

all_flag_types = ['HIGH CONTACTS', 'PERSONAL EMAIL', 'PROPERTY COUNT', 'NON-CORE COUNTRY']

def flag_counts(seg_leads):
    counts = defaultdict(int)
    for l in seg_leads:
        for f in l['flags']:
            counts[f] += 1
    return counts

smb_flags = flag_counts(smb)
mm_flags  = flag_counts(midmarket)
ent_flags = flag_counts(enterprise)

# ── print summary for verification ───────────────────────────────────────────

print("\n=== FLAG SUMMARY ===")
for ft in all_flag_types:
    total = smb_flags[ft] + mm_flags[ft] + ent_flags[ft]
    print(f"  {ft}: SMB={smb_flags[ft]}, MM={mm_flags[ft]}, Ent={ent_flags[ft]}, Total={total}")

print("\n=== MM AE BREAKDOWN ===")
for a in mm_ae:
    print(f"  {a['ae']}: total={a['total']}, flagged={a['flagged']}, avg_contacts={a['avg_contacts']:.1f}, avg_days={a['avg_days']:.0f}")

print("\n=== ENT AE BREAKDOWN ===")
for a in ent_ae:
    print(f"  {a['ae']}: total={a['total']}, flagged={a['flagged']}, avg_contacts={a['avg_contacts']:.1f}, avg_days={a['avg_days']:.0f}")

# =============================================================================
# PDF GENERATION
# =============================================================================

from fpdf import FPDF

OUTPUT_DIR = r"c:/Users/aless/Documents/skills/mql-analysis-workspace/iteration-2/eval-1/with_skill/outputs"
today_str = date.today().strftime('%Y-%m-%d')
pdf_path  = f"{OUTPUT_DIR}/mql_analysis_{today_str}.pdf"

class PDF(FPDF):
    def header(self):
        pass

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, f'Page {self.page_no()}', align='C')
        self.set_text_color(0, 0, 0)

    def section_title(self, txt):
        self.ln(4)
        self.set_fill_color(232, 232, 232)
        self.set_font('Helvetica', 'B', 13)
        self.cell(0, 8, safe(txt), ln=True, fill=True)
        self.ln(2)

    def sub_title(self, txt):
        self.ln(2)
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 6, safe(txt), ln=True)
        self.ln(1)

    def body_text(self, txt):
        self.set_font('Helvetica', '', 9)
        self.multi_cell(0, 5, safe(txt))
        self.ln(1)

    def bullet(self, txt):
        self.set_font('Helvetica', '', 9)
        self.cell(5)
        self.multi_cell(0, 5, safe(f'- {txt}'))

    def table(self, headers, rows, col_widths=None, stripe=True):
        """Draw a table. headers = list of str, rows = list of list."""
        if col_widths is None:
            avail = self.w - self.l_margin - self.r_margin
            col_widths = [avail / len(headers)] * len(headers)

        # header row
        self.set_font('Helvetica', 'B', 7.5)
        self.set_fill_color(204, 204, 204)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, safe(str(h)), border=0, ln=0, fill=True, align='C')
        self.ln()

        # data rows
        self.set_font('Helvetica', '', 7.5)
        for ri, row in enumerate(rows):
            # check page break — leave room for at least one row
            if self.get_y() > self.h - self.b_margin - 8:
                self.add_page()
                # re-draw header
                self.set_font('Helvetica', 'B', 7.5)
                self.set_fill_color(204, 204, 204)
                for i, h in enumerate(headers):
                    self.cell(col_widths[i], 6, safe(str(h)), border=0, ln=0, fill=True, align='C')
                self.ln()
                self.set_font('Helvetica', '', 7.5)

            fill = (ri % 2 == 1) if stripe else False
            self.set_fill_color(245, 245, 245)
            for i, val in enumerate(row):
                txt = safe(str(val)) if val is not None else ''
                self.cell(col_widths[i], 5.5, txt, border=0, ln=0, fill=fill, align='L')
            self.ln()
        self.ln(2)


pdf = PDF(orientation='L', format='A4')
pdf.set_margins(12, 12, 12)
pdf.set_auto_page_break(auto=True, margin=15)

# ── COVER PAGE ────────────────────────────────────────────────────────────────

pdf.add_page()
pdf.ln(50)
pdf.set_font('Helvetica', 'B', 24)
pdf.set_text_color(30, 30, 30)
pdf.cell(0, 12, safe('MQL Quality Analysis Report'), ln=True, align='C')
pdf.ln(6)
pdf.set_font('Helvetica', '', 12)
pdf.cell(0, 8, safe(f'Report Date: {today_str}'), ln=True, align='C')
pdf.cell(0, 8, safe(f'Total MQLs Analyzed: {len(leads)}'), ln=True, align='C')
pdf.ln(4)
pdf.set_font('Helvetica', '', 10)
pdf.set_text_color(100, 100, 100)
pdf.cell(0, 6, safe(f'SMB: {len(smb)}  |  Mid-Market: {len(midmarket)}  |  Enterprise: {len(enterprise)}'), ln=True, align='C')
total_flagged = sum(1 for l in leads if l['flag_count'] > 0)
pdf.cell(0, 6, safe(f'Total Flagged: {total_flagged} ({100*total_flagged/len(leads):.0f}%)'), ln=True, align='C')
pdf.set_text_color(0, 0, 0)

# ── EXECUTIVE SUMMARY ─────────────────────────────────────────────────────────

pdf.add_page()
pdf.section_title('Executive Summary')
pdf.set_font('Helvetica', '', 9)

smb_flagged   = sum(1 for l in smb if l['flag_count']>0)
mm_flagged    = sum(1 for l in midmarket if l['flag_count']>0)
ent_flagged   = sum(1 for l in enterprise if l['flag_count']>0)

# top source overall
all_sources = defaultdict(lambda: {'total':0,'flagged':0})
for l in leads:
    s = l['source'] or '(No value)'
    all_sources[s]['total'] += 1
    if l['flag_count'] > 0:
        all_sources[s]['flagged'] += 1
top_src = max(all_sources.items(), key=lambda x: x[1]['flagged'])

# most contacted lead
most_contacted = max(leads, key=lambda l: l['contacts'])

# top non-core country
nc_country = defaultdict(int)
for l in leads:
    if 'NON-CORE COUNTRY' in l['flags']:
        nc_country[l['country']] += 1
top_nc = max(nc_country.items(), key=lambda x: x[1]) if nc_country else ('N/A', 0)

# AE with most flagged across MM+ENT
ae_flagged = defaultdict(int)
for l in midmarket + enterprise:
    if l['flag_count'] > 0:
        ae_flagged[l['ae']] += 1
top_ae = max(ae_flagged.items(), key=lambda x: x[1]) if ae_flagged else ('N/A', 0)

bullets = [
    f"Of {len(leads)} stagnant MQLs, {total_flagged} ({100*total_flagged/len(leads):.0f}%) carry at least one quality flag. "
    f"SMB accounts for {smb_flagged} flagged leads ({100*smb_flagged/len(smb):.0f}% of SMB), "
    f"Mid-Market for {mm_flagged} ({100*mm_flagged/max(len(midmarket),1):.0f}%), "
    f"and Enterprise for {ent_flagged} ({100*ent_flagged/max(len(enterprise),1):.0f}%).",

    f"HIGH CONTACTS is the dominant flag across all segments — {smb_flags['HIGH CONTACTS']+mm_flags['HIGH CONTACTS']+ent_flags['HIGH CONTACTS']} leads "
    f"have been contacted 10 or more times with no progression, signaling either stale outreach or leads that should be formally disqualified.",

    f"{top_src[0]} is the top source by flagged volume: {top_src[1]['flagged']} flagged out of {top_src[1]['total']} total "
    f"({100*top_src[1]['flagged']/max(top_src[1]['total'],1):.0f}%). Review qualification criteria for this channel.",

    f"NON-CORE COUNTRY flags account for {smb_flags['NON-CORE COUNTRY']+mm_flags['NON-CORE COUNTRY']+ent_flags['NON-CORE COUNTRY']} leads. "
    f"Top non-core country: {top_nc[0]} ({top_nc[1]} leads). Country-level lead scoring filters should be evaluated.",

    f"The most over-worked lead has been contacted {most_contacted['contacts']} times "
    f"(Contact ID {most_contacted['contact_id']}, {most_contacted['segment']}, AE: {most_contacted['ae']}) "
    f"with no qualification. A disqualification SLA is recommended.",

    f"In Mid-Market and Enterprise, {top_ae[0]} has the highest number of flagged leads ({top_ae[1]}), "
    f"suggesting a pipeline review session is warranted.",
]

for b in bullets:
    pdf.bullet(b)
    pdf.ln(1)

# ── OVERALL FLAG SUMMARY TABLE ────────────────────────────────────────────────

pdf.ln(4)
pdf.sub_title('Overall Flag Summary')

flag_headers = ['Flag Type', 'SMB', 'Mid-Market', 'Enterprise', 'Total']
flag_rows = []
for ft in all_flag_types:
    t = smb_flags[ft] + mm_flags[ft] + ent_flags[ft]
    flag_rows.append([ft, smb_flags[ft], mm_flags[ft], ent_flags[ft], t])
# totals row
flag_rows.append([
    'TOTAL FLAGGED LEADS',
    smb_flagged, mm_flagged, ent_flagged,
    smb_flagged + mm_flagged + ent_flagged
])

pdf.table(flag_headers, flag_rows, col_widths=[90, 35, 45, 45, 35])

# ── SMB SECTION ───────────────────────────────────────────────────────────────

pdf.add_page()
pdf.section_title(f'SMB  —  {len(smb)} leads, {smb_flagged} flagged ({100*smb_flagged/max(len(smb),1):.0f}%)')

pdf.sub_title('Top 15 Most-Flagged Leads')
top15 = smb[:15]
smb_headers = ['AE', 'Email', 'Units', 'Days Stagnant', 'Contacts', 'Country', 'Flags']
smb_rows = []
for l in top15:
    smb_rows.append([
        l['ae'], l['email'], l['units'],
        l['days_stagnant'] if l['days_stagnant'] is not None else 'N/A',
        l['contacts'], l['country'],
        ', '.join(l['flags']) if l['flags'] else '—'
    ])
pdf.table(smb_headers, smb_rows, col_widths=[40, 65, 18, 28, 22, 32, 70])

pdf.sub_title('Traffic Source Breakdown')
src_headers = ['Source', 'Total', 'Flagged', '% Flagged', 'Avg Days Stagnant']
src_rows = [[s['source'], s['total'], s['flagged'], f"{s['pct']:.0f}%", f"{s['avg_days']:.0f}"] for s in smb_sources]
pdf.table(src_headers, src_rows, col_widths=[90, 30, 30, 35, 45])

pdf.sub_title('Key Observations')
# build observations
ps_src = next((s for s in smb_sources if 'Paid Social' in s['source']), None)
obs = []
if ps_src:
    obs.append(f"Paid Social drives the most SMB volume ({ps_src['total']} leads, {ps_src['pct']:.0f}% flagged). "
               f"Facebook is the primary sub-channel and generates significant personal-email traffic, though SMB personal emails are acceptable.")
high_c_smb = sum(1 for l in smb if 'HIGH CONTACTS' in l['flags'])
obs.append(f"{high_c_smb} SMB leads have been contacted 10+ times. These represent wasted AE time and should be disqualified or archived under a formal SLA.")
nc_smb = sum(1 for l in smb if 'NON-CORE COUNTRY' in l['flags'])
if nc_smb:
    obs.append(f"{nc_smb} SMB leads originate from non-core countries. Adding country filters to SMB paid campaigns could reduce noise significantly.")

for o in obs[:3]:
    pdf.bullet(o)
    pdf.ln(1)

# ── MID-MARKET SECTION ────────────────────────────────────────────────────────

pdf.add_page()
pdf.section_title(f'Mid-Market  —  {len(midmarket)} leads, {mm_flagged} flagged ({100*mm_flagged/max(len(midmarket),1):.0f}%)')

mm_flagged_leads = [l for l in midmarket if l['flag_count'] > 0]
pdf.sub_title(f'All Flagged Leads ({len(mm_flagged_leads)})')
mm_headers = ['AE', 'Email', 'Units', 'Days Stagnant', 'Contacts', 'Country', 'Flags']
mm_rows = []
for l in mm_flagged_leads:
    mm_rows.append([
        l['ae'], l['email'], l['units'],
        l['days_stagnant'] if l['days_stagnant'] is not None else 'N/A',
        l['contacts'], l['country'],
        ', '.join(l['flags']) if l['flags'] else '—'
    ])
pdf.table(mm_headers, mm_rows, col_widths=[40, 65, 18, 28, 22, 32, 70])

pdf.sub_title('Traffic Source Breakdown')
mm_src_rows = [[s['source'], s['total'], s['flagged'], f"{s['pct']:.0f}%", f"{s['avg_days']:.0f}"] for s in mm_sources]
pdf.table(src_headers, mm_src_rows, col_widths=[90, 30, 30, 35, 45])

pdf.sub_title('Per-AE Breakdown')
ae_headers = ['AE', 'Total Leads', 'Flagged', '% Flagged', 'Avg Contacts', 'Avg Days Stagnant']
ae_rows = [[a['ae'], a['total'], a['flagged'], f"{a['pct']:.0f}%", f"{a['avg_contacts']:.1f}", f"{a['avg_days']:.0f}"] for a in mm_ae]
pdf.table(ae_headers, ae_rows, col_widths=[55, 35, 30, 35, 40, 50])

pdf.sub_title('Key Observations')
mm_obs = []
mm_high_c = [l for l in midmarket if 'HIGH CONTACTS' in l['flags']]
if mm_high_c:
    mm_obs.append(f"{len(mm_high_c)} Mid-Market leads have HIGH CONTACTS (≥10 attempts). Each represents a missed commercial opportunity — a disqualification review is overdue.")
mm_pe = [l for l in midmarket if 'PERSONAL EMAIL' in l['flags']]
if mm_pe:
    mm_obs.append(f"{len(mm_pe)} Mid-Market leads registered with personal email addresses, indicating low intent or incorrect segmentation. Adding an email-domain validation gate is recommended.")
mm_nc = [l for l in midmarket if 'NON-CORE COUNTRY' in l['flags']]
if mm_nc:
    mm_obs.append(f"{len(mm_nc)} Mid-Market leads are from non-core countries. Marketing campaigns should be geo-targeted more precisely at this tier.")
top_mm_ae = max(mm_ae, key=lambda a: a['flagged']) if mm_ae else None
if top_mm_ae and top_mm_ae['flagged'] > 0:
    mm_obs.append(f"{top_mm_ae['ae']} carries {top_mm_ae['flagged']} flagged Mid-Market leads out of {top_mm_ae['total']} assigned "
                  f"(avg {top_mm_ae['avg_contacts']:.1f} contacts, {top_mm_ae['avg_days']:.0f} avg days stagnant). A pipeline review session is recommended.")

for o in mm_obs[:4]:
    pdf.bullet(o)
    pdf.ln(1)

# ── ENTERPRISE SECTION ────────────────────────────────────────────────────────

pdf.add_page()
pdf.section_title(f'Enterprise  —  {len(enterprise)} leads, {ent_flagged} flagged ({100*ent_flagged/max(len(enterprise),1):.0f}%)')

pdf.sub_title(f'All Enterprise Leads ({len(enterprise)})')
ent_headers = ['AE', 'Email', 'Units', 'Days Stagnant', 'Contacts', 'Country', 'Source', 'Flags']
ent_rows = []
for l in enterprise:
    ent_rows.append([
        l['ae'], l['email'], l['units'],
        l['days_stagnant'] if l['days_stagnant'] is not None else 'N/A',
        l['contacts'], l['country'], l['source'],
        ', '.join(l['flags']) if l['flags'] else '—'
    ])
pdf.table(ent_headers, ent_rows, col_widths=[38, 60, 14, 24, 20, 30, 35, 54])

pdf.sub_title('Per-AE Breakdown')
ent_ae_rows = [[a['ae'], a['total'], a['flagged'], f"{a['pct']:.0f}%", f"{a['avg_contacts']:.1f}", f"{a['avg_days']:.0f}"] for a in ent_ae]
pdf.table(ae_headers, ent_ae_rows, col_widths=[55, 35, 30, 35, 40, 50])

pdf.sub_title('Traffic Source Breakdown')
ent_src_rows = [[s['source'], s['total'], s['flagged'], f"{s['pct']:.0f}%", f"{s['avg_days']:.0f}"] for s in ent_sources]
pdf.table(src_headers, ent_src_rows, col_widths=[90, 30, 30, 35, 45])

# Individual lead commentary for concerning enterprise leads
concerning = [l for l in enterprise if l['flag_count'] >= 2 or l['contacts'] >= 10 or (l['days_stagnant'] or 0) >= 30]
if concerning:
    pdf.sub_title('Individual Lead Commentary (Concerning Leads)')
    for l in concerning:
        reasons = []
        if 'HIGH CONTACTS' in l['flags']:
            reasons.append(f"contacted {l['contacts']} times with no progression")
        if 'PERSONAL EMAIL' in l['flags']:
            reasons.append("registered with personal email (low intent signal for Enterprise)")
        if 'PROPERTY COUNT' in l['flags']:
            reasons.append(f"unit count ({l['units']}) >500 — suspect data")
        if 'NON-CORE COUNTRY' in l['flags']:
            reasons.append(f"non-core country ({l['country']})")
        if (l['days_stagnant'] or 0) >= 30 and 'HIGH CONTACTS' not in l['flags']:
            reasons.append(f"stagnant for {l['days_stagnant']} days")
        if reasons:
            commentary = f"Contact {l['contact_id']} ({l['ae']}): {'; '.join(reasons)}."
            pdf.bullet(commentary)
            pdf.ln(1)

# ── RECOMMENDATIONS ───────────────────────────────────────────────────────────

pdf.add_page()
pdf.section_title('Recommendations')

# compute for data-driven recs
total_high_c = smb_flags['HIGH CONTACTS'] + mm_flags['HIGH CONTACTS'] + ent_flags['HIGH CONTACTS']
total_nc     = smb_flags['NON-CORE COUNTRY'] + mm_flags['NON-CORE COUNTRY'] + ent_flags['NON-CORE COUNTRY']
total_pe     = mm_flags['PERSONAL EMAIL'] + ent_flags['PERSONAL EMAIL']
pct_nc_of_flags = 100 * total_nc / max(total_flagged, 1)

recs = []

# HIGH CONTACTS
recs.append(
    f"Implement a disqualification SLA: {total_high_c} leads have been contacted 10+ times with no response. "
    "Define a maximum contact threshold (e.g., 8 attempts over 30 days) after which a lead is automatically disqualified. "
    "This will free AE capacity and keep the pipeline accurate."
)

# Paid Social
ps_overall = all_sources.get('Paid Social', {'total': 0, 'flagged': 0})
if ps_overall['total']:
    ps_pct = 100 * ps_overall['flagged'] / ps_overall['total']
    recs.append(
        f"Paid Social generates {ps_overall['total']} MQLs ({ps_pct:.0f}% flagged). "
        "Review Facebook campaign targeting and MQL scoring thresholds — particularly for leads from non-core geos and personal emails. "
        "Consider requiring phone number or business email as a qualifying field."
    )

# Non-core country
if pct_nc_of_flags > 10:
    recs.append(
        f"Non-core country leads represent {total_nc} flags ({pct_nc_of_flags:.0f}% of all flags). "
        "Add country-level exclusions or scoring penalties in HubSpot for traffic originating outside core regions (Spain, Germany, Italy, Czech Republic, UK, Austria, UAE, Saudi Arabia)."
    )

# Personal email Mid-Market/Enterprise
if total_pe > 0:
    recs.append(
        f"{total_pe} Mid-Market/Enterprise leads registered with personal email addresses. "
        "Add an email domain validation gate to the MQL scoring workflow — personal domains should trigger a lower score or a manual review step before an AE is assigned."
    )

# AE review
recs.append(
    f"Schedule a disqualification review session with {top_ae[0]}, who has the highest flagged lead count in Mid-Market/Enterprise ({top_ae[1]} flagged). "
    "Walk through each flagged lead and formally close or recycle them. This will improve pipeline hygiene and reporting accuracy."
)

# Property count
pc_total = smb_flags['PROPERTY COUNT'] + mm_flags['PROPERTY COUNT'] + ent_flags['PROPERTY COUNT']
if pc_total > 0:
    recs.append(
        f"{pc_total} leads report more than 500 rooms/properties. These are likely data errors, spam submissions, or incorrectly imported records. "
        "Add a server-side validation or HubSpot workflow to flag >500 unit submissions for manual review before MQL assignment."
    )

for i, rec in enumerate(recs[:6], 1):
    pdf.set_font('Helvetica', '', 9)
    pdf.multi_cell(0, 5, safe(f'{i}. {rec}'))
    pdf.ln(2)

# ── APPENDIX ──────────────────────────────────────────────────────────────────

pdf.add_page()
pdf.section_title('Appendix — All Flagged Leads')

all_flagged = sorted(
    [l for l in leads if l['flag_count'] > 0],
    key=lambda l: (
        ['SMB', 'Mid-Market', 'Enterprise'].index(l['segment']) if l['segment'] in ['SMB', 'Mid-Market', 'Enterprise'] else 99,
        -l['flag_count']
    )
)

app_headers = ['Contact ID', 'AE', 'Segment', 'Email', 'Units', 'Country', 'Source', 'Contacts', 'Days', 'Flags']
app_rows = []
for l in all_flagged:
    app_rows.append([
        l['contact_id'], l['ae'], l['segment'], l['email'], l['units'],
        l['country'], l['source'], l['contacts'],
        l['days_stagnant'] if l['days_stagnant'] is not None else 'N/A',
        ', '.join(l['flags'])
    ])

pdf.table(app_headers, app_rows, col_widths=[28, 36, 24, 60, 14, 28, 32, 20, 16, 72])

# ── SAVE ──────────────────────────────────────────────────────────────────────

pdf.output(pdf_path)
print(f"\nPDF saved to: {pdf_path}")
