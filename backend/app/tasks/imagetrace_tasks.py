"""Celery tasks for the ImageTrace module."""
from datetime import datetime

from ..celery_app import celery_app
from ..database import SessionLocal
from ..models import ImageMatch, ImageSearch
from ..services.phash import hamming_similarity
from ..services.reverse_image import run_reverse_search

PHASH_CACHE_THRESHOLD = 92.0  # % similarity to reuse a previous search


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


@celery_app.task(name="imagetrace.search")
def image_search_task(search_id: str) -> None:
    db = SessionLocal()
    try:
        search = db.get(ImageSearch, search_id)
        if not search:
            return
        search.status = "running"
        db.commit()

        # 1) Perceptual-hash cache: reuse matches from a near-identical prior search.
        cached = (
            db.query(ImageSearch)
            .filter(ImageSearch.status == "done", ImageSearch.id != search.id)
            .order_by(ImageSearch.created_at.desc())
            .limit(500)
            .all()
        )
        for prior in cached:
            if hamming_similarity(search.phash, prior.phash) >= PHASH_CACHE_THRESHOLD:
                for m in prior.matches:
                    db.add(ImageMatch(
                        search_id=search.id, engine="local_cache",
                        page_url=m.page_url, image_url=m.image_url, title=m.title,
                        published_at=m.published_at, similarity=m.similarity,
                    ))
                search.status = "done"
                db.commit()
                return

        # 2) Multi-engine search.
        result = run_reverse_search(search.stored_path)
        for m in result["matches"]:
            db.add(ImageMatch(
                search_id=search.id,
                engine=m["engine"],
                page_url=m["page_url"],
                image_url=m.get("image_url"),
                title=m.get("title"),
                published_at=_parse_dt(m.get("published_at")),
                similarity=m.get("similarity", 0.0),
            ))
        if not any(result["engines"].values()):
            search.error = (
                "No search engine API keys configured — add "
                "BING_VISUAL_SEARCH_API_KEY and/or GOOGLE_CLOUD_VISION_API_KEY "
                "to .env. Local hashing and EXIF extraction still ran."
            )
        search.status = "done"
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        search = db.get(ImageSearch, search_id)
        if search:
            search.status = "failed"
            search.error = str(exc)
            db.commit()
    finally:
        db.close()
