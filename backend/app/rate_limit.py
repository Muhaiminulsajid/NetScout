"""Redis-backed per-minute rate limiting and daily usage quotas."""
from datetime import date

import redis
from fastapi import Depends, HTTPException, status

from .config import settings
from .deps import get_current_user
from .models import User

_pool = redis.ConnectionPool.from_url(settings.redis_url)


def get_redis() -> redis.Redis:
    return redis.Redis(connection_pool=_pool)


def check_rate_limit(user: User = Depends(get_current_user)) -> User:
    """Sliding one-minute request cap for any authenticated endpoint."""
    r = get_redis()
    key = f"rl:{user.id}"
    current = r.incr(key)
    if current == 1:
        r.expire(key, 60)
    if current > settings.rate_limit_per_minute:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                            "Rate limit exceeded, slow down.")
    return user


def _quota_key(user_id: str, kind: str) -> str:
    return f"quota:{kind}:{user_id}:{date.today().isoformat()}"


def quota_used(user_id: str, kind: str) -> int:
    val = get_redis().get(_quota_key(user_id, kind))
    return int(val) if val else 0


def consume_quota(user_id: str, kind: str, limit: int) -> None:
    r = get_redis()
    key = _quota_key(user_id, kind)
    current = r.incr(key)
    if current == 1:
        r.expire(key, 60 * 60 * 24 + 3600)
    if current > limit:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Daily {kind} quota of {limit} exhausted. Try again tomorrow.",
        )
