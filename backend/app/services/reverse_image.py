"""Multi-engine reverse image search orchestration."""
from concurrent.futures import ThreadPoolExecutor

from .bing_visual import bing_visual_search
from .google_vision import vision_web_detection


def _similarity(match: dict, rank: int, total: int) -> float:
    """Percentage confidence of visual resemblance.

    Uses the engine's own score when present, otherwise a rank-decayed
    estimate (earlier results from these engines are more similar).
    """
    raw = match.get("raw_score")
    if isinstance(raw, (int, float)) and raw > 0:
        return round(min(float(raw), 1.0) * 100, 1)
    if total <= 1:
        return 85.0
    return round(95.0 - (rank / (total - 1)) * 45.0, 1)


def run_reverse_search(image_path: str) -> dict:
    """Submit to Bing Visual Search + Google Vision simultaneously.

    Returns {'matches': [...], 'engines': {'bing': bool, 'google_vision': bool}}.
    Matches are sorted chronologically (dated first, oldest first) so the
    earliest/original publisher surfaces at the top.
    """
    with ThreadPoolExecutor(max_workers=2) as pool:
        bing_future = pool.submit(bing_visual_search, image_path)
        vision_future = pool.submit(vision_web_detection, image_path)
        bing = bing_future.result()
        vision = vision_future.result()

    engines = {"bing": bing is not None, "google_vision": vision is not None}
    matches: list[dict] = []
    for engine_results in (bing or []), (vision or []):
        total = len(engine_results)
        for rank, match in enumerate(engine_results):
            match["similarity"] = _similarity(match, rank, total)
            matches.append(match)

    # Deduplicate by page_url, keep highest similarity.
    dedup: dict[str, dict] = {}
    for m in matches:
        key = m["page_url"]
        if key not in dedup or m["similarity"] > dedup[key]["similarity"]:
            dedup[key] = m

    ordered = sorted(
        dedup.values(),
        key=lambda m: (m["published_at"] is None, m["published_at"] or "",
                       -m["similarity"]),
    )
    return {"matches": ordered, "engines": engines}
