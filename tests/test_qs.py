import datetime as dt
from collections.abc import Callable

from django.contrib.auth.models import User

import pytest

from qsstats import DateFieldMissingError
from qsstats import InvalidIntervalError
from qsstats import InvalidOperatorError
from qsstats import QuerySetMissingError
from qsstats import QuerySetStats

from .conftest import QuerySetStatsFactory


def test_this_day_counts_only_filtered_queryset(
    active_users_qss: QuerySetStats,
) -> None:
    assert active_users_qss.this_day() == 1


@pytest.mark.parametrize(
    ("method", "expected"),
    [
        pytest.param("this_minute", 2, id="minute"),
        pytest.param("this_hour", 3, id="hour"),
        pytest.param("this_day", 4, id="day"),
    ],
)
@pytest.mark.django_db
def test_this_interval_relative_to_current_time(
    now: dt.datetime,
    today: dt.datetime,
    method: str,
    expected: int,
) -> None:
    # The clock is frozen at the start of a minute, so all of these fall on
    # the same day, but only some of them in the current hour or minute.
    join_moments = [
        today,
        now,
        now + dt.timedelta(seconds=30),
        now + dt.timedelta(minutes=10),
    ]

    for idx, date_joined in enumerate(join_moments):
        User.objects.create_user(f"user-{idx}", date_joined=date_joined)

    qss = QuerySetStats(User.objects.all(), "date_joined")

    assert getattr(qss, method)() == expected


@pytest.mark.parametrize(
    "to_moment",
    [
        pytest.param(lambda day: day, id="datetime"),
        pytest.param(dt.datetime.date, id="date"),
    ],
)
def test_time_series_days(
    qss_for_date_joined_factory: QuerySetStatsFactory,
    today: dt.datetime,
    to_moment: Callable[[dt.datetime], dt.datetime | dt.date],
) -> None:
    # The user count grows by one each day: seven users today, none a week ago.
    join_dates = [
        today.date() - dt.timedelta(days=offset)
        for count in range(1, 8)
        for offset in range(count)
    ]
    qss = qss_for_date_joined_factory(join_dates)
    moment = to_moment(today)

    time_series = qss.time_series(moment - dt.timedelta(days=7), moment)

    assert [value for _, value in time_series] == [0, 1, 2, 3, 4, 5, 6, 7]


def test_this_day_counts_only_filtered_queryset_local_timezone(
    localtime_user_qss: QuerySetStats,
) -> None:
    assert localtime_user_qss.this_day() == 1


def test_time_series_days_local_timezone(
    localtime_user_qss: QuerySetStats,
) -> None:
    time_series = localtime_user_qss.time_series(
        dt.date(2026, 11, 13),
        dt.date(2026, 11, 14),
    )

    assert [(label.date(), value) for label, value in time_series] == [
        (dt.date(2026, 11, 13), 0),
        (dt.date(2026, 11, 14), 1),
    ]


def test_time_series_weeks(qss_for_date_joined_factory: QuerySetStatsFactory) -> None:
    day = dt.date(year=2013, month=4, day=5)
    qss = qss_for_date_joined_factory([day])

    time_series = qss.time_series(
        day - dt.timedelta(days=30),
        day,
        interval="weeks",
    )

    # Weeks start on Monday, so the series is aligned to Mondays rather than
    # to the requested start (Wednesday, March 6).
    assert [(label.date(), value) for label, value in time_series] == [
        (dt.date(2013, 3, 4), 0),
        (dt.date(2013, 3, 11), 0),
        (dt.date(2013, 3, 18), 0),
        (dt.date(2013, 3, 25), 0),
        (dt.date(2013, 4, 1), 1),
    ]


def test_time_series_quarters(
    qss_for_date_joined_factory: QuerySetStatsFactory,
) -> None:
    year = 2013
    quarter_starts = [
        dt.date(year, 1, 1),
        dt.date(year, 4, 1),
        dt.date(year, 7, 1),
        dt.date(year, 10, 1),
    ]
    # The N-th quarter gets N users.
    join_dates = [
        quarter_start
        for quarter, quarter_start in enumerate(quarter_starts, start=1)
        for _ in range(quarter)
    ]
    qss = qss_for_date_joined_factory(join_dates)

    time_series = qss.time_series(
        dt.date(year, 1, 1),
        dt.date(year, 12, 31),
        interval="quarters",
    )

    assert [value for _, value in time_series] == [1, 2, 3, 4]


def test_time_series_multi_unit_buckets_labeled_by_start(
    qss_for_date_joined_factory: QuerySetStatsFactory,
    today: dt.datetime,
) -> None:
    # A "2days" bucket covering days 0-1 must be labeled day 0,
    # not drift forward to day 1.
    join_dates = [today.date() + dt.timedelta(days=offset) for offset in range(5)]
    qss = qss_for_date_joined_factory(join_dates)

    time_series = qss.time_series(
        today,
        today + dt.timedelta(days=4),
        interval="2days",
    )

    assert time_series == [
        (today, 2),
        (today + dt.timedelta(days=2), 2),
        (today + dt.timedelta(days=4), 1),
    ]


def test_until(
    active_users_qss: QuerySetStats,
    active_user: User,
    now: dt.datetime,
    today: dt.datetime,
) -> None:
    active_user.date_joined = today
    active_user.save()

    assert active_users_qss.until(now) == 1
    assert active_users_qss.until(today) == 1
    assert active_users_qss.until(today - dt.timedelta(days=1)) == 0
    assert active_users_qss.until_now() == 1


def test_after(
    active_users_qss: QuerySetStats,
    active_user: User,
    now: dt.datetime,
    today: dt.datetime,
) -> None:
    active_user.date_joined = today
    active_user.save()

    assert active_users_qss.after(now) == 0
    assert active_users_qss.after(today) == 1
    assert active_users_qss.after(today + dt.timedelta(days=1)) == 0
    assert active_users_qss.after_now() == 0


def test_pivot_defaults_to_lte(
    active_users_qss: QuerySetStats,
    active_user: User,
    now: dt.datetime,
    today: dt.datetime,
) -> None:
    active_user.date_joined = today
    active_user.save()

    assert active_users_qss.pivot(now) == 1


def test_pivot_invalid_operator(active_users_qss: QuerySetStats) -> None:

    with pytest.raises(InvalidOperatorError, match="Please provide a valid operator"):
        active_users_qss.pivot(active_users_qss.today, operator="monkeys")


@pytest.mark.parametrize(
    "interval",
    [
        pytest.param("monkeys", id="unknown"),
        pytest.param("day", id="singular"),
        pytest.param("2day", id="singular-with-count"),
        pytest.param("0days", id="zero-count"),
        pytest.param("daysss", id="trailing-letters"),
        pytest.param("Days", id="capitalized"),
        pytest.param("2days3", id="trailing-digits"),
    ],
)
def test_time_series_invalid_interval(
    active_users_qss: QuerySetStats,
    interval: str,
) -> None:
    today = active_users_qss.today

    with pytest.raises(
        InvalidIntervalError,
        match=rf"Interval \({interval}\) not supported",
    ):
        active_users_qss.time_series(today, today, interval=interval)


def test_time_series_count_beyond_range_gives_one_bucket(
    qss_for_date_joined_factory: QuerySetStatsFactory,
    today: dt.datetime,
) -> None:
    qss = qss_for_date_joined_factory([today.date()])

    time_series = qss.time_series(today, today, interval="1000000days")

    assert time_series == [(today, 1)]


def test_unknown_attribute_error_has_name() -> None:
    qss = QuerySetStats()

    with pytest.raises(AttributeError, match="bogus_attr") as exc_info:
        qss.bogus_attr  # noqa: B018

    assert exc_info.value.name == "bogus_attr"
    assert exc_info.value.obj is qss


@pytest.mark.parametrize(
    "method",
    ["this_day", "this_month", "this_quarter", "this_year"],
)
def test_queryset_missing(method: str) -> None:
    qss = QuerySetStats(date_field="foo")

    with pytest.raises(QuerySetMissingError, match="Please provide a queryset"):
        getattr(qss, method)()


@pytest.mark.parametrize(
    "method",
    ["this_day", "this_month", "this_quarter", "this_year"],
)
def test_date_field_missing(method: str) -> None:
    qss = QuerySetStats(User.objects.filter(is_active=True))

    with pytest.raises(DateFieldMissingError, match="Please provide a date_field"):
        getattr(qss, method)()
