"""Domain age lookup via WHOIS. Falls back to None on failure."""
from datetime import datetime
from urllib.parse import urlparse

import whois  # python-whois


def get_domain_age_days(url: str) -> int | None:
    host = urlparse(url).hostname
    if not host:
        return None
    try:
        info = whois.whois(host)
        created = info.creation_date
        if isinstance(created, list):
            created = created[0] if created else None
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except ValueError:
                return None
        if not isinstance(created, datetime):
            return None
        return max((datetime.utcnow() - created.replace(tzinfo=None)).days, 0)
    except Exception:  # noqa: BLE001 - WHOIS is flaky by nature
        return None
