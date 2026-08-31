Changes
-------

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
