"""SearXNG adapter — self-hosted meta-search behind the local web lanes.

One call:
  * search(query) → list[RawItem] (title/url/snippet/date) + Google-style "answers"

Config: SEARXNG_URL in .env (e.g. http://192.168.1.20:8080). The instance must expose the
JSON API — in its settings.yml:

    search:
      formats: [html, json]

Without it every request comes back 403 and the lane reports that error.
Optional knobs: SEARXNG_ENGINES (comma list, e.g. "google,bing,duckduckgo"),
SEARXNG_LANGUAGE (e.g. "en" / "fr" / "all").
"""
import os

import requests

from .base import RawItem, session
from .ratelimit import RateLimiter
from .retry import retry

_limiter = RateLimiter(4)          # be polite to the upstream engines SearXNG fans out to


def base_url():
    return os.environ.get("SEARXNG_URL", "").strip().rstrip("/")


def configured():
    return bool(base_url())


@retry(attempts=3, base_delay=1.0)
def search_raw(query: str, *, n: int = 8, engines: str = None, time_range: str = None,
               language: str = None) -> dict:
    """Raw JSON call. Returns {"items": [RawItem], "answers": [str], "infobox": str}."""
    if not configured():
        raise RuntimeError("SEARXNG_URL is not set")
    params = {"q": query, "format": "json", "safesearch": 0}
    eng = engines or os.environ.get("SEARXNG_ENGINES")
    if eng:
        params["engines"] = eng
    lang = language or os.environ.get("SEARXNG_LANGUAGE")
    if lang:
        params["language"] = lang
    if time_range in ("day", "week", "month", "year"):
        params["time_range"] = time_range
    _limiter.acquire()
    r = session().get(base_url() + "/search", params=params, timeout=30)
    if r.status_code == 403:
        raise RuntimeError("SearXNG returned 403 — enable the JSON API "
                           "(settings.yml → search.formats: [html, json])")
    r.raise_for_status()
    try:
        d = r.json()
    except ValueError:
        raise requests.exceptions.HTTPError("SearXNG did not return JSON", response=r)

    items, seen = [], set()
    for x in (d.get("results") or []):
        url = x.get("url") or ""
        if not url or url in seen:
            continue
        seen.add(url)
        items.append(RawItem(url=url, title=(x.get("title") or "").strip(),
                             content=(x.get("content") or "").strip(),
                             postdate=(x.get("publishedDate") or "") or "",
                             author=""))
        if len(items) >= n:
            break

    # SearXNG's "answers" are the engines' own extracted answers (instant answers,
    # calculator, Wikipedia summary…) — the closest thing to Google's answer box.
    answers = []
    for a in (d.get("answers") or []):
        if isinstance(a, dict):
            a = a.get("answer") or a.get("content") or ""
        if isinstance(a, str) and a.strip():
            answers.append(a.strip())
    infobox = ""
    for ib in (d.get("infoboxes") or []):
        txt = (ib.get("content") or "").strip()
        if txt:
            infobox = f"{ib.get('infobox') or ''}: {txt}".strip(": ")
            break
    return {"items": items, "answers": answers, "infobox": infobox}


def search(query: str, *, n: int = 8, **kw) -> list:
    """Semantic-search-shaped call: list[RawItem] only."""
    return search_raw(query, n=n, **kw)["items"]
