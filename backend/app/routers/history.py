from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import CrawlJob, ImageSearch, User
from ..rate_limit import check_rate_limit, quota_used
from ..schemas import CrawlJobOut, ImageSearchOut, QuotaOut

router = APIRouter()


@router.get("/crawls", response_model=list[CrawlJobOut])
def crawl_history(user: User = Depends(check_rate_limit), db: Session = Depends(get_db),
                  limit: int = 50):
    return (db.query(CrawlJob).filter(CrawlJob.user_id == user.id)
            .order_by(CrawlJob.created_at.desc()).limit(limit).all())


@router.get("/image-searches", response_model=list[ImageSearchOut])
def image_history(user: User = Depends(check_rate_limit), db: Session = Depends(get_db),
                  limit: int = 50):
    return (db.query(ImageSearch).filter(ImageSearch.user_id == user.id)
            .order_by(ImageSearch.created_at.desc()).limit(limit).all())


@router.get("/quota", response_model=QuotaOut)
def quota(user: User = Depends(check_rate_limit)):
    return QuotaOut(
        crawls_used=quota_used(user.id, "crawl"),
        crawls_limit=settings.daily_crawl_quota,
        image_searches_used=quota_used(user.id, "image_search"),
        image_searches_limit=settings.daily_image_search_quota,
    )
