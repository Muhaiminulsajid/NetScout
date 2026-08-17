"""Google Safe Browsing v4 lookup. Requires API key; returns None otherwise."""
import httpx

from ..config import key_configured, settings

API = "https://safebrowsing.googleapis.com/v4/threatMatches:find"


def gsb_check(url: str, timeout: float = 10.0) -> dict | None:
    """Return {'threats': [types...]} (empty list == clean) or None if unavailable."""
    if not key_configured(settings.google_safe_browsing_api_key):
        return None
    body = {
        "client": {"clientId": "netscout", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": [
                "MALWARE", "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }
    try:
        resp = httpx.post(
            API, params={"key": settings.google_safe_browsing_api_key},
            json=body, timeout=timeout,
        )
        resp.raise_for_status()
        matches = resp.json().get("matches", [])
        return {"threats": sorted({m["threatType"] for m in matches})}
    except Exception:  # noqa: BLE001
        return None
