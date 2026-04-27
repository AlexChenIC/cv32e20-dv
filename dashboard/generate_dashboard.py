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
MATRIX_TARGETS_ORDER = [
    "core / hello-world",
    "uvm / hello-world",
    "act4 / gen-certify",
]
MATRIX_SIMULATORS_ORDER = ["verilator", "vsim", "dsim"]
TREND_COUNT = 20


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


def display_field(value: str) -> str:
    if not value:
        return "N/A"
    if "${{" in value:
        return "matrix"
    return value


def is_valid_matrix_job(job: dict) -> bool:
    bench = job.get("bench", "")
    testcase = job.get("testcase", "")
    simulator = job.get("simulator", "")
    if not bench or not testcase or not simulator:
        return False
    return "${{" not in bench and "${{" not in testcase and "${{" not in simulator


def enrich(run: dict) -> dict:
    run["duration_display"] = format_duration(run.get("duration_seconds", 0))
    run["created_at_display"] = format_datetime(run.get("created_at", ""))
    for job in run.get("jobs", []):
        job["duration_display"] = format_duration(job.get("duration_seconds", 0))
        job["bench_display"] = display_field(job.get("bench", ""))
        job["testcase_display"] = display_field(job.get("testcase", ""))
        job["simulator_display"] = display_field(job.get("simulator", ""))
    return run


def ordered(items: set, preferred: list) -> list:
    result = [item for item in preferred if item in items]
    extras = sorted(items - set(preferred))
    return result + extras


def build_matrix(workflows: list) -> tuple[dict, list, list]:
    matrix = {}
    all_targets = set()
    all_simulators = set()

    for workflow in workflows:
        runs = workflow["runs"]
        if not runs:
            continue

        latest = next(
            (run for run in runs if any(is_valid_matrix_job(job) for job in run.get("jobs", []))),
            None,
        )
        if latest is None:
            continue

        for job in latest.get("jobs", []):
            if not is_valid_matrix_job(job):
                continue
            target = f"{job.get('bench', '').lower()} / {job.get('testcase', '')}"
            simulator = job.get("simulator", "").lower()
            all_targets.add(target)
            all_simulators.add(simulator)
            matrix.setdefault(target, {}).setdefault(simulator, {})[workflow["key"]] = {
                "conclusion": job.get("conclusion", "unknown"),
                "duration_display": job.get("duration_display", "N/A"),
                "html_url": job.get("html_url", ""),
                "name": job.get("name", ""),
            }

    return (
        matrix,
        ordered(all_targets, MATRIX_TARGETS_ORDER),
        ordered(all_simulators, MATRIX_SIMULATORS_ORDER),
    )


def build_latest_jobs(workflows: list) -> list:
    latest_jobs = []
    for workflow in workflows:
        runs = workflow["runs"]
        if not runs:
            continue
        for job in runs[0].get("jobs", []):
            latest_jobs.append({**job, "workflow": workflow["display_name"]})

    order = ["Core hello-world / verilator", "UVM hello-world / vsim", "UVM hello-world / dsim", "ACT4 gen-certify / verilator"]
    latest_jobs.sort(key=lambda job: order.index(job["name"]) if job["name"] in order else len(order))
    return latest_jobs


def build_chart_data(workflows: list) -> dict:
    chart_data = {}
    for workflow in workflows:
        trend_runs = list(reversed(workflow["runs"][:TREND_COUNT]))
        labels = []
        pass_rates = []
        durations = []
        failed_jobs = []
        for run in trend_runs:
            labels.append(str(run.get("run_number", "")))
            total = run.get("total_jobs", 0)
            passed = run.get("passed_jobs", 0)
            pass_rates.append(round(passed / total * 100, 1) if total > 0 else 0)
            durations.append(round(run.get("duration_seconds", 0) / 60, 1))
            failed_jobs.append(run.get("failed_jobs", 0))
        chart_data[workflow["key"]] = {
            "labels": labels,
            "pass_rates": pass_rates,
            "durations": durations,
            "failed_jobs": failed_jobs,
        }
    return chart_data


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
            "skipped_jobs": 0,
            "total_jobs": 0,
            "duration_display": "N/A",
            "run_number": 0,
            "html_url": "#",
        }
        workflows.append({**wf, "runs": runs, "latest": latest})

    matrix_data, matrix_targets, matrix_simulators = build_matrix(workflows)
    latest_jobs = build_latest_jobs(workflows)
    chart_data = build_chart_data(workflows)
    default_matrix_wf = next((wf["key"] for wf in workflows if wf["runs"]), WORKFLOW_INFO[0]["key"])

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")), autoescape=True)
    html = env.get_template("index.html").render(
        repo=args.repo,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        year=datetime.now(timezone.utc).year,
        workflows=workflows,
        latest_jobs=latest_jobs,
        matrix_data=matrix_data,
        matrix_data_json=json.dumps(matrix_data),
        matrix_targets=matrix_targets,
        matrix_targets_json=json.dumps(matrix_targets),
        matrix_simulators=matrix_simulators,
        matrix_simulators_json=json.dumps(matrix_simulators),
        default_matrix_wf=default_matrix_wf,
        chart_data_json=json.dumps(chart_data),
        trend_count=TREND_COUNT,
    )
    (output_dir / "index.html").write_text(html)


if __name__ == "__main__":
    main()
