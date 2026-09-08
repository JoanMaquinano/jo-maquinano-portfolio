import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
SYNC_DIR = ROOT / "profile-sync"
LINKEDIN_FILE = SYNC_DIR / "linkedin-profile.json"
GITHUB_FILE = SYNC_DIR / "github-profile.json"
SNAPSHOT_FILE = SYNC_DIR / "profile-snapshot.json"
REPORT_FILE = SYNC_DIR / "profile-update.md"


def fetch_json(url):
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "portfolio-profile-sync",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def fetch_text(url):
    request = Request(url, headers={"Accept": "text/plain", "User-Agent": "portfolio-profile-sync"})
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    username = os.environ.get("GITHUB_USERNAME", "JoanMaquinano")
    profile = fetch_json(f"https://api.github.com/users/{username}")
    repositories = fetch_json(
        f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    )
    readme_url = f"https://raw.githubusercontent.com/{username}/{username}/main/README.md"

    try:
        readme = fetch_text(readme_url)
    except (HTTPError, URLError) as error:
        print(f"GitHub profile README could not be fetched: {error}", file=sys.stderr)
        readme = ""

    linkedin = json.loads(LINKEDIN_FILE.read_text(encoding="utf-8"))
    synced_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    github = {
        "login": profile.get("login"),
        "name": profile.get("name"),
        "bio": profile.get("bio"),
        "blog": profile.get("blog"),
        "location": profile.get("location"),
        "public_repos": profile.get("public_repos"),
        "followers": profile.get("followers"),
        "profile_url": profile.get("html_url"),
        "readme": readme,
        "repositories": [
            {
                "name": repo.get("name"),
                "description": repo.get("description"),
                "html_url": repo.get("html_url"),
                "language": repo.get("language"),
                "topics": repo.get("topics", []),
                "updated_at": repo.get("updated_at"),
            }
            for repo in repositories
        ],
    }
    snapshot = {"synced_at": synced_at, "github": github, "linkedin": linkedin}
    write_json(GITHUB_FILE, github)
    write_json(SNAPSHOT_FILE, snapshot)

    report = [
        "# Proposed profile sync",
        "",
        f"Generated: `{synced_at}`",
        "",
        "Review this pull request before merging. No live portfolio content is changed automatically.",
        "",
        "## GitHub changes to review",
        "",
        f"- Public repositories: **{github['public_repos']}**",
        f"- Followers: **{github['followers']}**",
        f"- Profile: [{github['login']}]({github['profile_url']})",
        f"- README characters captured: **{len(readme)}**",
        "",
        "## LinkedIn source",
        "",
        "- Profile: [LinkedIn](https://www.linkedin.com/in/jrmaquinano/)",
        f"- Last manually reviewed: `{linkedin.get('last_reviewed', '')}`",
        "",
        "## Approval checklist",
        "",
        "- [ ] Confirm the GitHub repository list and descriptions.",
        "- [ ] Review or update `linkedin-profile.json` if LinkedIn changed.",
        "- [ ] Make any intended `index.html` content edits in this pull request.",
        "- [ ] Merge only after approving the proposed changes.",
        "",
    ]
    REPORT_FILE.write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
