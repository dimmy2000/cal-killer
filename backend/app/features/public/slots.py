"""Slot compilation — pure functions.

Given a Schedule's WorkingHours / Overrides / existing Bookings and an
EventType's duration + notice, produce a list of available Slots in a
[from, to) window. All datetimes are timezone-aware UTC.

Key rules (ADR-0004, ADR-0002):
  - Availability is scoped to the Schedule. Every Booking whose EventType
    references the same Schedule consumes from one shared pool.
  - Slots are grid-aligned: the start must satisfy
        (minutes_since_midnight_local - workingHours.startMin) % durationMin == 0
  - `available=false` overrides block the whole day.
  - `minNoticeMin` cuts off slots too close to "now".
  - DST: spring-forward gaps produce no slot; fall-back ambiguous times keep
    the first occurrence (we generate wall-clock candidates in local time and
    convert to UTC, so a non-existent local time simply yields nothing).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo

MAX_WINDOW_DAYS = 60


def _day_to_date(day_of_week: int, start_date: date) -> date:
    """First date on/after start_date whose weekday == day_of_week."""
    offset = (day_of_week - start_date.weekday()) % 7
    return start_date + timedelta(days=offset)


# WorkingHours.dayOfWeek is ISO: 1=Monday..7=Sunday. Python date.weekday()
# returns 0=Monday..6=Sunday, so we compare against weekday()+1.
ISO_MONDAY = 1


def _iter_dates(start: date, end: date):
    d = start
    while d < end:
        yield d
        d += timedelta(days=1)


def _override_for(overrides: list[dict], d: date) -> dict | None:
    key = d.isoformat()
    for ov in overrides:
        if ov["date"] == key:
            return ov
    return None


def _booked_intervals(bookings: list[dict]) -> list[tuple[datetime, datetime]]:
    return [
        (
            _as_utc(b["startUtc"]),
            _as_utc(b["endUtc"]),
        )
        for b in bookings
    ]


def _as_utc(value) -> datetime:
    """Coerce a datetime (aware or naive) or ISO string to aware UTC.

    SQLite strips tzinfo on read-back, so ORM datetimes are often naive and
    must be re-stamped UTC before comparison with aware inputs.
    """
    dt = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def compile_slots(
    *,
    working_hours: list[dict],
    overrides: list[dict],
    bookings: list[dict],
    duration_min: int,
    min_notice_min: int,
    tz_name: str,
    from_utc: datetime,
    to_utc: datetime,
    now: datetime,
) -> list[dict]:
    """Compile available slots.

    Returns a list of ``{"startUtc": iso, "endUtc": iso}`` dicts sorted by
    start time. Inputs are expected in the Schedule's timezone for wall-clock
    intervals (working_hours / overrides) and UTC for datetimes.
    """
    if duration_min <= 0:
        return []

    tz: tzinfo = ZoneInfo(tz_name)
    booked = _booked_intervals(bookings)
    earliest = now + timedelta(minutes=min_notice_min)

    from_local = from_utc.astimezone(tz)
    to_local = to_utc.astimezone(tz)
    start_date = from_local.date()
    end_date = to_local.date()

    slots: list[dict] = []

    for d in _iter_dates(start_date, end_date + timedelta(days=1)):
        # Per-day override: available=false blocks the whole day.
        ov = _override_for(overrides, d)
        if ov is not None and ov.get("available") is False:
            continue

        for wh in working_hours:
            if wh["dayOfWeek"] != d.weekday() + 1:
                continue
            day_start_min = wh["startMin"]
            day_end_min = wh["endMin"]
            # If the override is available=True, narrow the window.
            if ov is not None and ov.get("available") is True:
                day_start_min = max(day_start_min, ov["startMin"])
                day_end_min = min(day_end_min, ov["endMin"])

            minute = day_start_min
            while minute + duration_min <= day_end_min:
                local_dt = datetime(d.year, d.month, d.day, minute // 60, minute % 60, tzinfo=tz)
                utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
                minute += duration_min

                if utc_dt < from_utc or utc_dt >= to_utc:
                    continue
                if utc_dt < earliest:
                    continue
                end_utc = utc_dt + timedelta(minutes=duration_min)
                if any(_overlaps(utc_dt, end_utc, bs, be) for bs, be in booked):
                    continue
                slots.append(
                    {
                        "startUtc": utc_dt.isoformat().replace("+00:00", "Z"),
                        "endUtc": end_utc.isoformat().replace("+00:00", "Z"),
                    }
                )

    slots.sort(key=lambda s: s["startUtc"])
    return slots
