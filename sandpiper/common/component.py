import abc
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sandpiper import Sandpiper


class Component(abc.ABC):
    def __init__(self, sandpiper: Sandpiper):
        self.sandpiper = sandpiper

    @abc.abstractmethod
    async def setup(self):
        pass

    @abc.abstractmethod
    async def teardown(self):
        pass
