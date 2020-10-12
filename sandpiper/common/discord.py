from datetime import date
from typing import List

import discord
from discord.ext.commands import BadArgument

from sandpiper.user_info.enums import PrivacyType

__all__ = ['date_handler', 'privacy_handler', 'find_user_in_mutual_guilds']


def date_handler(date_str: str) -> date:
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise BadArgument(
            'Use date format YYYY-MM-DD (example: 1997-08-27)')


def privacy_handler(privacy_str: str) -> PrivacyType:
    privacy_str = privacy_str.upper()
    try:
        return PrivacyType[privacy_str]
    except KeyError:
        privacy_names = [n.lower() for n in PrivacyType.__members__.keys()]
        raise BadArgument(f'Privacy must be one of {privacy_names}')


def find_user_in_mutual_guilds(client: discord.Client, whos_looking: int,
                               for_whom: int) -> List[discord.Member]:
    found_members = []
    for g in client.guilds:
        g: discord.Guild
        if g.get_member(whos_looking):
            member = g.get_member(for_whom)
            if member:
                found_members.append(member)
    return found_members
