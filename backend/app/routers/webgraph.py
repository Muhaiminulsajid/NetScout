from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..celery_app import celery_app
from ..config import settings
from ..database import get_db
from ..models import CrawlJob, User
from ..rate_limit import check_rate_limit, consume_quota
from ..schemas import CrawlJobOut, CrawlRequest, ExpandRequest
from ..tasks.webgraph_tasks import crawl_task, expand_task

router = APIRouter()


@router.post("/crawl", response_model=CrawlJobOut, status_code=202)
def start_crawl(
    payload: CrawlRequest,
    user: User = Depends(check_rate_limit),
    db: Session = Depends(get_db),
):
    consume_quota(user.id, "crawl", settings.daily_crawl_quota)
    depth = min(payload.depth, settings.max_crawl_depth)
    job = CrawlJob(user_id=user.id, root_url=payload.url, depth=depth)
    db.add(job)
    db.commit()
    db.refresh(job)
    crawl_task.delay(job.id)
    return job


@router.get("/crawl/{job_id}", response_model=CrawlJobOut)
def get_crawl(job_id: str, user: User = Depends(check_rate_limit),
              db: Session = Depends(get_db)):
    job = db.get(CrawlJob, job_id)
    if not job or job.user_id != user.id:
        raise HTTPException(404, "Job not found")
    return job


@router.post("/expand", status_code=202)
def expand_node(payload: ExpandRequest, user: User = Depends(check_rate_limit)):
    """Lazily expand a single node; returns a Celery task id to poll."""
    consume_quota(user.id, "crawl", settings.daily_crawl_quota)
    task = expand_task.delay(payload.url)
    return {"task_id": task.id}


@router.get("/expand/{task_id}")
def expand_result(task_id: str, user: User = Depends(check_rate_limit)):
    res = AsyncResult(task_id, app=celery_app)
    if res.failed():
        return {"status": "failed", "error": str(res.result)}
    if not res.ready():
        return {"status": res.state.lower(), "node": None}
    return {"status": "done", "node": res.result}
