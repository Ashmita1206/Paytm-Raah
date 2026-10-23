from datetime import datetime, timezone

def utcnow() -> datetime:
    """Returns naive UTC datetime for seamless SQLite & SQLAlchemy datetime arithmetic."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

def ensure_naive(dt: datetime) -> datetime:
    """Ensures datetime is offset-naive UTC."""
    if dt is None:
        return None
    if getattr(dt, "tzinfo", None) is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
