import uuid
from datetime import datetime

from sqlalchemy import (JSON, DateTime, Float, ForeignKey, Integer, String,
                        Text)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _uuid() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    crawls: Mapped[list["CrawlJob"]] = relationship(back_populates="user")
    image_searches: Mapped[list["ImageSearch"]] = relationship(back_populates="user")


class CrawlJob(Base):
    """One WebGraph crawl/expand request and its result tree."""
    __tablename__ = "crawl_jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    root_url: Mapped[str] = mapped_column(Text)
    depth: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|running|done|failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="crawls")


class UrlScore(Base):
    """Cached spam/phishing score per URL (avoid re-hitting external APIs)."""
    __tablename__ = "url_scores"

    url_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    url: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float)         # 0 (safe) .. 100 (malicious)
    verdict: Mapped[str] = mapped_column(String(10))    # green|amber|red
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ImageSearch(Base):
    __tablename__ = "image_searches"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(512))
    stored_path: Mapped[str] = mapped_column(Text)
    phash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    exif: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="image_searches")
    matches: Mapped[list["ImageMatch"]] = relationship(
        back_populates="search", cascade="all, delete-orphan",
        order_by="ImageMatch.published_at",
    )


class ImageMatch(Base):
    __tablename__ = "image_matches"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    search_id: Mapped[str] = mapped_column(ForeignKey("image_searches.id"), index=True)
    engine: Mapped[str] = mapped_column(String(30))         # bing|google_vision|local_cache
    page_url: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    similarity: Mapped[float] = mapped_column(Float, default=0.0)  # 0..100

    search: Mapped["ImageSearch"] = relationship(back_populates="matches")
