import warnings

__all__ = [
    "DateFieldMissingError",
    "InvalidIntervalError",
    "InvalidOperatorError",
    "QuerySetMissingError",
    "QuerySetStatsError",
]


class QuerySetStatsError(Exception):
    pass


class InvalidIntervalError(QuerySetStatsError):
    pass


class InvalidOperatorError(QuerySetStatsError):
    pass


class DateFieldMissingError(QuerySetStatsError):
    pass


class QuerySetMissingError(QuerySetStatsError):
    pass


# Deprecated aliases, kept for backwards compatibility.
# TODO: remove in the next major release.
_DEPRECATED_ALIASES = {
    "InvalidInterval": "InvalidIntervalError",
    "InvalidOperator": "InvalidOperatorError",
    "DateFieldMissing": "DateFieldMissingError",
    "QuerySetMissing": "QuerySetMissingError",
}


def __getattr__(name):
    new_name = _DEPRECATED_ALIASES.get(name)
    if new_name is None:
        msg = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(msg)
    warnings.warn(
        f"qsstats.exceptions.{name} is deprecated and will be removed in a "
        f"future release, use {new_name} instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return globals()[new_name]
