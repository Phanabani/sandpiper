from datetime import date
from typing import List, Tuple

import discord
from discord.ext.commands import BadArgument

from sandpiper.user_data.enums import PrivacyType

__all__ = ['date_handler', 'privacy_handler', 'find_user_in_mutual_guilds',
           'find_users_by_display_name', 'find_users_by_username']


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


def find_users_by_username(client: discord.Client,
                           name: str) -> [List[Tuple[int, str]]]:
    users = []
    name = name.casefold()
    for user in client.users:
        user: discord.User
        if name in user.name.casefold():
            users.append((user.id, f'{user.name}#{user.discriminator}'))
    return users


def find_users_by_display_name(client: discord.Client, whos_looking: int,
                               name: str) -> [List[Tuple[int, str]]]:
    users = []
    name = name.casefold()
    for g in client.guilds:
        g: discord.Guild
        if g.get_member(whos_looking):
            for member in g.members:
                member: discord.Member
                if name in member.display_name.casefold():
                    users.append((member.id, member.display_name))
    return users
