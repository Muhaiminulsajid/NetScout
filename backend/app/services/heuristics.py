"""Local URL heuristics — always available, no API key required."""
import ipaddress
import re
from urllib.parse import urlparse

SUSPICIOUS_TLDS = {
    "zip", "mov", "xyz", "top", "gq", "tk", "ml", "cf", "loan", "click",
    "work", "country", "stream", "download", "racing", "win", "bid",
}
PHISHY_KEYWORDS = {
    "login", "verify", "secure", "account", "update", "banking", "signin",
    "confirm", "password", "wallet", "free", "bonus", "prize", "urgent",
}
URL_SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly"}


def score_url_heuristics(url: str) -> dict:
    """Return {'score': 0..100, 'flags': [...]} based on lexical features."""
    flags: list[str] = []
    score = 0.0
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()

    try:
        ipaddress.ip_address(host)
        flags.append("ip_address_host")
        score += 30
    except ValueError:
        pass

    if host.startswith("xn--") or ".xn--" in host:
        flags.append("punycode_host")
        score += 25

    if len(url) > 120:
        flags.append("very_long_url")
        score += 10

    if host.count(".") >= 4:
        flags.append("excessive_subdomains")
        score += 15

    if "@" in parsed.netloc:
        flags.append("userinfo_in_url")
        score += 25

    tld = host.rsplit(".", 1)[-1] if "." in host else ""
    if tld in SUSPICIOUS_TLDS:
        flags.append(f"suspicious_tld:.{tld}")
        score += 15

    if host in URL_SHORTENERS:
        flags.append("url_shortener")
        score += 10

    path_query = f"{parsed.path}?{parsed.query}".lower()
    hits = [kw for kw in PHISHY_KEYWORDS if kw in path_query or kw in host]
    if len(hits) >= 2:
        flags.append("phishy_keywords:" + ",".join(hits[:4]))
        score += 15

    if re.search(r"%[0-9a-f]{2}", url, re.I) and url.lower().count("%") > 5:
        flags.append("heavy_url_encoding")
        score += 10

    if parsed.scheme == "http":
        flags.append("no_https")
        score += 10

    return {"score": min(score, 100.0), "flags": flags}
