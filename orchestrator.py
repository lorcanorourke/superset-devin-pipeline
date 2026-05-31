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

def write_github_summary(results):
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    total = len(results)
    completed = sum(1 for r in results if r["status"] == "completed")
    failed = total - completed
    rate = f"{round(completed/total*100)}%" if total else "N/A"
    with open(summary_path, "a") as f:
        f.write("# Devin Remediation Report\n\n")
        f.write(f"**Total tasks:** {total}  \n")
        f.write(f"**Completed:** {completed}  \n")
        f.write(f"**Failed:** {failed}  \n")
        f.write(f"**Success rate:** {rate}\n\n")
        f.write("| Issue | Title | Status | Session |\n")
        f.write("|-------|-------|--------|--------|\n")
        for r in results:
            f.write(
                f"| #{r['issue_number']} | {r['issue_title']} | {r['status']} | "
                f"[view](https://app.devin.ai/sessions/{r['session_id']}) |\n"
            )

if __name__ == "__main__":
    results = run_automation()

    with open("report.json", "w") as f:
        json.dump(results, f, indent=2)

    write_github_summary(results)

    total = len(results)
    completed = sum(1 for r in results if r["status"] == "completed")
    print(f"\n=== SUMMARY ===")
    print(f"Total:     {total}")
    print(f"Completed: {completed}")
    print(f"Failed:    {total - completed}")
    print(f"Report saved to report.json")