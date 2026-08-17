from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- WebGraph ---
class CrawlRequest(BaseModel):
    url: str
    depth: int = Field(default=1, ge=1, le=5)


class ExpandRequest(BaseModel):
    url: str


class NodeScore(BaseModel):
    score: float
    verdict: str
    details: dict = {}


class GraphNode(BaseModel):
    id: str
    url: str
    title: str | None = None
    http_status: int | None = None
    broken: bool = False
    score: NodeScore | None = None
    children: list["GraphNode"] = []


class CrawlJobOut(BaseModel):
    id: str
    root_url: str
    depth: int
    status: str
    error: str | None = None
    result: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- ImageTrace ---
class ImageMatchOut(BaseModel):
    id: str
    engine: str
    page_url: str
    image_url: str | None = None
    title: str | None = None
    published_at: datetime | None = None
    similarity: float

    class Config:
        from_attributes = True


class ImageSearchOut(BaseModel):
    id: str
    filename: str
    phash: str
    status: str
    error: str | None = None
    exif: dict | None = None
    created_at: datetime
    matches: list[ImageMatchOut] = []

    class Config:
        from_attributes = True


class QuotaOut(BaseModel):
    crawls_used: int
    crawls_limit: int
    image_searches_used: int
    image_searches_limit: int
