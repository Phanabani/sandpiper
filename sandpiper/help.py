import itertools
from typing import *

from discord.ext.commands import DefaultHelpCommand, Group, Command

__all__ = ['HelpCommand']


def sort_commands_key(c: Command):
    try:
        return c.__original_kwargs__['order']
    except KeyError:
        return c.name


def sort_commands(commands: Iterable[Command]):
    return sorted(commands, key=sort_commands_key)


def boxify(inside: str):
    line = '─' * (len(inside) + 2)
    top = f'╭{line}╮'
    bot = f'╰{line}╯'
    return f"{top}\n│ {inside} │\n{bot}"


class HelpCommand(DefaultHelpCommand):

    def __init__(self, **kwargs):
        kwargs.pop('indent', None)
        super().__init__(indent=3, **kwargs)

    def get_ending_note(self):
        command_name = self.invoked_with
        return (
            f"Type {self.clean_prefix}{command_name} <command> for more info "
            f"on a command."
        )

    def add_commands_recursive(self, commands: Iterable[Command], depth=0):
        indent = ' ' * max(0, self.indent * (depth - 1))

        commands = list(commands)
        for i, c in enumerate(sort_commands(commands)):
            if depth != 0:
                if i == len(commands) - 1:
                    connector = '└─ '
                else:
                    connector = '├─ '
            else:
                connector = ''
            self.paginator.add_line(
                f"{indent}{connector}{c.name} \N{EN DASH} {c.short_doc}")
            if isinstance(c, Group):
                self.add_commands_recursive(c.commands, depth+1)
                self.paginator.add_line()

    async def send_bot_help(self, mapping):
        ctx = self.context
        bot = ctx.bot

        if bot.description:
            # <description> portion
            self.paginator.add_line(bot.description)

        def get_category(command) -> str:
            cog = command.cog
            return cog.qualified_name if cog is not None else self.no_category

        filtered = await self.filter_commands(bot.commands, sort=True,
                                              key=get_category)
        to_iterate = itertools.groupby(filtered, key=get_category)

        # Now we can add the commands to the page.
        for category, commands in to_iterate:
            self.paginator.add_line()
            self.paginator.add_line(boxify(category))
            self.add_commands_recursive(commands)

        note = self.get_ending_note()
        if note:
            self.paginator.add_line()
            self.paginator.add_line(note)

        await self.send_pages()
