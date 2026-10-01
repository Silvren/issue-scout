from __future__ import annotations

import csv
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TextIO

from issue_scout.models import IssueCandidate, ScoreBreakdown

ROW_FIELDS = [
    "score",
    "repository",
    "number",
    "title",
    "url",
    "labels",
    "comments",
    "linked_open_pr",
    "reasons",
]


@dataclass(frozen=True)
class RankedIssue:
    issue: IssueCandidate
    ranking: ScoreBreakdown

    def as_row(self) -> dict[str, object]:
        return {
            "score": self.ranking.score,
            "repository": self.issue.repository,
            "number": self.issue.number,
            "title": self.issue.title,
            "url": self.issue.url,
            "labels": ", ".join(self.issue.labels),
            "comments": self.issue.comments,
            "linked_open_pr": self.issue.linked_open_pull_request,
            "reasons": "; ".join(self.ranking.reasons),
        }


def render(
    ranked: Iterable[RankedIssue], format_name: str, *, stream: TextIO | None = None
) -> None:
    stream = stream or sys.stdout
    rows = [item.as_row() for item in ranked]
    if format_name == "json":
        # Keep JSON portable across terminals whose text encoding cannot represent
        # every issue title, such as the default Windows console encoding.
        json.dump(rows, stream, indent=2, ensure_ascii=True)
        stream.write("\n")
    elif format_name == "csv":
        writer = csv.DictWriter(stream, fieldnames=ROW_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    elif format_name == "table":
        _render_table(rows, stream)
    else:
        raise ValueError(f"unsupported output format: {format_name}")


def _render_table(rows: list[dict[str, object]], stream: TextIO) -> None:
    if not rows:
        stream.write("No matching issues found.\n")
        return
    stream.write(f"{'SCORE':>5}  {'ISSUE':<28}  TITLE\n")
    stream.write(f"{'-' * 5}  {'-' * 28}  {'-' * 48}\n")
    for row in rows:
        reference = f"{row['repository']}#{row['number']}"
        title = str(row["title"]).replace("\n", " ")
        if len(title) > 70:
            title = title[:67] + "..."
        stream.write(f"{row['score']:>5}  {reference:<28}  {title}\n")
        stream.write(f"       {row['url']}\n")
