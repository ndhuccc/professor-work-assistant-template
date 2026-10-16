"""Time helpers. Rule: new code never calls datetime.now()/utcnow() directly.

* Database timestamps of the quiz/assignment extension are naive UTC.
* Taipei is a fixed UTC+8 zone (no DST), so a fixed offset is used (no tzdata dependency on Windows).
* Legacy ``tasks/subtasks.deadline`` values are naive *Taipei local time*; use ``taipei_naive_now()`` to
  compare against them, independent of the machine's own time zone.
"""
from datetime import datetime, timedelta, timezone

TAIPEI = timezone(timedelta(hours=8), 'Asia/Taipei')
UTC = timezone.utc


def now_utc() -> datetime:
    """Current time as a naive UTC datetime (the storage format)."""
    return datetime.now(UTC).replace(tzinfo=None)


def taipei_naive_now() -> datetime:
    """Current Taipei wall-clock time as a naive datetime (to compare with legacy deadlines)."""
    return datetime.now(TAIPEI).replace(tzinfo=None)


def to_taipei(dt_utc):
    """Naive UTC -> aware Taipei datetime (None passes through)."""
    if dt_utc is None:
        return None
    return dt_utc.replace(tzinfo=UTC).astimezone(TAIPEI)


def fmt_taipei(dt_utc, fmt='%Y-%m-%d %H:%M'):
    t = to_taipei(dt_utc)
    return t.strftime(fmt) if t else ''


def parse_taipei_local(text):
    """'YYYY-MM-DDTHH:MM' (datetime-local input, Taipei) -> naive UTC. Empty -> None."""
    text = (text or '').strip()
    if not text:
        return None
    for fmt in ('%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S'):
        try:
            local = datetime.strptime(text, fmt)
            return local.replace(tzinfo=TAIPEI).astimezone(UTC).replace(tzinfo=None)
        except ValueError:
            continue
    raise ValueError(f'無法解析時間:{text!r}')


def to_local_input(dt_utc):
    """Naive UTC -> value for <input type=datetime-local> (Taipei)."""
    t = to_taipei(dt_utc)
    return t.strftime('%Y-%m-%dT%H:%M') if t else ''


def iso_z(dt_utc):
    """Naive UTC -> 'YYYY-MM-DDTHH:MM:SSZ' (None -> None)."""
    return dt_utc.strftime('%Y-%m-%dT%H:%M:%SZ') if dt_utc else None


def parse_iso_z(text):
    """'2026-10-19T06:10:03Z' (or with +00:00) -> naive UTC. Raises ValueError."""
    if not isinstance(text, str):
        raise ValueError('時間必須是字串')
    t = text.strip()
    if t.endswith('Z'):
        t = t[:-1] + '+00:00'
    dt = datetime.fromisoformat(t)
    if dt.tzinfo is None:
        raise ValueError('時間必須含時區(例如結尾 Z)')
    return dt.astimezone(UTC).replace(tzinfo=None)
