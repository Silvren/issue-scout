import urllib.parse

import pytest

from issue_scout.github import GitHubApiError, GitHubClient


def api_issue(number=1, *, pull_request=False):
    payload = {
        "repository_url": "https://api.github.com/repos/octo/demo",
        "number": number,
        "title": f"Issue {number}",
        "html_url": f"https://github.com/octo/demo/issues/{number}",
        "body": "Description",
        "labels": [],
        "assignees": [],
        "comments": 0,
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-07-01T00:00:00Z",
    }
    if pull_request:
        payload["pull_request"] = {"url": "https://api.github.com/pulls/1"}
    return payload


def test_search_filters_pull_requests_and_sends_token():
    calls = []

    def transport(url, headers):
        calls.append((url, headers))
        return {"items": [api_issue(1), api_issue(2, pull_request=True)]}

    issues = GitHubClient("secret", transport=transport).search_issues("is:issue", limit=10)

    assert [issue.number for issue in issues] == [1]
    assert calls[0][1]["Authorization"] == "Bearer secret"
    assert urllib.parse.parse_qs(urllib.parse.urlparse(calls[0][0]).query)["q"] == ["is:issue"]


def test_search_rejects_malformed_response():
    client = GitHubClient(transport=lambda _url, _headers: {"unexpected": []})
    with pytest.raises(GitHubApiError, match="items"):
        client.search_issues("is:issue")


@pytest.mark.parametrize("limit", [1, 100, 101, 150, 250])
def test_search_pagination_returns_consecutive_issues(limit):
    items = [api_issue(number) for number in range(1, 301)]
    calls = []

    def transport(url, _headers):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        page = int(params["page"][0])
        per_page = int(params["per_page"][0])
        calls.append((page, per_page))
        start = (page - 1) * per_page
        return {"items": items[start : start + per_page]}

    issues = GitHubClient(transport=transport).search_issues("is:issue", limit=limit)

    assert [issue.number for issue in issues] == list(range(1, limit + 1))
    per_page = min(100, limit)
    assert calls == [(page, per_page) for page in range(1, (limit - 1) // per_page + 2)]


def test_linked_open_pull_request(candidate_factory):
    client = GitHubClient(
        transport=lambda _url, _headers: [
            {
                "event": "cross-referenced",
                "source": {"issue": {"state": "open", "pull_request": {}}},
            }
        ]
    )
    assert client.has_linked_open_pull_request(candidate_factory()) is True


def test_closed_or_non_pr_cross_reference_is_ignored(candidate_factory):
    client = GitHubClient(
        transport=lambda _url, _headers: [
            {"source": {"issue": {"state": "closed", "pull_request": {}}}},
            {"source": {"issue": {"state": "open"}}},
        ]
    )
    assert client.has_linked_open_pull_request(candidate_factory()) is False
