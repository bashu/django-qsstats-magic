import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

import pytest

from qsstats import DateFieldMissingError
from qsstats import InvalidIntervalError
from qsstats import InvalidOperatorError
from qsstats import QuerySetMissingError
from qsstats import QuerySetStats
from qsstats import utils


class QuerySetStatsTestCase(TestCase):
    def setUp(self):
        # We'll be making sure that this user is found
        self.user = User.objects.create_user("u1", "u1@example.com")
        # And that this user is not
        self.another_user = User.objects.create_user("u2", "u2@example.com")
        self.another_user.is_active = False
        self.another_user.save()

    def test_basic_today(self):
        # Create a QuerySet and QuerySetStats
        qss = QuerySetStats(User.objects.filter(is_active=True), "date_joined")

        # We should only see a single user
        assert qss.this_day() == 1

    def assert_time_series_works(self, today):
        seven_days_ago = today - datetime.timedelta(days=7)
        for j in range(1, 8):
            for i in range(j):
                u = User.objects.create_user(
                    f"p-{j}-{i}",
                    f"p{j}-{i}@example.com",
                )
                u.date_joined = today - datetime.timedelta(days=i)
                u.save()
        qss = QuerySetStats(
            User.objects.filter(username__startswith="p"),
            "date_joined",
        )
        time_series = qss.time_series(seven_days_ago, today)
        assert [t[1] for t in time_series] == [0, 1, 2, 3, 4, 5, 6, 7]

    def test_time_series(self):
        self.assert_time_series_works(utils._remove_time(timezone.now()))  # noqa: SLF001

    def test_time_series_naive(self):
        self.assert_time_series_works(
            datetime.datetime.now(tz=datetime.timezone.utc).date(),
        )

    def test_time_series_weeks(self):
        day = datetime.date(year=2013, month=4, day=5)

        self.user.date_joined = day
        self.user.save()

        qss = QuerySetStats(User.objects.filter(is_active=True), "date_joined")
        qss.time_series(day - datetime.timedelta(days=30), day, interval="weeks")

    def test_time_series_multi_unit_bucket_labels(self):
        # Each bucket's label must be its own start, not drift forward by
        # (num - 1) units - e.g. a "2days" bucket covering day0-1 must be
        # labeled day0, not day1.
        start = utils._remove_time(timezone.now())  # noqa: SLF001
        for i in range(5):
            u = User.objects.create_user(f"m{i}", f"m{i}@example.com")
            u.date_joined = start + datetime.timedelta(days=i)
            u.save()

        qss = QuerySetStats(
            User.objects.filter(username__startswith="m"),
            "date_joined",
        )
        end = start + datetime.timedelta(days=4)

        result = qss.time_series(start, end, interval="2days")
        assert result == [
            (start, 2),
            (start + datetime.timedelta(days=2), 2),
            (start + datetime.timedelta(days=4), 1),
        ]

    def test_until(self):
        now = timezone.now()
        today = utils._remove_time(now)  # noqa: SLF001
        yesterday = today - datetime.timedelta(days=1)

        self.user.date_joined = today
        self.user.save()

        qss = QuerySetStats(User.objects.filter(is_active=True), "date_joined")

        assert qss.until(now) == 1
        assert qss.until(today) == 1
        assert qss.until(yesterday) == 0
        assert qss.until_now() == 1

    def test_after(self):
        now = timezone.now()
        today = utils._remove_time(now)  # noqa: SLF001
        tomorrow = today + datetime.timedelta(days=1)

        self.user.date_joined = today
        self.user.save()

        qss = QuerySetStats(User.objects.filter(is_active=True), "date_joined")

        assert qss.after(now) == 0
        assert qss.after(today) == 1
        assert qss.after(tomorrow) == 0
        assert qss.after_now() == 0

    def test_attribute_error_has_name(self):
        # A missing attribute (not a for_*/this_* method) should raise a
        # normal, informative AttributeError - not a bare, message-less one.
        qss = QuerySetStats()

        with pytest.raises(AttributeError, match="bogus_attr") as exc_info:
            qss.bogus_attr  # noqa: B018

        assert exc_info.value.name == "bogus_attr"
        assert exc_info.value.obj is qss

    # TODO: aggregate_field tests

    def test_query_set_missing(self):
        qss = QuerySetStats(date_field="foo")

        for method in ["this_day", "this_month", "this_year"]:
            with pytest.raises(QuerySetMissingError):
                getattr(qss, method)()

    def test_date_field_missing(self):
        qss = QuerySetStats(User.objects.filter(is_active=True))

        for method in ["this_day", "this_month", "this_year"]:
            with pytest.raises(DateFieldMissingError):
                getattr(qss, method)()

    def test_invalid_interval(self):
        qss = QuerySetStats(User.objects.filter(is_active=True), "date_joined")

        with pytest.raises(InvalidIntervalError):
            qss.time_series(qss.today, qss.today, interval="monkeys")

    def test_pivot_default_operator(self):
        # pivot() without an explicit operator falls back to self.operator,
        # which defaults to 'lte' (see README's documented default).
        now = timezone.now()
        today = utils._remove_time(now)  # noqa: SLF001

        self.user.date_joined = today
        self.user.save()

        qss = QuerySetStats(User.objects.filter(is_active=True), "date_joined")

        assert qss.pivot(now) == 1

    def test_invalid_operator(self):
        qss = QuerySetStats(User.objects.filter(is_active=True), "date_joined")

        with pytest.raises(InvalidOperatorError):
            qss.pivot(qss.today, operator="monkeys")
