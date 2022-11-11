from typing import NoReturn, Union
from unittest import mock

import discord

from .misc import assert_in, assert_one_if_list

__all__ = [
    "get_contents",
    "get_embeds",
    "assert_success",
    "assert_warning",
    "assert_error",
    "assert_info",
    "assert_no_reply",
]

# region Misc helper functions


def get_contents(mock_: mock.Mock) -> list[str]:
    """
    :param mock_: a mock ``send`` method
    :return: a list of each message's contents
    """
    # noinspection PyUnboundLocalVariable
    return [
        content
        for call in mock_.call_args_list
        if len(call.args) > 0 and (content := call.args[0]) is not None
    ]


def get_embeds(mock_: mock.Mock) -> list[discord.Embed]:
    """
    :param mock_: a mock ``send`` method
    :return: a list of embeds sent in each message
    """
    return [
        embed for call in mock_.call_args_list if (embed := call.kwargs.get("embed"))
    ]


# endregion

# region Embed assertions


def assert_success(embed: Union[discord.Embed, list[discord.Embed]], *substrings: str):
    """
    Assert ``embed`` is a success embed and that its description contains
    each substring in ``substrings``.
    """
    __tracebackhide__ = True
    embed = assert_one_if_list(embed)
    assert "Success" in embed.title
    assert_in(embed.description, *substrings)


def assert_warning(embed: Union[discord.Embed, list[discord.Embed]], *substrings: str):
    """
    Assert ``embed`` is a warning embed and that its description contains
    each substring in ``substrings``.
    """
    __tracebackhide__ = True
    embed = assert_one_if_list(embed)
    assert "Warning" in embed.title
    assert_in(embed.description, *substrings)


def assert_error(embed: Union[discord.Embed, list[discord.Embed]], *substrings: str):
    """
    Assert ``embed`` is an error embed and that its description contains
    each substring in ``substrings``.
    """
    __tracebackhide__ = True
    embed = assert_one_if_list(embed)
    assert "Error" in embed.title
    assert_in(embed.description, *substrings)


def assert_info(embed: Union[discord.Embed, list[discord.Embed]], *substrings: str):
    """
    Assert ``embed`` is an info embed and that its description contains
    each substring in ``substrings``.
    """
    __tracebackhide__ = True
    embed = assert_one_if_list(embed)
    assert "Info" in embed.title
    assert_in(embed.description, *substrings)


# endregion


def assert_no_reply(send: mock.Mock) -> NoReturn:
    """Assert that the bot didn't reply with the `send` mock."""
    __tracebackhide__ = True
    assert not send.called, "Bot replied when it shouldn't have"
