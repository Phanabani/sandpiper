from decimal import Decimal as D
import logging
import re
from typing import Optional, Tuple

from pint import UndefinedUnitError, UnitRegistry, Unit
from pint.quantity import Quantity

from sandpiper.conversion.unit_map import UnitMap

__all__ = ['convert_measurement']

logger = logging.getLogger('sandpiper.conversion.unit_conversion')

ureg = UnitRegistry(
    autoconvert_offset_to_baseunit=True,  # For temperatures
    non_int_type=D
)
ureg.define(
    '@alias degreeC = c = C = degreec = degc = degC = °C = °c '
    '= Celsius = celsius'
)
ureg.define(
    '@alias degreeF = f = F = degreef = degf = degF = °F = °f '
    '= Fahrenheit = fahrenheit'
)
Q_ = ureg.Quantity

unit_map: UnitMap[Unit] = UnitMap(
    two_way={
        # Length
        ureg.km: ureg.mile,
        ureg.meter: ureg.foot,
        ureg.cm: ureg.inch,
        # Mass
        ureg.kilogram: ureg.pound,
        # Temperature
        ureg['°C'].u: ureg['°F'].u,
    },
    one_way={
        ureg.yard: ureg.meter,
    }
)

imperial_shorthand_pattern = re.compile(
    # Either feet or inches may be excluded, but not both, so make sure
    # at least one of them matches with this lookahead
    r'^(?=.)'
    # Only allow integer foot values
    r'(?:(?P<foot>[\d]+)\')?'
    r'(?:'
        # Allow a space if foot is matched
        r'(?(foot) ?|)'
        # Allow integer or decimal inch values
        r'(?P<inch>(?:\d+)|(?:\d*\.\d+))\"'
    r')?'
    r'$'
)


def convert_measurement(
        quantity_str: str, unit: str = None
) -> Optional[Tuple[Quantity, Quantity]]:
    """
    Parse and convert a quantity string between imperial and metric

    :param quantity_str: a string that may contain a quantity to be
        converted
    :return: ``None`` if the string was not a known or supported quantity,
        otherwise a tuple of original quantity and converted quantity
    """

    logger.info(f"Attempting unit conversion for {quantity_str!r}")

    if height := imperial_shorthand_pattern.match(quantity_str):
        # Added support for imperial shorthand units for length
        # e.g. 5' 8" == 5 feet + 8 inches
        logger.info('Imperial length shorthand detected')
        foot = Q_(D(foot), 'foot') if (foot := height.group('foot')) else 0
        inch = Q_(D(inch), 'inch') if (inch := height.group('inch')) else 0
        quantity = foot + inch
    else:
        # Regular parsing
        try:
            quantity = ureg.parse_expression(quantity_str)
        except UndefinedUnitError:
            logger.info('Undefined unit')
            return None

    if not isinstance(quantity, Quantity):
        logger.info('Not a quantity')
        return None

    if unit:
        conversion_unit = unit
    else:
        if quantity.units not in unit_map:
            logger.info(f"Unit not supported {quantity.units}")
            return None
        conversion_unit = unit_map[quantity.units]

    quantity_to = quantity.to(conversion_unit)
    logger.info(
        f"Conversion successful: "
        f"{quantity:.2f~P} -> {quantity_to:.2f~P}"
    )
    return quantity, quantity_to
