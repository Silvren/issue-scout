from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from issue_scout.github import GitHubApiError, GitHubClient, GitHubRateLimitError
from issue_scout.models import IssueCandidate
from issue_scout.output import RankedIssue, render
from issue_scout.query import build_query
from issue_scout.scoring import score_issue


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="issue-scout",
        description="Find and rank approachable open GitHub issues.",
    )
    parser.add_argument(
        "--language", default="Python", help="GitHub language filter (default: Python)"
    )
    parser.add_argument("--label", action="append", default=[], help="Required label; repeatable")
    parser.add_argument("--repo", help="Limit results to an owner/name repository")
    parser.add_argument("--query", help="Additional raw GitHub search qualifiers")
    parser.add_argument("--include-assigned", action="store_true", help="Include assigned issues")
    parser.add_argument(
        "--include-linked-prs", action="store_true", help="Keep issues with linked open PRs"
    )
    parser.add_argument(
        "--skip-pr-check", action="store_true", help="Skip timeline checks for linked PRs"
    )
    parser.add_argument(
        "--pr-check-limit",
        type=_positive_int,
        default=20,
        help="Maximum candidate timelines to check for linked PRs (default: 20)",
    )
    parser.add_argument("--min-score", type=int, default=0, help="Minimum candidate score")
    parser.add_argument("--limit", type=_positive_int, default=20, help="Maximum search results")
    parser.add_argument("--format", choices=["table", "json", "csv"], default="table")
    parser.add_argument(
        "--show-filtered",
        action="store_true",
        help="Include candidates excluded by score or linked pull request filters",
    )
    parser.add_argument(
        "--token-env",
        default="GH_TOKEN",
        help="Environment variable containing a GitHub token (default: GH_TOKEN)",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        query = build_query(
            language=args.language,
            labels=tuple(args.label),
            repository=args.repo,
            include_assigned=args.include_assigned,
            extra=args.query,
        )
        client = GitHubClient(token=os.environ.get(args.token_env))
        candidates = client.search_issues(query, limit=args.limit)
        if not args.skip_pr_check:
            candidates = _check_linked_pull_requests(client, candidates, args.pr_check_limit)

        ranked = [RankedIssue(issue=issue, ranking=score_issue(issue)) for issue in candidates]
        ranked = [_mark_filtered(item, args.min_score, args.include_linked_prs) for item in ranked]
        ranked.sort(key=lambda item: (-item.ranking.score, -item.issue.updated_at.timestamp()))
        render(ranked, args.format, show_filtered=args.show_filtered)
        return 0
    except (GitHubApiError, ValueError) as error:
        print(f"issue-scout: error: {error}", file=sys.stderr)
        return 2


def main() -> None:
    raise SystemExit(run())


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def _check_linked_pull_requests(
    client: GitHubClient, candidates: list[IssueCandidate], check_limit: int
) -> list[IssueCandidate]:
    ordered = sorted(candidates, key=lambda issue: -score_issue(issue).score)
    checked = []
    for index, issue in enumerate(ordered):
        if index >= check_limit:
            checked.append(issue)
            continue
        try:
            checked.append(issue.with_linked_pr(client.has_linked_open_pull_request(issue)))
        except GitHubRateLimitError:
            print(
                "issue-scout: warning: GitHub API rate limit exceeded; "
                "remaining linked PR checks were skipped",
                file=sys.stderr,
            )
            checked.extend(ordered[index:])
            break
    return checked


def _mark_filtered(
    item: RankedIssue, min_score: int, include_linked_prs: bool
) -> RankedIssue:
    reasons = []
    if item.ranking.score < min_score:
        reasons.append(f"score below --min-score ({min_score})")
    if item.issue.linked_open_pull_request and not include_linked_prs:
        reasons.append("linked open pull request")
    return RankedIssue(item.issue, item.ranking, included=not reasons, filter_reasons=tuple(reasons))


if __name__ == "__main__":
    main()
