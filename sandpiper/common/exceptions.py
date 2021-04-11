from typing import *

__all__ = ('AggregateException',)


class AggregateException(Exception):

    __slots__ = ('exceptions',)

    exceptions: List[Exception]

    def __init__(self):
        self.exceptions = []

    def __bool__(self):
        return len(self.exceptions) != 0

    def __contains__(self, instance_or_type: Union[Exception, Type]):
        if isinstance(instance_or_type, Exception):
            return instance_or_type in self.exceptions
        if isinstance(instance_or_type, type):
            for i in self.exceptions:
                if isinstance(i, instance_or_type):
                    return True
        return False

    def __iadd__(self, exc: Exception):
        self.exceptions.append(exc)
        return self

    def __iter__(self):
        return iter(self.exceptions)
