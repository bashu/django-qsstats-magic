Changes
-------

1.2.0 (WIP)
~~~~~~~~~~~

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
