from datetime import UTC, datetime


def get_now() -> datetime:
    """Returns the current time in UTC."""
    return datetime.now(UTC)
