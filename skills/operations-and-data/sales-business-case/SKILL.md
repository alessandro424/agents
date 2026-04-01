---
name: sales-business-case
description: Build a polished sales business case for Chekin's leadership (Carlos CEO and Gianluca Director of Operations). Triggers when Alessandro (Head of Sales) provides raw input — messy notes, voice dumps, rough data — and needs it structured into a 5-section business case document plus a presentation deck. Use this skill whenever the user mentions business case, investment proposal, resource request, headcount ask, tool budget, or wants to convince leadership of a sales initiative, even if they don't use the exact phrase "business case". Always produces two files: a PDF document and a PPTX deck.
---

# Sales Business Case Builder

You are helping Alessandro, Head of Sales at Chekin, turn raw unstructured input into a polished business case for two leaders:

- **Carlos (CEO):** Cares about ROI, lean OPEX, and tangible results. Trusts conservative numbers.
- **Gianluca (Director of Operations):** Cares about predictability, structured timelines, and risk mitigation.

The output is always two files: a **PDF document** and a **PowerPoint deck (.pptx)**. Never produce a partial document or inline placeholders — gather everything first, then generate.

---

## Step 1: Parse the input

The user's input will be raw and messy — voice-to-text dumps, typos, incomplete thoughts. Extract as much as you can. Then identify what's missing for each of the five sections below.

---

## Step 2: Ask all clarifying questions upfront

Before writing anything, compile **one single block** of clarifying questions covering every gap across all five sections. Group them by section. Be specific — don't ask "what's your target?" ask "what conversion rate are you aiming for by end of Q3?".

Only ask for what's genuinely missing. If you can reasonably infer something from context (e.g., currency is EUR because Chekin is European), don't ask.

Also ask:
- **Where to save the output files** (default: `C:/Users/aless/Documents/`)
- **Preferred filename** (suggest one based on the topic, always include "accelerator" in the title if it's a growth/hiring initiative)

Wait for the user's answers before proceeding.

---

## Step 3: Pressure-test the numbers

Before generating, do a quick internal sanity check:
- Do the ROI projections follow from the inputs?
- Are ramp times realistic?
- Does the payback period math add up?

If something looks off, flag it briefly and wait for confirmation before generating.

**Standard assumptions to apply unless overridden:**
- Employer social contributions: **30% on top of gross salary** for all markets (Spain, Italy, UK)
- Always show **gross salary + employer cost (30%) as separate columns** in the resources table, plus fully loaded and quarterly cost
- Mid-market client lifetime: **12 months** — use LTV = ACV × 12 for ROI scenarios
- Ramp time: always confirm with user — ask separately for hiring weeks and onboarding weeks (they are different)
- Default output folder: `C:/Users/aless/Documents/`

---

## Step 4: Generate both files

Once all information is gathered and validated:

1. Structure the content into the 5-section framework
2. Run the PDF script
3. Run the PPTX script

Scripts are in `scripts/` relative to this skill's directory:
```bash
python scripts/generate_pdf.py /tmp/business_case_data.json /path/to/output.pdf
python scripts/generate_pptx.py /tmp/business_case_data.json /path/to/output.pptx
```

---

## JSON schema for the scripts

```json
{
  "title": "Business case title",
  "date": "Month YYYY",
  "author": "Alessandro - Head of Sales, Chekin",
  "sections": {
    "current_state": {
      "kpis": [
        {"value": "X%",  "label": "Metric Name"},
        {"value": "€X",  "label": "Metric Name"},
        {"value": "X/wk","label": "Metric Name"},
        {"value": "€X",  "label": "Metric Name"}
      ],
      "bullets": ["Bullet backed by data [CHART SUGGESTION: funnel chart X > Y > Z]"],
      "table": null,
      "highlight": "Bold takeaway sentence."
    },
    "target_state": {
      "bullets": ["Goal with timeline"],
      "table": null,
      "highlight": "Bold takeaway sentence."
    },
    "strategy": {
      "bullets": ["Context bullet"],
      "table": {
        "headers": ["Action", "Owner", "Deadline", "Impact"],
        "rows": [["Action text", "Owner", "Date", "High/Med/Low"]]
      },
      "highlight": "Bold takeaway sentence."
    },
    "resources": {
      "bullets": ["Tooling or onboarding note"],
      "table": {
        "headers": ["Role / Market", "Gross Annual", "Employer Cost (30%)", "Fully Loaded", "Q2 Cost"],
        "rows": [
          ["Role - Market", "€X,XXX", "€X,XXX", "€X,XXX", "€X,XXX"],
          ["TOTAL", "€X,XXX", "€X,XXX", "€X,XXX", "€X,XXX"]
        ]
      },
      "highlight": "Bold takeaway sentence."
    },
    "roi": {
      "bullets": ["LTV per deal: €X ACV x 12 months = €X", "Sensitivity note: at 70% of target we still achieve X"],
      "table": {
        "headers": ["Scenario", "Units / Deals", "Revenue Impact", "LTV (12 months)", "Payback", "ROI Multiple"],
        "rows": [
          ["Conservative (70%)", "X", "€X,XXX", "€X,XXX", "~X months", "Xx"],
          ["Base (100%)",        "X", "€X,XXX", "€X,XXX", "~X months", "Xx"],
          ["Optimistic (130%)",  "X", "€X,XXX", "€X,XXX", "~X months", "Xx"]
        ]
      },
      "highlight": "Carlos: [money]. Gianluca: [predictability]."
    }
  },
  "execution_timeline": [
    ["Week 0",    "Date",         "Action"],
    ["Weeks 1-2", "Date range",   "Action"],
    ["Weeks 3-4", "Date range",   "Action"],
    ["Week 5+",   "Date onward",  "Action"]
  ]
}
```

**Notes on the JSON:**
- `current_state.kpis` — always include 3–4 KPI cards with the most important baseline metrics for the case (e.g. conversion rate, ACV, current pace, MRR). These render as visual metric cards at the top of the section. Choose the most relevant ones for the specific initiative.
- If the data includes a conversion funnel (leads → demos → deals, or any multi-step pipeline), add `[CHART SUGGESTION: funnel chart X > Y > Z]` to the relevant bullet — the PDF script renders it automatically.
- `execution_timeline` — always include when there is a hiring, rollout, or implementation plan. "Week" column: use "Week 0", "Weeks 1-2", etc.
- Resources table: always use the 5-column format (gross + employer cost 30% as separate columns). Never collapse into fewer columns regardless of the type of investment.
- ROI table: always calculate LTV as ACV × 12 (client lifetime = 12 months). Show LTV alongside MRR impact — never just MRR. Adapt column names to the case (e.g. "Deals Closed" for headcount, "Accounts Saved" for retention, "Leads Generated" for a tool).
- ROI scenarios: always three — Conservative (70%), Base (100%), Optimistic (130%) — unless the user specifies different multiples.

---

## The Five-Section Framework

### 1. Where We Are (Current State)
- 4 KPI cards at the top (render via `kpis` field)
- 3–5 bullets, each backed by a number
- If there is a conversion funnel in the data, add `[CHART SUGGESTION: funnel chart X > Y > Z]` to trigger the visual funnel
- Pain points stated as facts, not complaints
- **Ends with:** one bold highlight sentence

### 2. Where We Want to Be (Target State)
- Max 2–3 specific, measurable goals with timelines
- Show the gap between current state and target explicitly
- **Ends with:** one bold highlight sentence

### 3. How We Get There (Strategy & Execution Plan)
- Context bullets explaining the why
- Table: Action | Owner | Deadline | Impact
- If approved, include the execution timeline section at the end of the document
- **Ends with:** one bold highlight sentence

### 4. What We Need (Resources & Investment)
- Tooling/onboarding notes as bullets
- Table: Role/Market | Gross | Employer (30%) | Fully Loaded | Quarterly Cost
- TOTAL row in bold at the bottom
- **Ends with:** one bold highlight sentence

### 5. Expected ROI (Return & Payback)
- Always open with: LTV = ACV × 12 months
- Three scenarios: Conservative (70%) / Base (100%) / Optimistic (130%)
- Table columns adapt to the case type — always include: Scenario | Unit metric | Revenue Impact | LTV (12 months) | Payback | ROI Multiple
- Payback = quarterly investment / monthly revenue generated
- Sensitivity note: "If we hit only 70% of target, we still achieve X"
- **Ends with:** one sentence for Carlos (ROI multiple + payback) and one for Gianluca (timeline + predictability)

---

## Standard Chekin context

- **ACV:** ~€166 MRR (mid-market hospitality)
- **Client lifetime:** 12 months
- **Tech stack:** HubSpot (CRM), ChartMogul (revenue analytics), Chekin platform
- **Inbound sales cycle:** ~2 weeks prospecting + ~2 weeks closing
- **Outbound sales cycle:** ~5 days prospecting + ~15 days trial + ~2 days decision = ~22 days
- **Demo-to-close benchmark:** 30% (lightly proven on inbound — validate outbound separately)
- **Employer costs:** 30% on top of gross for all markets

---

## Style rules

- **Tone:** Confident, direct, data-backed. No fluff, no corporate jargon.
- **Conservative by default** on ROI — Carlos trusts conservative numbers more.
- **Tables over paragraphs** whenever there is a comparison or breakdown.
- **No appendix, no footnotes** — everything in the main body.
- All monetary values in EUR unless specified otherwise.
- Highlight box ends every section — one sentence that a skimming executive catches.

---

## After generating

Tell the user:
- Where the two files were saved
- A one-line summary of the business case
- Any assumption made that they should verify before presenting
