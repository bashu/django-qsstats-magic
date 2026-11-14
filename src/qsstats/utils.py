import datetime as dt
import re

from django.utils import timezone

from dateutil.relativedelta import MO
from dateutil.relativedelta import relativedelta

from qsstats.exceptions import InvalidIntervalError

TIME_SERIES_UNITS = frozenset(
    {"minutes", "hours", "days", "weeks", "months", "quarters", "years"},
)


def _remove_time(
    moment: dt.datetime | dt.date,
) -> dt.datetime:
    tzinfo = moment.tzinfo if isinstance(moment, dt.datetime) else timezone.now().tzinfo
    return dt.datetime(moment.year, moment.month, moment.day, tzinfo=tzinfo)


def _to_datetime(
    moment: dt.datetime | dt.date,
) -> dt.datetime:
    if isinstance(moment, dt.datetime):
        return moment
    return _remove_time(moment)


def _parse_interval(interval: str) -> tuple[int, str]:
    """Split a time series interval such as ``"2days"`` into a count and a unit.

    Only plural units are accepted: a singular one would make step() set an
    absolute field (``relativedelta(day=1)``) instead of advancing, and a zero
    count would never advance either, so time_series() would loop forever.
    """
    # The optional count must be positive: "0days" is rejected, "02days" is 2.
    match = re.fullmatch(r"(0*[1-9]\d*)?([a-z]+)", interval)

    if match is None or match.group(2) not in TIME_SERIES_UNITS:
        msg = f"Interval ({interval}) not supported."
        raise InvalidIntervalError(msg)

    return int(match.group(1) or 1), match.group(2)


def step(interval: str) -> relativedelta:
    """A relativedelta() advancing by one pluralized `interval` unit.

    relativedelta() has no `quarters` keyword, so that one needs mapping to
    its equivalent in months.
    """
    if interval == "quarters":
        return relativedelta(months=3)
    # dt1 and dt2 are passed explicitly so the type checker matches the unit
    # keyword only against relativedelta's keyword parameters.
    return relativedelta(None, None, **{interval: 1})


def get_bounds(
    moment: dt.datetime | dt.date,
    interval: str,
) -> tuple[dt.datetime, dt.datetime]:
    """Returns interval bounds the datetime is in."""

    day = _remove_time(moment)
    moment = _to_datetime(moment)

    if interval == "minute":
        begin = dt.datetime(
            moment.year,
            moment.month,
            moment.day,
            moment.hour,
            moment.minute,
            tzinfo=moment.tzinfo,
        )
        end = begin + relativedelta(minutes=1)
    elif interval == "hour":
        begin = dt.datetime(
            moment.year,
            moment.month,
            moment.day,
            moment.hour,
            tzinfo=moment.tzinfo,
        )
        end = begin + relativedelta(hours=1)
    elif interval == "day":
        begin = day
        end = day + relativedelta(days=1)
    elif interval == "week":
        begin = day - relativedelta(weekday=MO(-1))
        end = begin + dt.timedelta(days=7)
    elif interval == "month":
        begin = dt.datetime(moment.year, moment.month, 1, tzinfo=moment.tzinfo)
        end = begin + relativedelta(months=1)
    elif interval == "quarter":
        begin = dt.datetime(
            moment.year,
            ((moment.month - 1) // 3) * 3 + 1,
            1,
            tzinfo=moment.tzinfo,
        )
        end = begin + relativedelta(months=3)
    elif interval == "year":
        begin = dt.datetime(moment.year, 1, 1, tzinfo=moment.tzinfo)
        end = dt.datetime(moment.year + 1, 1, 1, tzinfo=moment.tzinfo)
    else:
        msg = f"Interval ({interval}) not supported."
        raise InvalidIntervalError(
            msg,
        )
    end = end - relativedelta(microseconds=1)

    return begin, end
