from decimal import Decimal as D
import logging
import re
from typing import *

from pint import UndefinedUnitError as PintUndefinedUnitError
from pint import UnitRegistry, Unit
from pint.quantity import Quantity

from sandpiper.common.misc import RuntimeMessages
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
        # Area
        ureg.hectare: ureg.acre,
        # Speed
        ureg.kilometer_per_hour: ureg.mile_per_hour,
        # Mass
        ureg.gram: ureg.ounce,
        ureg.kilogram: ureg.pound,
        # Volume
        ureg.liter: ureg.gallon,
        ureg.milliliter: ureg.cup,
        # Pressure
        ureg.pascal: ureg.pound_force_per_square_inch,
        # Temperature
        ureg.celsius: ureg.fahrenheit,
        # Energy
        ureg.joule: ureg.foot_pound,
        # Angle
        ureg.radian: ureg.degree,
    },
    one_way={
        # Length
        ureg.yard: ureg.meter,
        # Speed
        ureg.meter_per_second: ureg.kilometer_per_hour,
        ureg.foot_per_second: ureg.mile_per_hour,
        # Mass
        ureg.stone: ureg.kilogram,
        # Volume
        ureg.pint: ureg.liter,
        ureg.fluid_ounce: ureg.milliliter,
        # Pressure
        # These two are both derived from pascals, so I think these one-way
        # mappings are reasonable
        ureg.atmosphere: ureg.pound_force_per_square_inch,
        ureg.bar: ureg.pound_force_per_square_inch,
        # Temperature
        ureg.kelvin: ureg.celsius,
        # Time
        ureg.second: ureg.minute,
        ureg.minute: ureg.hour,
        ureg.hour: ureg.day,
        ureg.day: ureg.week,
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
        r'(?P<inch>\d+|\d*\.\d+)\"'
    r')?'
    r'$'
)


class UndefinedUnitError(Exception):

    def __init__(self, unit: str):
        self.unit = unit

    def __str__(self):
        return f"Unknown unit \"{self.unit}\""


class NotAMeasurementError(Exception):

    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return f"\"{self.value}\" is not a measurement"


class UnmappedUnitError(Exception):

    def __init__(self, quantity: Quantity):
        self.quantity = quantity

    def __str__(self):
        return (
            f"I don't know what unit to convert \"{self.quantity.u}\" to. You "
            f"can specify an output unit like this: "
            f"{{{self.quantity} > otherunit}}"
        )


def convert_measurement(
        quantity_str: str, unit: str = None,
        *, runtime_msgs: RuntimeMessages = None
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
        # User used imperial length shorthand
        # e.g. 5' 8" == 5 feet + 8 inches
        logger.info('Imperial length shorthand detected')
        foot = Q_(D(foot), 'foot') if (foot := height['foot']) else 0
        inch = Q_(D(inch), 'inch') if (inch := height['inch']) else 0
        quantity: Quantity = foot + inch
    else:
        # Regular parsing
        try:
            quantity = ureg.parse_expression(quantity_str)
        except PintUndefinedUnitError as e:
            unit = e.args[0]
            logger.info(f"Undefined unit {unit}")
            if runtime_msgs is not None:
                runtime_msgs += UndefinedUnitError(unit)
            return None

    if not isinstance(quantity, Quantity):
        # quantity_str can be parsed as an int
        logger.info(f"Not a quantity ({type(quantity)})")
        if runtime_msgs is not None:
            runtime_msgs += NotAMeasurementError(quantity_str)
        return None

    if unit:
        # User specified an output unit
        unit_out = unit
    else:
        # Try getting the output unit from the unit map
        if quantity.u not in unit_map:
            logger.info(f"Unit not mapped {quantity.u}")
            if runtime_msgs is not None:
                runtime_msgs += UnmappedUnitError(quantity)
            return None
        unit_out = unit_map[quantity.u]

    try:
        # Convert to output unit
        quantity_out = quantity.to(unit_out)
    except PintUndefinedUnitError as e:
        # User specified an undefined output unit
        unit = e.args[0]
        logger.info(f"Undefined unit {unit}")
        if runtime_msgs is not None:
            runtime_msgs += UndefinedUnitError(unit)
        return None

    logger.info(
        f"Conversion successful: "
        f"{quantity:.2f~P} -> {quantity_out:.2f~P}"
    )
    return quantity, quantity_out
