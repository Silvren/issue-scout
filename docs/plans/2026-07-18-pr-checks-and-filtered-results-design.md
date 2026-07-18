# PR checks and filtered results

## Scope

Limit linked-pull-request timeline checks and let users inspect candidates excluded
from the final result. The scoring policy itself does not change.

## PR checks

`--pr-check-limit` accepts a positive integer and defaults to 20. Issue Scout first
scores and orders candidates without linked-PR penalties, then checks timelines for at
most that many leading candidates. `--skip-pr-check` still skips all timeline requests.

If GitHub reports a rate-limit error while checking a timeline, Issue Scout writes a
warning to stderr and keeps the remaining unchecked candidates. Search failures and
other API failures remain errors.

## Filtered candidates

`--show-filtered` retains the normal selected output and additionally includes
candidates excluded by `--min-score` or an open linked pull request. Each excluded
candidate identifies every applicable exclusion reason.

Table output renders selected candidates followed by a separate filtered section.
JSON and CSV output include selection status and exclusion reasons when the flag is
used, preserving their machine-readable form.

## Compatibility

The existing score calculation, default table columns, and output without the new
flag remain unchanged. The default number of timeline requests becomes bounded.
