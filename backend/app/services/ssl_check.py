"""SSL certificate validity check via a raw TLS handshake."""
import socket
import ssl
from datetime import datetime
from urllib.parse import urlparse


def check_ssl(url: str, timeout: float = 6.0) -> dict:
    """Return {'valid': bool|None, 'issuer': str|None, 'expires': str|None, 'error': str|None}."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return {"valid": None, "issuer": None, "expires": None, "error": "not_https"}
    host = parsed.hostname
    port = parsed.port or 443
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
        issuer = ", ".join(
            f"{k}={v}" for pair in cert.get("issuer", ()) for k, v in pair
        ) or None
        not_after = cert.get("notAfter")
        expires = None
        if not_after:
            expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").isoformat()
        return {"valid": True, "issuer": issuer, "expires": expires, "error": None}
    except ssl.SSLError as exc:
        return {"valid": False, "issuer": None, "expires": None, "error": f"ssl:{exc}"}
    except Exception as exc:  # noqa: BLE001 - network errors are expected
        return {"valid": None, "issuer": None, "expires": None, "error": str(exc)}
