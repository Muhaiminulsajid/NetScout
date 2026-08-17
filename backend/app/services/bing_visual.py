"""Bing Visual Search client. Requires BING_VISUAL_SEARCH_API_KEY."""
from datetime import datetime

import httpx

from ..config import key_configured, settings

API = "https://api.bing.microsoft.com/v7.0/images/visualsearch"


def _parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return None


def bing_visual_search(image_path: str, timeout: float = 25.0) -> list[dict] | None:
    """Return normalized matches or None when the key is missing/unavailable.

    Match shape: {'engine','page_url','image_url','title','published_at','raw_score'}
    """
    if not key_configured(settings.bing_visual_search_api_key):
        return None
    headers = {"Ocp-Apim-Subscription-Key": settings.bing_visual_search_api_key}
    try:
        with open(image_path, "rb") as fh:
            files = {"image": ("image", fh)}
            resp = httpx.post(API, headers=headers, files=files, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        matches: list[dict] = []
        for tag in data.get("tags", []):
            for action in tag.get("actions", []):
                if action.get("actionType") not in ("PagesIncluding", "VisualSearch"):
                    continue
                for item in action.get("data", {}).get("value", []):
                    matches.append({
                        "engine": "bing",
                        "page_url": item.get("hostPageUrl") or item.get("webSearchUrl") or "",
                        "image_url": item.get("contentUrl"),
                        "title": item.get("name"),
                        "published_at": _parse_date(item.get("datePublished")),
                        "raw_score": None,
                    })
        return [m for m in matches if m["page_url"]]
    except Exception:  # noqa: BLE001
        return None
