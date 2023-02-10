from __future__ import annotations

__all__ = ["MissingComponentError", "Component"]

import abc
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sandpiper import Sandpiper

logger = logging.getLogger(__name__)


class MissingComponentError(Exception):
    def __init__(self, component_name: str, extra_info: str = ""):
        self.component_name = component_name
        self.extra_info = extra_info

    def __str__(self):
        extra_info = self.extra_info
        if extra_info:
            extra_info = f"; {extra_info}"
        return f"Failed to get the {self.component_name} component{extra_info}"


class Component(abc.ABC):
    def __init__(self, sandpiper: Sandpiper):
        self.sandpiper = sandpiper

    async def setup(self):
        pass

    async def teardown(self):
        pass
