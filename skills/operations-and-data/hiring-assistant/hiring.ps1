# hiring.ps1
# Usage: ./hiring.ps1 "Senior Developer"

param(
    [Parameter(Mandatory=$false)]
    [string]$Role = "Software Engineer"
)

Write-Host "Executing hiring-assistant skill for role: $Role..." -ForegroundColor Cyan

claude -p "Generate the hiring docs for a '$Role' (JD, Offer, and HR Slack message in plain text) using the hiring-assistant skill."
