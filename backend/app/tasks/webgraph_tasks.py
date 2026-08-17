"""Celery tasks for the WebGraph module."""
import hashlib

from ..celery_app import celery_app
from ..database import SessionLocal
from ..models import CrawlJob
from ..services.crawler import fetch_page
from ..services.spam_score import get_or_compute_score


def _node_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:12]


def _build_node(db, url: str, depth_remaining: int, visited: set[str]) -> dict:
    page = fetch_page(url)
    score = get_or_compute_score(db, url)
    node = {
        "id": _node_id(url),
        "url": url,
        "title": page["title"],
        "http_status": page["http_status"],
        "broken": page["broken"],
        "error": page["error"],
        "score": score,
        "link_count": len(page["links"]),
        "children": [],
    }
    if depth_remaining <= 0:
        # Leaf: still list child URLs (unscored stubs) so the UI can lazily expand.
        node["stub_links"] = page["links"]
        return node
    for link in page["links"]:
        if link in visited:
            continue
        visited.add(link)
        node["children"].append(_build_node(db, link, depth_remaining - 1, visited))
    return node


@celery_app.task(name="webgraph.crawl")
def crawl_task(job_id: str) -> None:
    db = SessionLocal()
    try:
        job = db.get(CrawlJob, job_id)
        if not job:
            return
        job.status = "running"
        db.commit()
        visited = {job.root_url}
        tree = _build_node(db, job.root_url, job.depth - 1, visited)
        job.result = {"tree": tree, "visited_count": len(visited)}
        job.status = "done"
        db.commit()
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        job = db.get(CrawlJob, job_id)
        if job:
            job.status = "failed"
            job.error = str(exc)
            db.commit()
    finally:
        db.close()


@celery_app.task(name="webgraph.expand")
def expand_task(url: str) -> dict:
    """Synchronous-result task: crawl one page and score it + its links."""
    db = SessionLocal()
    try:
        node = _build_node(db, url, 0, {url})
        # Score stub links cheaply (heuristics run always; APIs if keys present).
        children = []
        for link in node.pop("stub_links", []):
            children.append({
                "id": _node_id(link),
                "url": link,
                "title": None,
                "http_status": None,
                "broken": False,
                "score": get_or_compute_score(db, link),
                "children": [],
            })
        node["children"] = children
        return node
    finally:
        db.close()
