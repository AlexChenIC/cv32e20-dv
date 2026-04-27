#!/usr/bin/env python3
# Copyright 2026 OpenHW Group
# SPDX-License-Identifier: Apache-2.0
"""Render a static dashboard for CV32E20 CI data."""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


WORKFLOW_INFO = [
    {"key": "cv32e20_dv", "display_name": "CV32E20-DV PR CI", "file": "runs_cv32e20_dv.json"},
    {"key": "cve2_act", "display_name": "CVE2 ACT4 CI", "file": "runs_cve2_act.json"},
]


def format_duration(seconds: int) -> str:
    if seconds <= 0:
        return "N/A"
    minutes, secs = divmod(seconds, 60)
    if minutes >= 60:
        hours, minutes = divmod(minutes, 60)
        return f"{hours}h {minutes}m"
    return f"{minutes}m {secs}s"


def format_datetime(value: str) -> str:
    if not value:
        return "N/A"
    return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")


def load_runs(data_dir: Path, file_name: str) -> list:
    path = data_dir / file_name
    if not path.exists():
        return []
    return json.loads(path.read_text())


def enrich(run: dict) -> dict:
    run["duration_display"] = format_duration(run.get("duration_seconds", 0))
    run["created_at_display"] = format_datetime(run.get("created_at", ""))
    for job in run.get("jobs", []):
        job["duration_display"] = format_duration(job.get("duration_seconds", 0))
    return run


def build_matrix(workflows: list) -> tuple[list, list]:
    latest_jobs = []
    for workflow in workflows:
        runs = workflow["runs"]
        if not runs:
            continue
        for job in runs[0].get("jobs", []):
            latest_jobs.append({**job, "workflow": workflow["display_name"]})

    order = ["Core hello-world / verilator", "UVM hello-world / vsim", "UVM hello-world / dsim", "ACT4 gen-certify / verilator"]
    latest_jobs.sort(key=lambda job: order.index(job["name"]) if job["name"] in order else len(order))
    return latest_jobs, order


def main() -> None:
    argp = argparse.ArgumentParser()
    argp.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "openhwgroup/cv32e20-dv"))
    argp.add_argument("--data-dir", default="data")
    argp.add_argument("--output-dir", default="site")
    args = argp.parse_args()

    data_dir = Path(args.data_dir)
    workflows = []
    for wf in WORKFLOW_INFO:
        runs = [enrich(run) for run in load_runs(data_dir, wf["file"])]
        latest = runs[0] if runs else {
            "conclusion": "unknown",
            "head_branch": "N/A",
            "head_sha": "N/A",
            "passed_jobs": 0,
            "failed_jobs": 0,
            "total_jobs": 0,
            "duration_display": "N/A",
            "run_number": 0,
            "html_url": "#",
        }
        workflows.append({**wf, "runs": runs, "latest": latest})

    latest_jobs, _ = build_matrix(workflows)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")), autoescape=True)
    html = env.get_template("index.html").render(
        repo=args.repo,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        workflows=workflows,
        latest_jobs=latest_jobs,
    )
    (output_dir / "index.html").write_text(html)


if __name__ == "__main__":
    main()
