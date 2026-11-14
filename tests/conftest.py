import datetime as dt
from collections.abc import Callable
from collections.abc import Iterable

from django.contrib.auth.models import User
from django.utils import timezone

import pytest
from time_machine import TimeMachineFixture

from qsstats import QuerySetStats

StatsFactory = Callable[[Iterable[dt.date]], QuerySetStats]

FROZEN_MOMENT = dt.datetime(2026, 11, 14, 12, 0, tzinfo=dt.UTC)


@pytest.fixture(autouse=True)
def frozen_time(time_machine: TimeMachineFixture) -> None:
    """Stop the clock so a run crossing midnight cannot shift "today"."""
    time_machine.move_to(FROZEN_MOMENT, tick=False)


@pytest.fixture
def now() -> dt.datetime:
    return timezone.now()


def to_day_start(day: dt.date) -> dt.datetime:
    """Midnight of ``day``, aware in UTC when ``USE_TZ`` is on, naive otherwise."""
    return dt.datetime.combine(day, dt.time(), tzinfo=timezone.now().tzinfo)


@pytest.fixture
def today(now: dt.datetime) -> dt.datetime:
    return to_day_start(now.date())


@pytest.fixture
def active_user(db: None) -> User:
    return User.objects.create_user("u1", "u1@example.com")


@pytest.fixture
def inactive_user(db: None) -> User:
    return User.objects.create_user("u2", "u2@example.com", is_active=False)


@pytest.fixture
def active_users_stats(active_user: User, inactive_user: User) -> QuerySetStats:
    """Stats over active users: counts ``active_user``, skips ``inactive_user``."""
    return QuerySetStats(User.objects.filter(is_active=True), "date_joined")


@pytest.fixture
def joined_users_stats_factory(db: None) -> StatsFactory:
    """Create one user joined at midnight of each date; return stats over all users."""

    def create_joined_users_stats(join_dates: Iterable[dt.date]) -> QuerySetStats:

        for idx, join_date in enumerate(join_dates):
            User.objects.create_user(
                f"user-{idx}",
                f"user-{idx}@example.com",
                date_joined=to_day_start(join_date),
            )

        return QuerySetStats(User.objects.all(), "date_joined")

    return create_joined_users_stats
