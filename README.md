# Issue Scout

[![Tests](https://github.com/Silvren/issue-scout/actions/workflows/tests.yml/badge.svg)](https://github.com/Silvren/issue-scout/actions/workflows/tests.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Issue Scout is a small, dependency-free Python CLI that finds and ranks approachable GitHub issues. Its scoring is deliberately transparent: every candidate includes the reasons it gained or lost points.

## Why

Labels such as `good first issue` are useful, but they do not tell the whole story. An issue may already be assigned, have an open pull request, contain little context, or have a long discussion. Issue Scout combines these signals into a reviewable shortlist—it does **not** automatically claim issues or submit code.

## Install

```bash
git clone https://github.com/Silvren/issue-scout.git
cd issue-scout
python -m pip install -e .
```

For authenticated requests and a higher GitHub API rate limit, set a token:

```bash
# PowerShell
$env:GH_TOKEN = "your-token"

# bash/zsh
export GH_TOKEN="your-token"
```

The token is read from the environment and is never printed.

## Examples

Find unassigned Python issues with two required labels:

```bash
issue-scout \
  --language Python \
  --label "good first issue" \
  --label "help wanted" \
  --min-score 40
```

Search within one repository and export JSON:

```bash
issue-scout --repo pallets/click --limit 10 --format json
```

Add raw GitHub search qualifiers:

```bash
issue-scout --query "comments:<5 updated:>2026-01-01" --format csv
```

By default, Issue Scout checks issue timelines and removes candidates with a linked open pull request. Use `--skip-pr-check` to avoid the extra API calls, or `--include-linked-prs` to keep them with a score penalty.

To stay within GitHub API limits, it checks timelines for only the 20 highest-scoring
candidates by default. Change that bound with `--pr-check-limit`, or use
`--show-filtered` to see candidates removed by the score and linked-PR filters.

## Scoring

| Signal | Points |
|---|---:|
| `good first issue` | +30 |
| `help wanted` | +20 |
| Unassigned | +15 |
| Updated within 7 days | +15 |
| Detailed description | +8 |
| `bug` | +8 |
| `documentation` | +6 |
| Assigned | -25 |
| Discussion activity | up to -15 |
| Linked open pull request | -50 |

The scoring function is deterministic and tested, so users can inspect or change the policy without relying on a black box.

## Development

```bash
python -m pip install -e ".[dev]"
pytest
ruff check .
ruff format --check .
```

## Responsible contribution workflow

Issue Scout helps with discovery only. Before working on a result:

1. Read the repository's contribution guide.
2. Confirm the issue is still relevant and unclaimed.
3. Discuss substantial design changes with maintainers.
4. Make focused changes with tests.
5. Respond to review feedback and maintain the PR.

## License

[MIT](LICENSE)
