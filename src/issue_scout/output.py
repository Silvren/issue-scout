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

FILTER_FIELDS = [
    "included",
    "filter_reasons",
]


@dataclass(frozen=True)
class RankedIssue:
    issue: IssueCandidate
    ranking: ScoreBreakdown
    included: bool = True
    filter_reasons: tuple[str, ...] = ()

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
            "included": self.included,
            "filter_reasons": "; ".join(self.filter_reasons),
        }


def render(
    ranked: Iterable[RankedIssue],
    format_name: str,
    *,
    show_filtered: bool = False,
    stream: TextIO | None = None,
) -> None:
    stream = stream or sys.stdout
    items = list(ranked)
    if not show_filtered:
        items = [item for item in items if item.included]
    rows = [item.as_row() for item in items]
    if format_name == "json":
        json.dump(_machine_rows(rows, show_filtered), stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    elif format_name == "csv":
        fields = ROW_FIELDS + FILTER_FIELDS if show_filtered else ROW_FIELDS
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(_machine_rows(rows, show_filtered))
    elif format_name == "table":
        selected = [row for row in rows if row["included"]]
        filtered = [row for row in rows if not row["included"]]
        _render_table(selected, stream)
        if filtered:
            stream.write("\nFILTERED\n")
            for row in filtered:
                reference = f"{row['repository']}#{row['number']}"
                stream.write(f"{row['score']:>5}  {reference:<28}  {row['filter_reasons']}\n")
                stream.write(f"       {row['url']}\n")
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


def _machine_rows(rows: list[dict[str, object]], show_filtered: bool) -> list[dict[str, object]]:
    if show_filtered:
        return rows
    return [{field: row[field] for field in ROW_FIELDS} for row in rows]
