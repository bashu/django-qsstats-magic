import datetime
import warnings
from functools import partial
from typing import Any

from django.core.exceptions import FieldDoesNotExist
from django.db import transaction
from django.db.models import Aggregate
from django.db.models import Count
from django.db.models import DateTimeField
from django.db.models import QuerySet
from django.db.models.functions import Trunc
from django.utils import timezone

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from six import string_types

from qsstats import exceptions
from qsstats import utils
from qsstats.exceptions import DateFieldMissingError
from qsstats.exceptions import InvalidIntervalError
from qsstats.exceptions import InvalidOperatorError
from qsstats.exceptions import QuerySetMissingError

# Deprecated exception aliases (see qsstats.exceptions), resolved lazily so
# that accessing e.g. qsstats.DateFieldMissing warns, without warning for
# everyone who merely imports this package.
# TODO: remove in the next major release.
_DEPRECATED_EXCEPTION_ALIASES = frozenset(
    {"InvalidInterval", "InvalidOperator", "DateFieldMissing", "QuerySetMissing"},
)


def __getattr__(name):
    if name in _DEPRECATED_EXCEPTION_ALIASES:
        return getattr(exceptions, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


class QuerySetStats:
    """
    Generates statistics about a queryset using Django aggregates.  QuerySetStats
    is able to handle snapshots of data (for example this day, week, month, or
    year) or generate time series data suitable for graphing.
    """

    def __init__(
        self,
        qs: QuerySet | None = None,
        date_field: str | None = None,
        aggregate: Aggregate | None = None,
        today: datetime.datetime | None = None,
    ):
        self.qs = qs
        self.date_field = date_field
        self.aggregate = aggregate or Count("id", distinct=True)
        self.today = today or self.update_today()

    # Aggregates for a specific period of time

    def for_interval(
        self,
        interval: str,
        dt: datetime.datetime | datetime.date,
        date_field: str | None = None,
        aggregate: Aggregate | None = None,
    ) -> Any | None:
        start, end = utils.get_bounds(dt, interval)
        date_field = date_field or self.date_field
        kwargs = {f"{date_field}__range": (start, end)}
        return self._aggregate(date_field, aggregate, kwargs)

    def this_interval(
        self,
        interval: str,
        date_field: str | None = None,
        aggregate: Aggregate | None = None,
    ) -> Any | None:
        method = getattr(self, f"for_{interval}")
        return method(self.today, date_field, aggregate)

    # support for this_* and for_* methods
    def __getattr__(self, name):
        if name.startswith("for_"):
            return partial(self.for_interval, name[4:])
        if name.startswith("this_"):
            return partial(self.this_interval, name[5:])
        raise AttributeError

    def time_series(  # noqa: PLR0913, PLR0917
        self,
        start: datetime.datetime | datetime.date,
        end: datetime.datetime | datetime.date | None = None,
        interval: str = "days",
        date_field: str | None = None,
        aggregate: Aggregate | None = None,
        engine=None,
    ) -> list[tuple[datetime.datetime, int]]:
        """Aggregate over time intervals"""

        end = end or self.today
        args = [start, end, interval, date_field, aggregate]
        sid = transaction.savepoint()
        try:
            return self._fast_time_series(*args)
        except ValueError:
            transaction.savepoint_rollback(sid)
            warnings.warn(
                "Your database doesn't support timezones. Switching to slower QSStats queries.",  # noqa: E501
                stacklevel=2,
            )
            return self._slow_time_series(*args)

    def _slow_time_series(
        self,
        start: datetime.datetime | datetime.date,
        end: datetime.datetime | datetime.date,
        interval: str = "days",
        date_field: str | None = None,
        aggregate: Aggregate | None = None,
    ) -> list[tuple[datetime.datetime, int]]:
        """Aggregate over time intervals using 1 sql query for one interval"""

        num, interval = utils._parse_interval(interval)  # noqa: SLF001

        if (
            interval not in ["minutes", "hours", "days", "weeks", "months", "years"]
            or num != 1
        ):
            msg = "Interval is currently not supported."
            raise InvalidIntervalError(msg)

        method = getattr(self, f"for_{interval[:-1]}")

        stat_list = []
        dt, end = utils._to_datetime(start), utils._to_datetime(end)  # noqa: SLF001
        while dt <= end:
            value = method(dt, date_field, aggregate)
            stat_list.append((dt, value))
            dt = dt + relativedelta(**{interval: 1})
        return stat_list

    def _fast_time_series(
        self,
        start: datetime.datetime | datetime.date,
        end: datetime.datetime | datetime.date,
        interval: str = "days",
        date_field: str | None = None,
        aggregate: Aggregate | None = None,
    ) -> list[tuple[datetime.datetime, int]]:
        """Aggregate over time intervals using just 1 sql query"""

        date_field = date_field or self.date_field
        aggregate = aggregate or self.aggregate

        num, interval = utils._parse_interval(interval)  # noqa: SLF001

        interval_s = interval.rstrip("s")
        start, _ = utils.get_bounds(start, interval_s)
        _, end = utils.get_bounds(end, interval_s)

        kwargs = {f"{date_field}__range": (start, end)}

        # Trunc() unconditionally raises ValueError("tzinfo can only be used
        # with DateTimeField.") if tzinfo is passed for a plain DateField -
        # and a DateField has no timezone component to convert anyway. Only
        # pass tzinfo when date_field actually resolves to a DateTimeField,
        # so the fast path doesn't needlessly fall back to _slow_time_series.
        #  TODO: maybe we could use the tzinfo for the user's location
        trunc_kwargs = {}
        try:
            model_field = self.qs.model._meta.get_field(date_field)  # noqa: SLF001
        except (FieldDoesNotExist, AttributeError):
            model_field = None
        if isinstance(model_field, DateTimeField):
            trunc_kwargs["tzinfo"] = start.tzinfo

        aggregate_data = (
            self.qs.filter(**kwargs)
            .annotate(d=Trunc(date_field, interval_s, **trunc_kwargs))
            .order_by()
            .values("d")
            .annotate(agg=aggregate)
        )

        today = utils._remove_time(timezone.now())  # noqa: SLF001

        def to_dt(
            d: datetime.datetime | datetime.date | str,
        ) -> datetime.datetime:
            if isinstance(d, string_types):
                return parse(d, yearfirst=True, default=today)
            if type(d).__name__ == "date":
                return datetime.datetime(
                    year=d.year,
                    month=d.month,
                    day=d.day,
                    tzinfo=start.tzinfo,
                )
            return d

        data = {to_dt(item["d"]): item["agg"] for item in aggregate_data}

        stat_list = []
        dt = start
        while dt < end:
            idx = 0
            value = 0
            for i in range(num):
                value = value + data.get(dt, 0)
                if i == 0:
                    stat_list.append((dt, value))
                    idx = len(stat_list) - 1
                elif i == num - 1:
                    stat_list[idx] = (dt, value)
                dt = dt + relativedelta(**{interval: 1})

        return stat_list

    # Aggregate totals using a date or datetime as a pivot

    def until(
        self,
        dt: datetime.datetime | datetime.date,
        date_field: str | None = None,
        aggregate: Aggregate | None = None,
    ) -> Any | None:
        return self.pivot(dt, "lte", date_field, aggregate)

    def until_now(
        self,
        date_field: str | None = None,
        aggregate: Aggregate | None = None,
    ) -> Any | None:
        return self.pivot(timezone.now(), "lte", date_field, aggregate)

    def after(
        self,
        dt: datetime.datetime | datetime.date,
        date_field: str | None = None,
        aggregate: Aggregate | None = None,
    ) -> Any | None:
        return self.pivot(dt, "gte", date_field, aggregate)

    def after_now(
        self,
        date_field: str | None = None,
        aggregate: Aggregate | None = None,
    ) -> Any | None:
        return self.pivot(timezone.now(), "gte", date_field, aggregate)

    def pivot(
        self,
        dt: datetime.datetime | datetime.date,
        operator=None,
        date_field: str | None = None,
        aggregate: Aggregate | None = None,
    ) -> Any | None:
        operator = operator or self.operator
        if operator not in ["lt", "lte", "gt", "gte"]:
            msg = "Please provide a valid operator."
            raise InvalidOperatorError(msg)

        kwargs = {f"{date_field or self.date_field}__{operator}": dt}
        return self._aggregate(date_field, aggregate, kwargs)

    # Utility functions
    def update_today(self) -> datetime.datetime:
        _now = timezone.now()
        self.today = utils._remove_time(_now)  # noqa: SLF001
        return self.today

    def _aggregate(
        self,
        date_field: str | None = None,
        aggregate: Aggregate | None = None,
        filter_kwargs: dict | None = None,
    ) -> Any | None:
        date_field = date_field or self.date_field
        aggregate = aggregate or self.aggregate

        if not date_field:
            msg = "Please provide a date_field."
            raise DateFieldMissingError(msg)

        if self.qs is None:
            msg = "Please provide a queryset."
            raise QuerySetMissingError(msg)

        agg = self.qs.filter(**filter_kwargs).aggregate(agg=aggregate)
        return agg["agg"]
