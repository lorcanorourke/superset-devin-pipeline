import os, requests, time
from dotenv import load_dotenv

load_dotenv()

def get_headers():
    return {
        "Authorization": f"Bearer {os.environ['DEVIN_API_KEY']}",
        "Content-Type": "application/json"
    }

def create_session(issue_title, issue_url, repo_url):
    org_id = os.environ['DEVIN_ORG_ID']
    prompt = f"""
You are an autonomous engineering assistant working on a GitHub repository.

Repository: {repo_url}
Issue: {issue_title}
Issue URL: {issue_url}

Step 1 - TRIAGE: Analyze the issue and post a comment on the GitHub issue at {issue_url} with:
- Root cause analysis
- Which files are affected
- Estimated complexity (simple/medium/complex)
- Your planned fix approach

Step 2 - FIX: Implement the fix in the codebase.

Step 3 - VERIFY: Where it makes sense, add or update a test that proves the fix
works, and run the relevant tests or checks to confirm nothing is broken.
Briefly note in the PR what you ran to verify.

Step 4 - PR: Open a pull request referencing the issue with a clear description
of the root cause, what you changed, and how you verified it.
"""
    response = requests.post(
        f"https://api.devin.ai/v3/organizations/{org_id}/sessions",
        headers=get_headers(),
        json={"prompt": prompt}
    )
    data = response.json()
    print(f"Full API response: {data}")
    session_id = data["session_id"]
    print(f"Created session: {session_id}")
    return session_id

def poll_session(session_id, timeout=900):
    org_id = os.environ['DEVIN_ORG_ID']
    print(f"Polling session {session_id}...")
    for i in range(timeout // 20):
        response = requests.get(
            f"https://api.devin.ai/v3/organizations/{org_id}/sessions/{session_id}",
            headers=get_headers()
        )
        data = response.json()
        status = data.get("status", "unknown")
        print(f"  [{i*20}s] Status: {status}")
        if status in ("completed", "failed", "stopped", "finished"):
            # Pull the real PR URL out of the response if Devin opened one
            pr_url = None
            prs = data.get("pull_requests") or []
            if prs:
                pr_url = prs[0].get("pr_url")
            data["pr_url"] = pr_url
            return data
        time.sleep(20)
    return {"status": "timeout", "session_id": session_id, "pr_url": None}