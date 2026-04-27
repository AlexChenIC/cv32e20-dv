#!/usr/bin/env python3
# Copyright 2026 OpenHW Group
# SPDX-License-Identifier: Apache-2.0
"""Parse CV32E20 CI job names into dashboard fields."""

import re
from typing import Optional


SKIP_JOBS = {
    "Build Dashboard",
    "Deploy to Pages",
    "Persist Dashboard Data",
}


def parse_job_name(job_name: str, workflow_name: str) -> Optional[dict]:
    name = job_name.strip()
    if name in SKIP_JOBS:
        return None

    m = re.match(r"^(Core|UVM)\s+(.+?)\s+/\s+(.+)$", name)
    if m:
        return {
            "bench": m.group(1).lower(),
            "testcase": m.group(2).strip(),
            "simulator": m.group(3).strip(),
        }

    m = re.match(r"^ACT4\s+(.+?)\s+/\s+(.+)$", name)
    if m:
        return {
            "bench": "act4",
            "testcase": m.group(1).strip(),
            "simulator": m.group(2).strip(),
        }

    return None
