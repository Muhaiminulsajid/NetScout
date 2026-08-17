"""Playwright-based page fetcher + hyperlink extractor."""





from urllib.parse import urldefrag, urljoin, urlparse

from playwright.sync_api import sync_playwright

from ..config import settings

BLOCKED_SCHEMES = {"mailto", "tel", "javascript", "data", "about", "file"}


def _normalize(base: str, href: str) -> str | None:
    try:
        absolute = urljoin(base, href.strip())
        absolute, _ = urldefrag(absolute)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            return None
        return absolute
    except ValueError:
        return None


def fetch_page(url: str) -> dict: 
    """Load url in headless Chromium; return title, status and outgoing links. 
    Returns {'url', 'title', 'http_status', 'broken', 'links': [str, ...], 'error'} """

    result: dict = {"url": url, "title": None, "http_status": None,
                    "broken": False, "links": [], "error": None}
    timeout_ms = settings.crawler_timeout_seconds * 1000
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
            try:
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (compatible; NetScoutBot/1.0)",
                    viewport={"width": 1280, "height": 800},
                )
                page = context.new_page()
                response = page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
                result["http_status"] = response.status if response else None
                result["broken"] = bool(response and response.status >= 400)
                result["title"] = page.title() or None

                hrefs = page.eval_on_selector_all(
                    "a[href]", "els => els.map(e => e.getAttribute('href'))"
                )
                seen: set[str] = set()
                for href in hrefs:
                    if not href:
                        continue
                    link = _normalize(url, href)
                    if not link or link == url or link in seen:
                        continue
                    seen.add(link)
                    result["links"].append(link)
                    if len(result["links"]) >= settings.max_links_per_page:
                        break
            finally:
                browser.close()
    except Exception as exc:  # noqa: BLE001 - navigation failures are data, not bugs
        result["error"] = str(exc)
        result["broken"] = True
    return result
 
