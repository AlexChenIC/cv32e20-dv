#!/usr/bin/env python3
# Copyright 2026 OpenHW Group
# SPDX-License-Identifier: Apache-2.0
"""Collect GitHub Actions run/job data for the CV32E20 dashboard."""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from parser import parse_job_name


WORKFLOWS = {
    "cv32e20_dv": "cv32e20-dv-ci.yml",
    "cve2_act": "cve2-act-ci.yml",
}
MAX_HISTORY = 50


def gh_api(repo: str, endpoint: str) -> dict:
    result = subprocess.run(
        ["gh", "api", f"/repos/{repo}/actions/{endpoint}", "--paginate"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        if "Not Found" in result.stderr or "HTTP 404" in result.stderr:
            return {"workflow_missing": True}
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    return json.loads(result.stdout)


def fetch_runs(repo: str, workflow_file: str, count: int) -> list:
    data = gh_api(repo, f"workflows/{workflow_file}/runs?status=completed&per_page={count}")
    if data.get("workflow_missing"):
        return []
    return data.get("workflow_runs", [])[:count]


def fetch_jobs(repo: str, run_id: int) -> list:
    data = gh_api(repo, f"runs/{run_id}/jobs?per_page=100")
    return data.get("jobs", [])


def duration_seconds(started_at: str, completed_at: str) -> int:
    if not started_at or not completed_at:
        return 0
    start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    end = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))
    return max(0, int((end - start).total_seconds()))


def process_run(repo: str, workflow_name: str, run: dict) -> dict:
    jobs = []
    passed = 0
    failed = 0

    for job in fetch_jobs(repo, run["id"]):
        parsed = parse_job_name(job.get("name", ""), workflow_name)
        if parsed is None:
            continue
        conclusion = job.get("conclusion") or "unknown"
        if conclusion == "success":
            passed += 1
        elif conclusion in ("failure", "timed_out", "cancelled"):
            failed += 1
        jobs.append(
            {
                **parsed,
                "name": job.get("name", ""),
                "conclusion": conclusion,
                "html_url": job.get("html_url", ""),
                "duration_seconds": duration_seconds(job.get("started_at", ""), job.get("completed_at", "")),
            }
        )

    return {
        "id": run["id"],
        "run_number": run.get("run_number", 0),
        "conclusion": run.get("conclusion") or "unknown",
        "html_url": run.get("html_url", ""),
        "head_branch": run.get("head_branch", ""),
        "head_sha": (run.get("head_sha") or "")[:8],
        "event": run.get("event", ""),
        "created_at": run.get("created_at", ""),
        "duration_seconds": duration_seconds(run.get("run_started_at", run.get("created_at", "")), run.get("updated_at", "")),
        "total_jobs": len(jobs),
        "passed_jobs": passed,
        "failed_jobs": failed,
        "skipped_jobs": len(jobs) - passed - failed,
        "jobs": jobs,
    }


def load_existing(path: Path) -> list:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return []


def merge_runs(existing: list, new_runs: list) -> list:
    by_id = {run["id"]: run for run in existing}
    for run in new_runs:
        by_id[run["id"]] = run
    merged = list(by_id.values())
    merged.sort(key=lambda run: run.get("created_at", ""), reverse=True)
    return merged[:MAX_HISTORY]


def main() -> None:
    argp = argparse.ArgumentParser()
    argp.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "openhwgroup/cv32e20-dv"))
    argp.add_argument("--data-dir", default="data")
    argp.add_argument("--fetch-count", type=int, default=10)
    args = argp.parse_args()

    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    for key, workflow_file in WORKFLOWS.items():
        path = data_dir / f"runs_{key}.json"
        existing = load_existing(path)
        existing_ids = {run["id"] for run in existing}
        new_runs = []
        for run in fetch_runs(args.repo, workflow_file, args.fetch_count):
            if run["id"] not in existing_ids:
                new_runs.append(process_run(args.repo, key, run))
        path.write_text(json.dumps(merge_runs(existing, new_runs), indent=2))

    (data_dir / "metadata.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "repo": args.repo,
                "workflows": list(WORKFLOWS.keys()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
