"""VirusTotal URL reputation. Requires VIRUSTOTAL_API_KEY; returns None otherwise."""
import base64

import httpx

from ..config import key_configured, settings

API = "https://www.virustotal.com/api/v3/urls"


def vt_url_report(url: str, timeout: float = 10.0) -> dict | None:
    """Return {'malicious': int, 'suspicious': int, 'harmless': int, 'total': int} or None."""
    if not key_configured(settings.virustotal_api_key):
        return None
    url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
    headers = {"x-apikey": settings.virustotal_api_key}
    try:
        resp = httpx.get(f"{API}/{url_id}", headers=headers, timeout=timeout)
        if resp.status_code == 404:
            # Not yet analyzed — submit and report unknown for now.
            httpx.post(API, headers=headers, data={"url": url}, timeout=timeout)
            return None
        resp.raise_for_status()
        stats = resp.json()["data"]["attributes"]["last_analysis_stats"]
        return {
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless": stats.get("harmless", 0),
            "total": sum(stats.values()),
        }
    except Exception:  # noqa: BLE001
        return None
