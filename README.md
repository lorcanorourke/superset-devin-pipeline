# superset-devin-pipeline
 
Automated security remediation for Apache Superset using the Devin API. Built as part of exploring how AI agents can handle routine engineering work autonomously.
 
## The problem
 
Security vulnerabilities and dependency issues pile up. Engineers know they need to fix them but there's always something more urgent. This pipeline removes that friction — label an issue, Devin handles the rest.
 
## How it works
 
1. A GitHub issue is created (e.g. a CVE in a dependency)
2. Add the `devin-task` label
3. GitHub Actions picks it up automatically
4. Devin investigates the codebase, posts a triage comment on the issue
5. Devin opens a pull request with the fix
6. A report is saved locally with session status
```
issue labeled → GitHub Actions → orchestrator.py → Devin API → PR + comment
```
 
## Setup
 
You'll need:
- A Devin account with API access (service user)
- A GitHub personal access token with `repo` and `workflow` scopes
Create a `.env` file in the root:
 
```
DEVIN_API_KEY=cog_your_key_here
DEVIN_ORG_ID=org-your_org_id_here
GITHUB_TOKEN=ghp_your_token_here
GITHUB_REPO=yourname/superset
```
 
### Run locally
 
```bash
pip install -r requirements.txt
python orchestrator.py
```
 
### Run with Docker
 
```bash
docker build -t superset-devin-pipeline .
docker run --env-file .env superset-devin-pipeline
```
 
### GitHub Actions
 
Add the following secrets to your repository settings under Actions:
 
- `DEVIN_API_KEY`
- `DEVIN_ORG_ID`  
- `GITHUB_TOKEN`
The workflow triggers automatically when an issue is labeled `devin-task`, or you can trigger it manually from the Actions tab.
 
## Observability
 
Each run saves a `report.json`:
 
```json
[
  {
    "issue_number": 1,
    "issue_title": "Upgrade Pillow - security vulnerability",
    "session_id": "abc123",
    "status": "completed",
    "timestamp": "2026-05-30T19:00:00"
  }
]
```
 
Devin also posts a comment directly on each GitHub issue with the session link so you can see exactly what it did.
 
To watch a session in real time: `https://app.devin.ai/sessions/{session_id}`
 
## Files
 
- `orchestrator.py` — main script, reads open issues and kicks off Devin sessions
- `devin_client.py` — handles Devin API calls (create session, poll status)
- `webhook_server.py` — optional Flask server if you want webhook-based triggering instead of Actions
- `.github/workflows/devin-automation.yml` — GitHub Actions workflow
## Repos
 
- This repo: `github.com/lorcanorourke/superset-devin-pipeline`
- Superset fork (with issues and PRs): `github.com/lorcanorourke/superset`
## Notes
 
This is intentionally kept simple. The goal was a working end-to-end demo, not a production system. Next steps would be adding Slack notifications, connecting a security scanner as the trigger, and extending to multiple repos.