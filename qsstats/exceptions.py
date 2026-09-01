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
