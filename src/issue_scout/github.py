from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from typing import Any

from issue_scout.models import IssueCandidate


class GitHubApiError(RuntimeError):
    """Raised when GitHub returns an unsuccessful or malformed response."""


Transport = Callable[[str, dict[str, str]], Any]


class GitHubClient:
    def __init__(self, token: str | None = None, *, transport: Transport | None = None):
        self._token = token
        self._transport = transport or self._request_json

    def search_issues(self, query: str, *, limit: int = 20) -> list[IssueCandidate]:
        """Search GitHub issues, following pagination until *limit* is reached."""
        if limit < 1:
            return []
        results: list[IssueCandidate] = []
        page = 1
        per_page = min(100, limit)
        while len(results) < limit:
            params = urllib.parse.urlencode(
                {"q": query, "sort": "updated", "order": "desc", "per_page": per_page, "page": page}
            )
            payload = self._transport(
                f"https://api.github.com/search/issues?{params}", self._headers()
            )
            items = payload.get("items") if isinstance(payload, dict) else None
            if not isinstance(items, list):
                raise GitHubApiError("GitHub search response has no 'items' list")
            issue_items = [item for item in items if "pull_request" not in item]
            results.extend(IssueCandidate.from_api(item) for item in issue_items)
            if len(items) < per_page or not items:
                break
            page += 1
        return results[:limit]

    def has_linked_open_pull_request(self, issue: IssueCandidate) -> bool:
        """Check issue timeline cross-references for an open pull request."""
        url = f"https://api.github.com/repos/{issue.repository}/issues/{issue.number}/timeline?per_page=100"
        events = self._transport(url, self._headers())
        if not isinstance(events, list):
            raise GitHubApiError("GitHub timeline response is not a list")
        for event in events:
            source = event.get("source", {}).get("issue", {}) if isinstance(event, dict) else {}
            if source.get("state") == "open" and "pull_request" in source:
                return True
        return False

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "issue-scout/0.1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    @staticmethod
    def _request_json(url: str, headers: dict[str, str]) -> Any:
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise GitHubApiError(f"GitHub API returned HTTP {error.code}: {detail}") from error
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise GitHubApiError(f"GitHub API request failed: {error}") from error
