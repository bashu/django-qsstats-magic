Changes
-------

3.0.0 (unreleased)
~~~~~~~~~~~~~~~~~~

* **Backwards incompatible**: with ``USE_TZ = True``, days, weeks, months,
  quarters and years now start at local midnight in the current time zone
  (``TIME_ZONE``, or the one activated with ``timezone.activate()``) instead
  of at UTC midnight. This affects ``this_*()``, the default ``today``, and
  ``for_*()``/``time_series()`` called with ``datetime.date`` values. In a
  project whose ``TIME_ZONE`` is not UTC, counts near midnight move to the
  local day they belong to, so totals per day, week or month can change.
  Aware ``datetime`` arguments keep their own time zone, as before.
* Hourly and minutely ``time_series()`` follow the local clock as well: on a
  day when clocks go back the repeated hour is reported as one bucket, and on
  a day when they go forward the skipped hour appears as an empty bucket.
  No event is lost or counted twice.
* Fixed ``this_hour()`` and ``this_minute()`` counting the first hour and
  minute of the day instead of the current ones: they now use the current
  local time. ``today`` is still used by ``this_day()`` and longer intervals.

2.2.2 (2026-11-14)
~~~~~~~~~~~~~~~~~~

* Shipped a ``py.typed`` marker, so type checkers now use the package's type
  hints instead of treating ``qsstats`` as untyped. Projects running mypy or
  a similar checker may see new errors where calls do not match the hints.
* Fixed the README link to the usage examples in the tests.

2.2.1 (2026-11-14)
~~~~~~~~~~~~~~~~~~

* Switched the build backend from setuptools to hatchling and moved the
  package to the ``src`` layout. The installed package is unchanged.
* Fixed ``time_series()`` hanging forever on a singular interval (e.g.
  ``interval='day'``) or a zero count (``'0days'``). These, and any other
  interval outside the documented plural units with an optional positive
  count, now raise ``InvalidIntervalError`` before querying.
* Fixed ``time_series()`` stepping through every unit of a huge count
  (e.g. ``'1000000days'``) past the end of the range.

2.2.0 (2026-11-11)
~~~~~~~~~~~~~~~~~~

* Added ``quarter`` as an interval: ``for_quarter``, ``this_quarter``, and
  ``time_series(..., interval='quarters')``.
* Excluded ``qsstats.tests`` from the built package.

2.1.0 (2026-10-10)
~~~~~~~~~~~~~~~~~~

* Dropped Python 3.10 support. Python 3.11 is
  now the minimum required version.
* Added support for Python 3.15.

2.0.0 (2026-09-01)
~~~~~~~~~~~~~~~~~~

* **Backwards incompatible**: removed the deprecated ``InvalidInterval``,
  ``InvalidOperator``, ``DateFieldMissing`` and ``QuerySetMissing`` exception
  aliases (deprecated in 1.1.1). Use ``InvalidIntervalError``,
  ``InvalidOperatorError``, ``DateFieldMissingError`` and
  ``QuerySetMissingError`` instead.
* **Backwards incompatible**: ``time_series()`` no longer transparently
  falls back to a separate, slower query engine on ``ValueError``. That
  fallback's only trigger was a Python-level field-type check that's now
  handled upfront (see below), so it was dead, unreachable code - along
  with the bugs in it, including incorrect and sometimes missing buckets
  for ``interval='weeks'`` (and other intervals) when ``start``/``end``
  weren't aligned to interval boundaries. If your database genuinely
  can't perform timezone-aware truncation, that error now surfaces
  directly instead of being silently retried with a misleading warning.
* Fixed ``pivot()`` (and ``until``/``until_now``/``after``/``after_now``)
  raising ``AttributeError`` instead of falling back to the documented
  default operator (``'lte'``) when called without one; ``QuerySetStats``
  had silently lost its ``operator`` constructor argument.
* Fixed ``TypeError`` in ``time_series()`` when an aggregate (e.g. ``Sum``,
  ``Avg``) returned ``None`` for an interval instead of the default
  ``Count``'s ``0``.
* Fixed ``time_series()`` mislabeling buckets for multi-unit intervals
  (e.g. ``interval='2days'``): each bucket's timestamp drifted forward by
  ``num - 1`` units from its true start, even though the aggregated
  values themselves were already correct.
* Fixed the ``time_series()`` query unnecessarily falling back to a
  slower code path when ``date_field`` is a plain ``DateField`` rather
  than a ``DateTimeField``.
* Fixed ``__getattr__`` raising a bare, message-less ``AttributeError``
  for unknown attributes instead of a normal, informative one.
* Added type hints throughout ``qsstats.QuerySetStats`` and
  ``qsstats.utils``; the package is now mypy-clean.
* Added ``__all__`` to ``qsstats`` documenting its public API.
* Dropped the unused ``six`` dependency.

1.1.1 (2026-08-31)
~~~~~~~~~~~~~~~~~~

* Renamed ``InvalidInterval``, ``InvalidOperator``, ``DateFieldMissing`` and
  ``QuerySetMissing`` to ``InvalidIntervalError``, ``InvalidOperatorError``,
  ``DateFieldMissingError`` and ``QuerySetMissingError``. The old names still
  work but now raise a ``DeprecationWarning`` and will be removed in a future
  release.
* Dropped the ``qsstats.compat`` module; ``django.utils.timezone.now()`` is
  used directly.
* Now requires Python 3.10+ and Django 5.2+.
* Migrated packaging to ``pyproject.toml``, switched the test suite to
  pytest, and added pre-commit hooks and GitHub Actions CI/release
  workflows.
