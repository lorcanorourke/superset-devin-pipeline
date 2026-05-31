import os, json, datetime
from github import Github
from devin_client import create_session, poll_session
from dotenv import load_dotenv

load_dotenv()

def run_automation():
    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(os.environ["GITHUB_REPO"])
    
    issues = list(repo.get_issues(labels=["devin-task"], state="open"))
    print(f"Found {len(issues)} issues to remediate")
    
    results = []
    
    for issue in issues:
        print(f"\n--- Processing: {issue.title} ---")
        
        session_id = create_session(
            issue_title=issue.title,
            issue_url=issue.html_url,
            repo_url=f"https://github.com/{os.environ['GITHUB_REPO']}"
        )
        
        result = poll_session(session_id)
        
        entry = {
            "issue_number": issue.number,
            "issue_title": issue.title,
            "session_id": session_id,
            "status": result.get("status"),
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        results.append(entry)
        
        status_emoji = "✅" if result.get("status") == "completed" else "❌"
        issue.create_comment(
            f"{status_emoji} **Devin automation update**\n\n"
            f"Session ID: `{session_id}`\n"
            f"Status: **{result.get('status')}**\n"
            f"View session: https://app.devin.ai/sessions/{session_id}"
        )
    
    return results

if __name__ == "__main__":
    results = run_automation()
    
    with open("report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    total = len(results)
    completed = sum(1 for r in results if r["status"] == "completed")
    print(f"\n=== SUMMARY ===")
    print(f"Total:     {total}")
    print(f"Completed: {completed}")
    print(f"Failed:    {total - completed}")
    print(f"Report saved to report.json")