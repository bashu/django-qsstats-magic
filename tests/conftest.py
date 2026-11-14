import datetime as dt
import zoneinfo
from collections.abc import Callable
from collections.abc import Iterable

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

import pytest
from pytest_django.fixtures import Settings
from time_machine import TimeMachineFixture

from qsstats import QuerySetStats

QuerySetStatsFactory = Callable[[Iterable[dt.date]], QuerySetStats]

FROZEN_MOMENT = dt.datetime(2026, 11, 14, 12, 0, tzinfo=dt.UTC)


@pytest.fixture(autouse=True)
def frozen_time(time_machine: TimeMachineFixture) -> None:
    """Stop the clock so a run crossing midnight cannot shift "today"."""
    time_machine.move_to(FROZEN_MOMENT, tick=False)


@pytest.fixture
def now() -> dt.datetime:
    return timezone.now()


def to_day_start(day: dt.date) -> dt.datetime:
    """Local midnight of ``day``: aware when ``USE_TZ`` is on, naive otherwise."""
    tzinfo = timezone.get_current_timezone() if settings.USE_TZ else None
    return dt.datetime.combine(day, dt.time(), tzinfo=tzinfo)


@pytest.fixture
def today(now: dt.datetime) -> dt.datetime:
    local_date = timezone.localdate(now) if settings.USE_TZ else now.date()
    return to_day_start(local_date)


@pytest.fixture
def active_user(db: None) -> User:
    return User.objects.create_user("u1", "u1@example.com")


@pytest.fixture
def inactive_user(db: None) -> User:
    return User.objects.create_user("u2", "u2@example.com", is_active=False)


@pytest.fixture
def active_users_qss(active_user: User, inactive_user: User) -> QuerySetStats:
    """Stats over active users: counts ``active_user``, skips ``inactive_user``."""
    return QuerySetStats(User.objects.filter(is_active=True), "date_joined")


@pytest.fixture
def localtime_user_qss(db: None, settings: Settings) -> QuerySetStats:
    """Stats over one user who joined at 02:00 local time on the frozen day.

    The project runs in Dubai (UTC+4), so that moment is still the previous
    day in UTC: 22:00 on November 13.
    """
    settings.TIME_ZONE = "Asia/Dubai"
    joined_at = dt.datetime(2026, 11, 14, 2, 0, tzinfo=zoneinfo.ZoneInfo("Asia/Dubai"))

    # Without USE_TZ the database stores naive local time.
    if not settings.USE_TZ:
        joined_at = timezone.make_naive(joined_at)

    User.objects.create_user(
        "early-bird",
        "early-bird@example.com",
        date_joined=joined_at,
    )

    return QuerySetStats(User.objects.all(), "date_joined")


@pytest.fixture
def qss_for_date_joined_factory(db: None) -> QuerySetStatsFactory:
    """Create one user joined at midnight of each date; return qss over all users."""

    def create_qss_for_date_joined(join_dates: Iterable[dt.date]) -> QuerySetStats:

        for idx, join_date in enumerate(join_dates):
            User.objects.create_user(
                f"user-{idx}",
                f"user-{idx}@example.com",
                date_joined=to_day_start(join_date),
            )

        return QuerySetStats(User.objects.all(), "date_joined")

    return create_qss_for_date_joined
