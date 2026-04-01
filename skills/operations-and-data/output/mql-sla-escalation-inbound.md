# HubSpot Workflow: MQL SLA Escalation (Inbound Only)

This workflow ensures that every Inbound MQL is contacted within 4 hours. It only applies to new contacts created starting today (March 24, 2026).

## Contact Enrollment Triggers

- **Lifecycle stage** is any of `Marketing Qualified Lead`
- **AND** **Original source** is any of `Inbound` (includes Organic Search, Direct Traffic, Social Media, etc.)
- **AND** **Create date** is after `2026-03-23`

> [!NOTE]
> Set "Enroll existing contacts who meet these criteria" to **No** when activating to ensure it only impacts new leads.

## Workflow Actions

### 1. Wait Step
- **Wait** for 4 hours (Business hours only recommended).

### 2. If/Then Branch: Verify Contact
- **Condition:** `Last contacted` is known **OR** `Number of sales activities` is greater than 0.
- **YES (Contacted):** Do nothing (Close workflow).
- **NO (Not Contacted):** Proceed to Escalation.

### 3. Escalation Actions
- **Send internal email notification:**
    - To: `Sales Manager`
    - Subject: `SLA Breach: [Contact Name] (Inbound MQL)`
    - Body: `Inbound MQL [Contact Name] has not been contacted within the 4-hour SLA. Please check status.`
- **Slack Notification:** Send alert to `#sales-alerts`.
- **Set property value:** Update `SLA Status` to `Breached`.

## Final Implementation Checklist

1.  **Create Custom Property:** Ensure `SLA Status` (Dropdown: `Normal`, `Warning`, `Breached`) exists in your HubSpot portal to track these escalations.
2.  **Test the Trigger:** Enroll a test contact with `Source = Inbound` and `Lifecycle Stage = MQL` to confirm the wait step initiates correctly.
3.  **Slack Integration:** Verify that the HubSpot-Slack integration is active for the `#sales-alerts` channel.

---

## Strategy Notes (Based on RevOps Skill):
1. **Speed-to-Lead:** Inbound leads drop in value by 10x after 30 minutes. A 4-hour SLA is the upper limit for "hot" leads.
2. **Data Cleanliness:** By using `Create date` and `Original source`, we avoid enrolling old leads or low-intent outbound leads into this high-priority escalation.
3. **Accountability:** Escalating to a manager ensures that bottlenecks in the sales process are identified early rather than when it's too late to save the deal.
