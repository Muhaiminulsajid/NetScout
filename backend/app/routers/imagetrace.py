import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import ImageSearch, User
from ..rate_limit import check_rate_limit, consume_quota
from ..schemas import ImageSearchOut
from ..services.exif import extract_exif
from ..services.phash import compute_phash
from ..services.report import build_csv, build_pdf
from ..tasks.imagetrace_tasks import image_search_task

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"}


def _get_owned_search(search_id: str, user: User, db: Session) -> ImageSearch:
    search = db.get(ImageSearch, search_id)
    if not search or search.user_id != user.id:
        raise HTTPException(404, "Search not found")
    return search


@router.post("/search", response_model=ImageSearchOut, status_code=202)
async def create_search(
    file: UploadFile,
    user: User = Depends(check_rate_limit),
    db: Session = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(415, f"Unsupported image type: {file.content_type}")
    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, "Image exceeds 10 MB limit")
    consume_quota(user.id, "image_search", settings.daily_image_search_quota)

    os.makedirs(settings.upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "upload.jpg")[1] or ".jpg"
    stored_path = os.path.join(settings.upload_dir, f"{uuid.uuid4().hex}{ext}")
    with open(stored_path, "wb") as fh:
        fh.write(data)

    try:
        phash = compute_phash(stored_path)
    except Exception as exc:  # noqa: BLE001
        os.remove(stored_path)
        raise HTTPException(422, f"Could not read image: {exc}") from exc

    search = ImageSearch(
        user_id=user.id, filename=file.filename or "upload",
        stored_path=stored_path, phash=phash, exif=extract_exif(stored_path),
    )
    db.add(search)
    db.commit()
    db.refresh(search)
    image_search_task.delay(search.id)
    return search


@router.get("/search/{search_id}", response_model=ImageSearchOut)
def get_search(search_id: str, user: User = Depends(check_rate_limit),
               db: Session = Depends(get_db)):
    return _get_owned_search(search_id, user, db)


@router.get("/search/{search_id}/export.csv")
def export_csv(search_id: str, user: User = Depends(check_rate_limit),
               db: Session = Depends(get_db)):
    search = _get_owned_search(search_id, user, db)
    return Response(
        build_csv(search), media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="netscout_{search_id}.csv"'},
    )


@router.get("/search/{search_id}/export.pdf")
def export_pdf(search_id: str, user: User = Depends(check_rate_limit),
               db: Session = Depends(get_db)):
    search = _get_owned_search(search_id, user, db)
    return Response(
        build_pdf(search), media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="netscout_{search_id}.pdf"'},
    )
