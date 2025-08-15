import subprocess
import json
import webbrowser
import re
import sys
import pathlib
import datetime

pend = json.loads(
    pathlib.Path(".agent/changes/pending.json").read_text(encoding="utf-8-sig")
)


def sh(cmd):
    return (
        subprocess.check_output(cmd, shell=True)
        .decode("utf-8", errors="ignore")
        .strip()
    )


def parse_remote(u):
    if u.startswith("git@"):
        m = re.search(r":(.+)/(.+)\.git$", u)
        return m.group(1), m.group(2)
    if u.startswith("https://"):
        m = re.search(r"github\.com/([^/]+)/([^/]+)\.git$", u)
        return m.group(1), m.group(2)
    raise RuntimeError("unsupported remote url")


def now():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:24]


def main():
    try:
        sh("git rev-parse --is-inside-work-tree")
    except Exception:
        print("not a git repo")
        sys.exit(1)
    owner, repo = parse_remote(sh("git config --get remote.origin.url"))
    sh("git fetch --all")
    try:
        sh("git switch main")
    except Exception:
        sh("git checkout -b main")
    try:
        sh("git pull --ff-only")
    except Exception:
        pass
    branch = f"feature/{now()}-{slug(pend.get('summary','change'))}"
    try:
        sh(f'git checkout -b "{branch}"')
    except Exception:
        sh(f'git switch "{branch}"')
    try:
        sh("git add -A")
        sh(
            f'git commit -m "{pend.get("summary","update")} [changeset:{pend.get("id","")}]""'
        )
    except Exception:
        pass
    sh(f'git push -u origin "{branch}"')
    pr = f"https://github.com/{owner}/{repo}/compare/{branch}?expand=1"
    print("Open PR:", pr)
    webbrowser.open(pr)


if __name__ == "__main__":
    main()
