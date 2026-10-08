from urllib.parse import urlsplit


def safe_next_url(target: str | None) -> str | None:
    """Return `target` only if it's a path on this site.

    Blocks open redirects such as //evil.com and /\\evil.com.
    """
    if not target or not target.startswith("/") or target.startswith(("//", "/\\")):
        return None
    parts = urlsplit(target)
    return target if not parts.scheme and not parts.netloc else None
