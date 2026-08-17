"""Aggregate spam/phishing scoring.

Combines VirusTotal, Google Safe Browsing, SSL validity, domain age and
lexical heuristics into a 0-100 score with a green/amber/red verdict.
Every external signal degrades gracefully to None when unavailable, in
which case the weight is redistributed to the signals we do have.
"""
import hashlib
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..models import UrlScore
from .domain_age import get_domain_age_days
from .heuristics import score_url_heuristics
from .safebrowsing import gsb_check
from .ssl_check import check_ssl
from .virustotal import vt_url_report

CACHE_TTL = timedelta(hours=12)

WEIGHTS = {
    "virustotal": 0.35,
    "safebrowsing": 0.25,
    "heuristics": 0.20,
    "ssl": 0.10,
    "domain_age": 0.10,
}


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def _component_scores(url: str) -> tuple[dict[str, float | None], dict]:
    details: dict = {}

    vt = vt_url_report(url)
    details["virustotal"] = vt
    vt_score = None
    if vt and vt["total"]:
        vt_score = min(100.0, (vt["malicious"] * 100 + vt["suspicious"] * 50)
                       / max(vt["total"], 1) * 5)

    gsb = gsb_check(url)
    details["safebrowsing"] = gsb
    gsb_score = None
    if gsb is not None:
        gsb_score = 100.0 if gsb["threats"] else 0.0

    heur = score_url_heuristics(url)
    details["heuristics"] = heur
    heur_score: float | None = heur["score"]

    ssl_info = check_ssl(url)
    details["ssl"] = ssl_info
    if ssl_info["valid"] is True:
        ssl_score: float | None = 0.0
    elif ssl_info["valid"] is False:
        ssl_score = 100.0
    elif ssl_info["error"] == "not_https":
        ssl_score = 40.0
    else:
        ssl_score = None

    age_days = get_domain_age_days(url)
    details["domain_age_days"] = age_days
    if age_days is None:
        age_score = None
    elif age_days < 30:
        age_score = 90.0
    elif age_days < 180:
        age_score = 50.0
    elif age_days < 365:
        age_score = 25.0
    else:
        age_score = 0.0

    return (
        {
            "virustotal": vt_score,
            "safebrowsing": gsb_score,
            "heuristics": heur_score,
            "ssl": ssl_score,
            "domain_age": age_score,
        },
        details,
    )


def compute_spam_score(url: str) -> dict:
    """Return {'score': float, 'verdict': str, 'details': dict}."""
    components, details = _component_scores(url)
    available = {k: v for k, v in components.items() if v is not None}
    if available:
        total_weight = sum(WEIGHTS[k] for k in available)
        score = sum(WEIGHTS[k] * v for k, v in available.items()) / total_weight
    else:
        score = 0.0
    # Hard override: a confirmed Safe Browsing threat is always red.
    if components.get("safebrowsing") == 100.0:
        score = max(score, 85.0)

    verdict = "green" if score < 25 else "amber" if score < 60 else "red"
    details["component_scores"] = components
    return {"score": round(score, 1), "verdict": verdict, "details": details}


def get_or_compute_score(db: Session, url: str) -> dict:
    """DB-cached wrapper around compute_spam_score."""
    h = url_hash(url)
    cached = db.get(UrlScore, h)
    if cached and datetime.utcnow() - cached.checked_at < CACHE_TTL:
        return {"score": cached.score, "verdict": cached.verdict, "details": cached.details}

    result = compute_spam_score(url)
    if cached:
        cached.score = result["score"]
        cached.verdict = result["verdict"]
        cached.details = result["details"]
        cached.checked_at = datetime.utcnow()
    else:
        db.add(UrlScore(url_hash=h, url=url, score=result["score"],
                        verdict=result["verdict"], details=result["details"]))
    db.commit()
    return result
