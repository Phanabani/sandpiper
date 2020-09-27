import logging
import re
from typing import Optional, Tuple, cast

from bidict import bidict as bidict_base
import discord
from pint import UnitRegistry
from pint.quantity import Quantity as Q_
from pint.errors import UndefinedUnitError

logger = logging.getLogger(__name__)
ureg = UnitRegistry(autoconvert_offset_to_baseunit=True)  # For temperatures
ureg.define('@alias degreeC = c = C = degreec = degc = degC')
ureg.define('@alias degreeF = f = F = degreef = degf = degF')


# noinspection PyPep8Naming
class bidict(bidict_base):

    def __contains__(self, item):
        return (super(bidict, self).__contains__(item)
                or super(bidict, self.inverse).__contains__(item))

    # noinspection PyArgumentList
    def __getitem__(self, item):
        try:
            return super(bidict, self).__getitem__(item)
        except KeyError:
            return super(bidict, self.inverse).__getitem__(item)


# noinspection PyMethodMayBeStatic
class Sandpiper(discord.Client):

    quantity_pattern = re.compile(r'{(.+?)}')
    imperial_height_pattern = re.compile(
        r'^(?=.)(?:(?P<foot>[\d]+)\')?(?:(?(foot) |)(?P<inch>[\d.]+)\")?$')
    unit_map = bidict({
        # Length
        ureg.km: ureg.mile,
        ureg.meter: ureg.foot,
        ureg.cm: ureg.inch,
        # Mass
        ureg.kilogram: ureg.pound,
        # Temperature
        ureg['°C'].u: ureg['°F'].u
    })

    async def on_ready(self):
        logger.info('Sandpiper client started')

    async def on_message(self, msg: discord.Message):
        guild: discord.Guild = msg.guild
        channel: discord.TextChannel = msg.channel
        perms = channel.permissions_for(guild.me)
        if not perms.send_messages:
            return

        await self.mentioned_me(msg)
        await self.unit_conversions(msg)

    async def mentioned_me(self, msg):
        """
        What to do when a user mentions me

        :param msg: message with self mention
        :return: ``False`` if not mentioned
        """

        if self.user not in msg.mentions:
            return False

        await msg.channel.send('hi :)')

    async def unit_conversions(self, msg: discord.Message):
        """
        Scan a message for quantities like {5 km}, and reply with their
        conversions to either imperial or metric.

        :param msg: discord message to scan for quantities
        :return: ``False`` if no quantities were found
        """

        quantity_strs = self.quantity_pattern.findall(msg.content)
        if not quantity_strs:
            return False
        quantities = [q for qstr in quantity_strs
                      if (q := self.convert(qstr)) is not None]
        # I'm not specifying a precision here for the input because it will
        # often be an integer, and will raise a ValueError if I try to format
        # its precision
        conversion = '\n'.join([f'{q[0]:~P} = {q[1]:.2f~P}'
                                for q in quantities])
        if not conversion:
            return

        try:
            await msg.channel.send(conversion)
        except discord.HTTPException as e:
            logger.warning('when sending conversion embed: ', exc_info=e)
        except discord.InvalidArgument as e:
            logger.error('when sending conversion embed:', exc_info=e)

    def convert(self, quantity_str: str) -> Optional[Tuple[Q_, Q_]]:
        """
        Parse and convert a quantity string between imperial and metric

        :param quantity_str: a string that may contain a quantity to be
            converted
        :return: ``None`` if the string was not a known or supported quantity,
        """

        if (height := self.imperial_height_pattern.match(quantity_str)):
            foot = (ureg.Quantity(int(foot), 'foot')
                    if (foot := height.group('foot')) else 0)
            inch = (ureg.Quantity(float(inch), 'inch')
                    if (inch := height.group('inch')) else 0)
            quantity = foot + inch
        else:
            quantity = ureg.parse_expression(quantity_str)

        if not isinstance(quantity, Q_) or quantity.u not in self.unit_map:
            return None
        conversion_unit = self.unit_map[quantity.u]

        return quantity, quantity.to(conversion_unit)


if __name__ == '__main__':
    import json
    from pathlib import Path
    import sys

    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    with Path(__file__, '../config.json').open() as f:
        config = json.load(f)

    sandpiper = Sandpiper()
    sandpiper.run(config['bot_token'])
