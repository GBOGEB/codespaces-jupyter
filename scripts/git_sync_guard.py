#!/usr/bin/env python3
"""Fail-closed GitHub-first sync helper.

The helper never merges a dirty or diverged local tree. It is intended for the
local Jupyter/Spyder workflow where GitHub is the intermediate synchronization
surface between remote tasks and the workstation clone.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=check,
        text=True,
        capture_output=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pull", action="store_true", help="fast-forward from origin/main when safe")
    args = parser.parse_args()

    try:
        root = Path(run("rev-parse", "--show-toplevel").stdout.strip())
    except subprocess.CalledProcessError:
        print("RED: not inside a Git repository", file=sys.stderr)
        return 2

    dirty = run("status", "--porcelain").stdout.splitlines()
    receipt = {
        "schema": "gbogeb.git_sync_guard/v1",
        "repo_root": str(root),
        "dirty": bool(dirty),
        "dirty_entries": dirty,
        "pull_requested": args.pull,
    }
    if dirty:
        receipt["status"] = "RED_DIRTY_TREE"
        print(json.dumps(receipt, indent=2))
        return 2

    remote = run("remote", "get-url", "origin", check=False)
    if remote.returncode != 0:
        receipt["status"] = "RED_NO_ORIGIN"
        print(json.dumps(receipt, indent=2))
        return 2

    receipt["origin"] = remote.stdout.strip()
    run("fetch", "--prune", "origin", "main")
    counts = run("rev-list", "--left-right", "--count", "HEAD...origin/main").stdout.strip().split()
    ahead, behind = map(int, counts)
    receipt.update({"ahead": ahead, "behind": behind})

    if ahead and behind:
        receipt["status"] = "RED_DIVERGED"
        print(json.dumps(receipt, indent=2))
        return 3

    if ahead:
        receipt["status"] = "YELLOW_LOCAL_COMMITS_NOT_ON_MAIN"
        print(json.dumps(receipt, indent=2))
        return 3

    if args.pull and behind:
        run("pull", "--ff-only", "origin", "main")
        receipt["status"] = "GREEN_FAST_FORWARDED"
    elif behind:
        receipt["status"] = "YELLOW_BEHIND_REMOTE"
    else:
        receipt["status"] = "GREEN_UP_TO_DATE"

    receipt["head"] = run("rev-parse", "HEAD").stdout.strip()
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"].startswith("GREEN") else 1


if __name__ == "__main__":
    raise SystemExit(main())
