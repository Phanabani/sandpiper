from discord.abc import Snowflake
from phanas_pydantic_helpers import FieldConverter


class SnowflakeImpl(Snowflake):
    def __init__(self, id: int):
        self.id = id


class SnowflakeField(SnowflakeImpl, FieldConverter):
    @classmethod
    def _pyd_convert(cls, id: int):
        return cls(id)
