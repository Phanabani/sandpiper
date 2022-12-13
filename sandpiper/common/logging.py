__all__ = ["warn_component_none"]

from logging import Logger


def warn_component_none(
    logger: Logger, component_name: str, extra_info: str = ""
) -> None:
    if extra_info:
        extra_info = f"; {extra_info}"
    logger.warning(f"Failed to get the {component_name} component{extra_info}")
