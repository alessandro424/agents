---
name: hiring-assistant
description: Generates Job Descriptions (JD), Job Offers, and Slack messages for HR to open new roles. Use this skill whenever a user needs to hire for a new position or create hiring-related documents.
---

# Hiring Assistant

This skill helps you streamline the process of opening new roles and managing hiring documents. It generates plain text outputs for Job Descriptions, Job Offers, and internal HR communications via Slack.

## Workflow

1.  **Capture Role Details**: Ask the user for the role name, key responsibilities, and any specific requirements if not already provided.
2.  **Generate Job Description (JD)**: Create a detailed JD in plain text.
3.  **Generate Job Offer**: Create a formal but friendly offer letter in plain text.
4.  **Generate HR Slack Message**: Create a concise message for the HR team to initiate the role-opening process.

---

## Output Formats

### 1. Job Description (JD)
The JD should be structured clearly in plain text:
- **Title**: [Role Name]
- **Summary**: A brief overview of the role and the company.
- **Key Responsibilities**: A bulleted list of what the person will do.
- **Requirements**: A bulleted list of qualifications and skills.
- **Perks & Benefits**: Why they should join.

### 2. Job Offer
The Offer should be a friendly, professional letter:
- **Subject**: Job Offer - [Role Name] - [Candidate Name]
- **Body**: Congratulations, role details, compensation (placeholders), start date (placeholder), and next steps.

### 3. HR Slack Message
A concise message for HR:
"Hi HR Team, I'd like to open a new role for [Role Name]. Attached is the JD. Key details: [Brief summary]. Let me know what else you need to get this posted!"

---

## Guidelines
- **Format**: ALWAYS use plain text. Do not use Markdown styling in the final output provided to the user, except for simple bullet points (-) and headers (UPPERCASE).
- **Tone**: Professional, welcoming, and clear.
- **Placeholders**: Use [BRACKETS] for information that needs to be filled in (e.g., [SALARY], [CANDIDATE NAME]).
