from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator
import httpx

class RateLimited(RuntimeError): pass

@dataclass
class _Token:
    value: str
    rest_remaining: int = 0
    graphql_remaining: int = 0
    search_remaining: int = 0
    reset: float = 0.0

@dataclass
class GitHubClient:
    tokens: list[str]
    client: httpx.Client = field(default_factory=lambda: httpx.Client(base_url="https://api.github.com", timeout=60))
    _pool: list[_Token] = field(init=False)
    _last_search: float = 0.0
    _secondary_attempts: int = 0
    def __post_init__(self) -> None:
        if not self.tokens:
            raise ValueError("Cần ít nhất một GitHub token")
        self._pool = [
            _Token(value=token, rest_remaining=5_000, graphql_remaining=5_000, search_remaining=30)
            for token in self.tokens
        ]
    def __enter__(self): return self
    def __exit__(self, *exc): self.close()
    def close(self): self.client.close()
    def _token(self, budget: str) -> _Token:
        return max(self._pool, key=lambda t: getattr(t, f"{budget}_remaining"))
    def _request(self, method: str, path: str, *, budget: str, **kwargs) -> httpx.Response:
        if budget == "search":
            delay = 3 - (time.monotonic() - self._last_search)
            if delay > 0: time.sleep(delay)
        token = self._token(budget)
        response = self.client.request(method, path, headers={"Authorization": f"Bearer {token.value}", "Accept": "application/vnd.github+json"}, **kwargs)
        if budget == "search": self._last_search = time.monotonic()
        remaining = response.headers.get("x-ratelimit-remaining")
        if remaining is not None: setattr(token, f"{budget}_remaining", int(remaining))
        reset = response.headers.get("x-ratelimit-reset")
        if reset: token.reset = float(reset)
        if response.status_code in (502, 503, 504):
            self._secondary_attempts += 1
            if self._secondary_attempts <= 4:
                time.sleep(10 * 2 ** (self._secondary_attempts - 1))
                return self._request(method, path, budget=budget, **kwargs)
        if response.status_code in (403, 429):
            retry = response.headers.get("retry-after")
            if retry: time.sleep(float(retry)); return self._request(method, path, budget=budget, **kwargs)
            if remaining == "0":
                time.sleep(max(0, token.reset - time.time()) + 1); return self._request(method, path, budget=budget, **kwargs)
            self._secondary_attempts += 1
            if self._secondary_attempts <= 4:
                time.sleep(90 * 2 ** (self._secondary_attempts - 1)); return self._request(method, path, budget=budget, **kwargs)
            raise RateLimited("GitHub secondary rate limit")
        self._secondary_attempts = 0; response.raise_for_status(); return response
    def search_count(self, q: str) -> int:
        data = self._request("GET", "/search/issues", budget="search", params={"q": q, "per_page": 1}).json()
        if data.get("incomplete_results"): raise RateLimited("GitHub search returned incomplete results")
        return int(data["total_count"])
    def graphql(self, query: str, vars: dict[str, Any]) -> dict[str, Any]:
        data = self._request("POST", "/graphql", budget="graphql", json={"query": query, "variables": vars}).json()
        if data.get("errors"): raise RuntimeError(data["errors"])
        return data["data"]
    def rest(self, path: str, params: dict[str, Any] | None = None) -> Any:
        return self._request("GET", path, budget="rest", params=params).json()
    def rest_paged(self, path: str, params: dict[str, Any] | None = None) -> Iterator[Any]:
        params = dict(params or {}); params.setdefault("per_page", 100); page = 1
        while True:
            data = self.rest(path, {**params, "page": page})
            if not data: return
            yield from data
            if len(data) < params["per_page"]: return
            page += 1
