"""Google Cloud Vision Web Detection via REST API key."""
import base64

import httpx

from ..config import key_configured, settings

API = "https://vision.googleapis.com/v1/images:annotate"


def vision_web_detection(image_path: str, timeout: float = 25.0) -> list[dict] | None:
    """Return normalized matches or None when the key is missing/unavailable."""
    if not key_configured(settings.google_vision_api_key):
        return None
    with open(image_path, "rb") as fh:
        content = base64.b64encode(fh.read()).decode()
    body = {
        "requests": [{
            "image": {"content": content},
            "features": [{"type": "WEB_DETECTION", "maxResults": 50}],
        }]
    }
    try:
        resp = httpx.post(API, params={"key": settings.google_vision_api_key},
                          json=body, timeout=timeout)
        resp.raise_for_status()
        detection = resp.json()["responses"][0].get("webDetection", {})
        matches: list[dict] = []
        for page in detection.get("pagesWithMatchingImages", []):
            image_url = None
            for key in ("fullMatchingImages", "partialMatchingImages"):
                imgs = page.get(key)
                if imgs:
                    image_url = imgs[0].get("url")
                    break
            matches.append({
                "engine": "google_vision",
                "page_url": page.get("url", ""),
                "image_url": image_url,
                "title": page.get("pageTitle"),
                "published_at": None,  # Vision API does not expose dates
                "raw_score": page.get("score"),
            })
        return [m for m in matches if m["page_url"]]
    except Exception:  # noqa: BLE001
        return None
