# CVE2 ACT4 CI Template

This directory contains the workflow that should be copied into the `cve2`
repository to implement Mike's proposed CI rule:

- any pull request to any branch of `cve2`
- clone `cv32e20-dv`
- point `CV_CORE_REPO`, `CV_CORE_BRANCH`, and `CV_CORE_HASH` at the PR head
- run `make gen-certify` in `cv32e20-dv/sim/core`

Copy target:

```text
cve2/.github/workflows/cve2-act-ci.yml
```

The workflow expects these shared helper paths in `cve2` as well:

```text
cve2/.github/actions/setup-cv32e20-tools/action.yml
cve2/scripts/*.sh
```
