====================================================
django-qsstats-magic: QuerySet statistics for Django
====================================================

The goal of django-qsstats is to be a microframework to make
repetitive tasks such as generating aggregate statistics of querysets
over time easier.  It's probably overkill for the task at hand, but yay
microframeworks!

django-qsstats-magic is a refactoring of django-qsstats app with slightly
changed API, simplified internals and faster time_series implementation.


Requirements
============

* `python-dateutil <http://labix.org/python-dateutil>`_ > 1.4, < 2.0
* `django <http://www.djangoproject.com/>`_ 1.8+

License
=======

Liensed under a BSD-style license.

Examples
========

How many users signed up today? this month? this year?
------------------------------------------------------

::

    from django.contrib.auth.models import User
    import qsstats

    qs = User.objects.all()
    qss = qsstats.QuerySetStats(qs, 'date_joined')

    print '%s new accounts today.' % qss.this_day()[0]
    print '%s new accounts this week.' % qss.this_week()[0]
    print '%s new accounts this month.' % qss.this_month()[0]
    print '%s new accounts this year.' % qss.this_year()[0]
    print '%s new accounts until now.' % qss.until_now()[0]

This might print something like::

    5 new accounts today.
    11 new accounts this week.
    27 new accounts this month.
    377 new accounts this year.
    409 new accounts until now.

Aggregating time-series data suitable for graphing
--------------------------------------------------

::

    from django.contrib.auth.models import User
    import datetime, qsstats

    qs = User.objects.all()
    qss = qsstats.QuerySetStats(qs, 'date_joined')

    time_series = qss.time_series(seven_days_ago, today)
    print 'New users in the last 7 days: %s' % [t[1] for t in time_series]

This might print something like::

    New users in the last 7 days: [3, 10, 7, 4, 12, 9, 11]


Please see qsstats/tests.py for similar usage examples.

Multiple aggregates
-------------------

::

    from my_store_app.models import Purchase
    from django.db.models import Sum, Count
    import datetime, qsstats

    qs = Purchase.objects.all()
    qss = qsstats.QuerySetStats(qs, 'date_purchased', aggregates=[Count('id'), Sum('amount')])

    print '%s Purchases of value %s today.' % tuple(qss.this_day())
    print '%s Purchases of value %s this week.' % tuple(qss.this_week())
    print '%s Purchases of value %s this month.' % tuple(qss.this_month())
    print '%s Purchases of value %s this year.' % tuple(qss.this_year())
    print '%s Purchases of value %s until now.' % tuple(qss.until_now())

This might print something like::

    5 Purchases of value 50 today.
    11 Purchases of value 110 this week.
    27 Purchases of value 270 this month.
    377 Purchases of value 3770 year.
    409 Purchases of value 4090 until now.

API
===

The ``QuerySetStats`` object
----------------------------

In order to provide maximum flexibility, the ``QuerySetStats`` object
can be instantiated with as little or as much information as you like.
All keword arguments are optional but ``DateFieldMissing`` and
``QuerySetMissing`` will be raised if you try to use ``QuerySetStats``
without providing enough information.

``qs``
    The queryset to operate on.

    Default: ``None``

``date_field``
    The date field within the queryset to use.

    Default: ``None``

``aggregates``
    A list of django aggregation instances. Can be set also set when
    instantiating or calling one of the methods. You can also pass
    one aggregation instance.

    Default: ``[Count('id')]``

``operator``
    The default operator to use for the ``pivot`` function.  Can be also set
    when calling ``pivot``.

    Default: ``'lte'``

``today``
    The date that will be considered as today date. If ``today`` param is None
    QuerySetStats' today will be datetime.date.today().

    Default: ``None``


All of the documented methods take a standard set of keyword arguments
that override any information already stored within the ``QuerySetStats``
object.  These keyword arguments are ``date_field`` and ``aggregates``.

Once you have a ``QuerySetStats`` object instantiated, you can receive a
single aggregate result by using the following methods:

* ``for_minute``
* ``for_hour``
* ``for_day``
* ``for_week``
* ``for_month``
* ``for_year``

    Positional arguments: ``dt``, a ``datetime.datetime`` or ``datetime.date``
    object to filter the queryset to this interval (minute, hour, day, week,
    month or year).

* ``this_minute``
* ``this_hour``
* ``this_day``
* ``this_week``
* ``this_month``
* ``this_year``

    Wrappers around ``for_<interval>`` that uses ``dateutil.relativedelta`` to
    provide aggregate information for this current interval.

``QuerySetStats`` also provides a method for returning aggregated
time-series data which may be extremely using in plotting data:

``time_series``
    Positional arguments: ``start`` and ``end``, each a
    ``datetime.date`` or ``datetime.datetime`` object used in marking
    the start and stop of the time series data.

    Keyword arguments: In addition to the standard ``date_field`` and
    ``aggregates`` keyword argument, ``time_series`` takes an optional
    ``interval`` keyword argument used to mark which interval to use while
    calculating aggregate data between ``start`` and ``end``.  This argument
    defaults to ``'days'`` and can accept ``'years'``, ``'months'``,
    ``'weeks'``, ``'days'``, ``'hours'`` or ``'minutes'``.
    It will raise ``InvalidInterval`` otherwise.

    This methods returns a list of tuples.  The first item in each
    tuple is a ``datetime.datetime`` object for the current inverval.  The
    other items are the results of the aggregates operations.  For
    example::

        [(datetime.datetime(2010, 3, 28, 0, 0), 12), (datetime.datetime(2010, 3, 29, 0, 0), 0), ...]

    Formatting of date information is left as an exercise to the user and may
    vary depending on interval used.

``until``
    Provide aggregate information until a given date or time, filtering the
    queryset using ``lte``.

    Positional arguments: ``dt`` a ``datetime.date`` or ``datetime.datetime``
    object to be used for filtering the queryset since.

    Keyword arguments: ``date_field``, ``aggregates``.

``until_now``
    Aggregate information until now.

    Positional arguments: ``dt`` a ``datetime.date`` or ``datetime.datetime``
    object to be used for filtering the queryset since (using ``lte``).

    Keyword arguments: ``date_field``, ``aggregates``.

``after``
    Aggregate information after a given date or time, filtering the queryset
    using ``gte``.

    Positional arguments: ``dt`` a ``datetime.date`` or ``datetime.datetime``
    object to be used for filtering the queryset since.

    Keyword arguments: ``date_field``, ``aggregates``.

``after_now``
    Aggregate information after now.

    Positional arguments: ``dt`` a ``datetime.date`` or ``datetime.datetime``
    object to be used for filtering the queryset since (using ``gte``).

    Keyword arguments: ``date_field``, ``aggregates``.

``pivot``
    Used by ``since``, ``after``, and ``until_now`` but potentially useful if
    you would like to specify your own operator instead of the defaults.

    Positional arguments: ``dt`` a ``datetime.date`` or ``datetime.datetime``
    object to be used for filtering the queryset since (using ``lte``).

    Keyword arguments: ``operator``, ``date_field``, ``aggregates``.

    Raises ``InvalidOperator`` if the operator provided is not one of ``'lt'``,
    ``'lte'``, ``gt`` or ``gte``.

Testing
=======

If you'd like to test ``django-qsstats-magic`` against your local configuration, add
``qsstats`` to your ``INSTALLED_APPS`` and run ``./manage.py test qsstats``.
The test suite assumes that ``django.contrib.auth`` is installed.

For testing against different python, DB and django versions install tox
(pip install tox) and run 'tox' from the source checkout::

    $ tox

Db user 'qsstats_test' with password 'qsstats_test' and a DB 'qsstats_test'
should exist.

Difference from django-qsstats
==============================

1. Faster time_series method using 1 sql query (currently works for MySQL and
   PostgreSQL, with a fallback to the old method for other DB backends).
2. Single ``aggregates`` parameter instead of ``aggregate_field`` and
   ``aggregate_class``. Default value is always ``[Count('id')]`` and can't be
   specified in settings.py. ``QUERYSETSTATS_DEFAULT_OPERATOR`` option is also
   unsupported now.
3. Support for minute and hour aggregates.
4. ``start_date`` and ``end_date`` arguments are renamed to ``start`` and
   ``end`` because of 3.
5. Internals are changed.

I don't know if original author (Matt Croydon) would like my changes so
I renamed a project for now. If the changes will be merged then
django-qsstats-magic will become obsolete.

New in 0.8.0
============

* Changed ``aggregate`` to ``aggregates`` and now the framework returns a list of
  aggregate information instead of only one.
