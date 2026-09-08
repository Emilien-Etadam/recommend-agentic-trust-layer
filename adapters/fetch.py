"""Page fetcher — turns a search result URL into readable text for the local web lanes.

Exa returns page text with every result; SearXNG returns a two-line snippet. This closes
the gap: a plain GET first (fast, works for most sites), and when the site answers with a
bot wall (403 / 503 / Cloudflare challenge) the request is replayed through Byparr, a
FlareSolverr-compatible headless browser (BYPARR_URL in .env, e.g. http://byparr:8191).

Byparr is slow (seconds per page, real browser) so it is only the fallback, capped by
FETCH_BYPARR_MAX pages per process-second-ish budget (default 4 concurrent). Text
extraction is pure stdlib: strip script/style/nav, keep block text, collapse whitespace.
"""
import html
import os
import re
import threading
from html.parser import HTMLParser

import requests

from .base import session

_cache, _cache_lock = {}, threading.Lock()
_byparr_sem = threading.BoundedSemaphore(int(os.environ.get("FETCH_BYPARR_MAX", "4")))

_BROWSER_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
               "Chrome/126.0 Safari/537.36")
_SKIP_EXT = (".pdf", ".zip", ".jpg", ".jpeg", ".png", ".gif", ".mp4", ".mp3", ".xls", ".xlsx",
             ".doc", ".docx", ".ppt", ".pptx")
_CHALLENGE_MARKERS = ("cf-browser-verification", "challenge-platform", "Just a moment",
                      "Attention Required! | Cloudflare", "_cf_chl_opt", "Verify you are human",
                      "Access denied", "captcha")


def byparr_url():
    return os.environ.get("BYPARR_URL", "").strip().rstrip("/")


class _Text(HTMLParser):
    _DROP = {"script", "style", "noscript", "nav", "header", "footer", "aside", "svg",
             "form", "button", "iframe", "template"}
    _BLOCK = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "td", "th",
              "section", "article", "blockquote", "pre", "dd", "dt"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts, self._skip, self.title, self._in_title = [], 0, "", False

    def handle_starttag(self, tag, attrs):
        if tag in self._DROP:
            self._skip += 1
        elif tag == "title":
            self._in_title = True
        elif tag in self._BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self._DROP and self._skip:
            self._skip -= 1
        elif tag == "title":
            self._in_title = False
        elif tag in self._BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip:
            self.parts.append(data)


def html_to_text(raw: str) -> tuple:
    """(title, text). Paragraph breaks preserved as single newlines."""
    p = _Text()
    try:
        p.feed(raw)
        p.close()
    except Exception:
        pass
    txt = html.unescape("".join(p.parts))
    txt = re.sub(r"[ \t\r\f\v]+", " ", txt)
    txt = re.sub(r"\n\s*\n+", "\n", txt)
    # drop nav-ish crumbs: lines under ~40 chars are menus, dates, cookie buttons
    lines = [l.strip() for l in txt.split("\n")]
    lines = [l for l in lines if len(l) >= 40 or l.endswith((".", "?", "!"))]
    return p.title.strip(), "\n".join(lines).strip()


def _looks_blocked(status: int, body: str) -> bool:
    if status in (401, 403, 429, 503):
        return True
    head = body[:4000]
    return any(m in head for m in _CHALLENGE_MARKERS) and len(body) < 20000


def _get_plain(url: str, timeout: float):
    r = session().get(url, headers={"User-Agent": _BROWSER_UA,
                                    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                                    "Accept-Language": "en,fr;q=0.8"},
                      timeout=timeout, allow_redirects=True)
    ctype = (r.headers.get("Content-Type") or "").lower()
    if "html" not in ctype and "text/plain" not in ctype and "xml" not in ctype:
        return r.status_code, ""            # binary / pdf — nothing to read
    return r.status_code, r.text


def _get_byparr(url: str, timeout: float) -> str:
    base = byparr_url()
    if not base:
        return ""
    with _byparr_sem:
        r = requests.post(base + "/v1", json={"cmd": "request.get", "url": url,
                                             "maxTimeout": int(timeout * 1000)},
                          timeout=timeout + 15)
    r.raise_for_status()
    d = r.json()
    if d.get("status") != "ok":
        return ""
    sol = d.get("solution") or {}
    if int(sol.get("status") or 200) >= 400:
        return ""
    return sol.get("response") or ""


def page_text(url: str, *, max_chars: int = 3000, timeout: float = 12.0) -> dict:
    """{title, text, via} — via ∈ {'plain','byparr','none'}. Never raises: an unreadable
    page is an empty text, and the caller falls back to the search snippet."""
    if not url or url.lower().split("?")[0].endswith(_SKIP_EXT):
        return {"title": "", "text": "", "via": "none"}
    with _cache_lock:
        hit = _cache.get(url)
    if hit is not None:
        return hit
    title, text, via = "", "", "none"
    body, status = "", 0
    try:
        status, body = _get_plain(url, timeout)
    except requests.exceptions.RequestException:
        status, body = 0, ""
    if body and not _looks_blocked(status, body):
        title, text = html_to_text(body)
        via = "plain"
    elif byparr_url():
        try:
            body = _get_byparr(url, timeout=float(os.environ.get("BYPARR_TIMEOUT", "45")))
            if body:
                title, text = html_to_text(body)
                via = "byparr"
        except (requests.exceptions.RequestException, ValueError):
            pass
    out = {"title": title[:200], "text": text[:max_chars], "via": via}
    with _cache_lock:
        if len(_cache) > 2000:
            _cache.clear()
        _cache[url] = out
    return out


def excerpt_for(text: str, query: str, max_chars: int = 900) -> str:
    """The window of `text` densest in query terms — what Exa's `highlights` would return.
    Falls back to the opening of the text when nothing matches."""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    terms = {t.lower() for t in re.findall(r"\w{4,}", query or "")}
    if not terms:
        return text[:max_chars]
    paras = [p for p in text.split("\n") if p.strip()]
    best, best_score = 0, -1
    for i, p in enumerate(paras):
        words = set(re.findall(r"\w{4,}", p.lower()))
        score = len(words & terms)
        if score > best_score:
            best, best_score = i, score
    if best_score <= 0:
        return text[:max_chars]
    out, j = "", best
    while j < len(paras) and len(out) + len(paras[j]) + 1 <= max_chars:
        out += paras[j] + "\n"
        j += 1
    return (out or paras[best][:max_chars]).strip()
