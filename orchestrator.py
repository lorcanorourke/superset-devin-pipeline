import os, json, datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from github import Github
from devin_client import create_session, poll_session
from dotenv import load_dotenv

load_dotenv()

def process_issue(issue_data):
    """Handle one issue end to end - runs in its own thread."""
    issue_number = issue_data["number"]
    issue_title = issue_data["title"]
    issue_url = issue_data["url"]
    repo_full = os.environ["GITHUB_REPO"]

    print(f"[START] Issue #{issue_number}: {issue_title}")

    session_id = create_session(
        issue_title=issue_title,
        issue_url=issue_url,
        repo_url=f"https://github.com/{repo_full}"
    )

    result = poll_session(session_id)
    status = result.get("status")
    pr_url = result.get("pr_url")

    print(f"[DONE] Issue #{issue_number}: {status} | PR: {pr_url}")

    return {
        "issue_number": issue_number,
        "issue_title": issue_title,
        "session_id": session_id,
        "status": status,
        "pr_url": pr_url,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

def run_automation():
    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(os.environ["GITHUB_REPO"])

    issues = list(repo.get_issues(labels=["devin-task"], state="open"))
    print(f"Found {len(issues)} issues to remediate\n")
    print(f"Spinning up {len(issues)} Devin sessions in parallel...\n")

    # Prepare issue data (PyGithub objects aren't thread-safe, so extract first)
    issue_data_list = [
        {"number": i.number, "title": i.title, "url": i.html_url}
        for i in issues
    ]

    results = []
    # Run all issues concurrently
    with ThreadPoolExecutor(max_workers=len(issue_data_list) or 1) as executor:
        futures = {executor.submit(process_issue, d): d for d in issue_data_list}
        for future in as_completed(futures):
            results.append(future.result())

    # Post status comments after all complete
    for r in results:
        issue = repo.get_issue(r["issue_number"])
        status_emoji = "✅" if r["status"] in ("completed", "finished") else "❌"
        pr_line = f"\nPull request: {r['pr_url']}" if r.get("pr_url") else ""
        issue.create_comment(
            f"{status_emoji} **Devin automation update**\n\n"
            f"Session ID: `{r['session_id']}`\n"
            f"Status: **{r['status']}**{pr_line}\n"
            f"View session: https://app.devin.ai/sessions/{r['session_id']}"
        )

    return results

def write_github_summary(results):
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    total = len(results)
    completed = sum(1 for r in results if r["status"] in ("completed", "finished"))
    failed = total - completed
    rate = f"{round(completed/total*100)}%" if total else "N/A"
    with open(summary_path, "a") as f:
        f.write("# Devin Remediation Report\n\n")
        f.write(f"**Total tasks:** {total}  \n")
        f.write(f"**Completed:** {completed}  \n")
        f.write(f"**Failed:** {failed}  \n")
        f.write(f"**Success rate:** {rate}\n\n")
        f.write("| Issue | Title | Status | Pull Request |\n")
        f.write("|-------|-------|--------|-------------|\n")
        for r in results:
            pr = f"[PR]({r['pr_url']})" if r.get("pr_url") else "—"
            f.write(
                f"| #{r['issue_number']} | {r['issue_title']} | {r['status']} | {pr} |\n"
            )

if __name__ == "__main__":
    results = run_automation()

    with open("report.json", "w") as f:
        json.dump(results, f, indent=2)

    write_github_summary(results)

    total = len(results)
    completed = sum(1 for r in results if r["status"] in ("completed", "finished"))
    print(f"\n=== SUMMARY ===")
    print(f"Total:     {total}")
    print(f"Completed: {completed}")
    print(f"Failed:    {total - completed}")
    print(f"Report saved to report.json")