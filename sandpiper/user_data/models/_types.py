import sqlalchemy.types as types

__all__ = ["Snowflake"]


class Snowflake(types.TypeDecorator):
    """
    SQLite only stores (signed) int64, so we need to coerce Snowflakes to
    strings for storage.

    20 == the number of digits in (1<<64) - 1
    """

    impl = types.String(20)

    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return int(value)
