import datetime as dt
import re

from django.utils import timezone

from dateutil.relativedelta import MO
from dateutil.relativedelta import relativedelta

from qsstats.exceptions import InvalidIntervalError


def _remove_time(
    moment: dt.datetime | dt.date,
) -> dt.datetime:
    tzinfo = getattr(moment, "tzinfo", timezone.now().tzinfo)
    return dt.datetime(moment.year, moment.month, moment.day, tzinfo=tzinfo)


def _to_datetime(
    moment: dt.datetime | dt.date,
) -> dt.datetime:
    if isinstance(moment, dt.datetime):
        return moment
    return _remove_time(moment)


def _parse_interval(interval: str) -> tuple[int, str]:
    num = 1
    match = re.match(r"(\d+)([A-Za-z]+)", interval)

    if match:
        num = int(match.group(1))
        interval = match.group(2)
    return num, interval


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
