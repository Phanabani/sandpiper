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

    def get_ending_note(self):
        command_name = self.invoked_with
        return (
            f"Type {self.clean_prefix}{command_name} <command> for more info "
            f"on a command."
        )

    def add_commands_recursive(self, commands: Iterable[Command],
                               depth=0, vertical_connectors='',
                               *, parent_path: str = None):
        if parent_path:
            # Print the nodes of this branch leading from the root to the
            # current command
            parent_path = parent_path.split(' ')
            depth = len(parent_path)
            for i, parent in enumerate(parent_path):
                if i == 0:
                    self.paginator.add_line(parent)
                else:
                    self.paginator.add_line(f"{vertical_connectors}└─ {parent}")
                    vertical_connectors += '   '

        commands = list(commands)
        for i, c in enumerate(sort_commands(commands)):
            if depth != 0:
                if i == len(commands) - 1:
                    # Last item; terminate this level of the tree
                    horizontal_connector = '└─ '
                    next_vertical = vertical_connectors + '   '
                else:
                    # Continue this level of the tree
                    horizontal_connector = '├─ '
                    next_vertical = vertical_connectors + '│  '
            else:
                # Don't print connectors for the top level of the tree
                horizontal_connector = next_vertical = ''

            line = (f"{vertical_connectors}{horizontal_connector}"
                    f"{c.name} \N{EN DASH} {c.short_doc}")
            self.paginator.add_line(self.shorten_text(line))

            if isinstance(c, Group):
                self.add_commands_recursive(c.commands, depth+1, next_vertical)
                if depth == 0:
                    # Add line breaks after first-level groups
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

    async def send_group_help(self, group):
        self.add_command_formatting(group)

        filtered = await self.filter_commands(group.commands)
        self.add_commands_recursive(filtered, parent_path=group.qualified_name)

        if filtered:
            note = self.get_ending_note()
            if note:
                self.paginator.add_line()
                self.paginator.add_line(note)

        await self.send_pages()

    def add_command_formatting(self, command):
        super().add_command_formatting(command)

        try:
            example = command.__original_kwargs__['example']
        except KeyError:
            pass
        else:
            if isinstance(example, str):
                self.paginator.add_line(f"Example: {example}")
            elif isinstance(example, (list, tuple)):
                self.paginator.add_line('Examples:')
                for ex in example:
                    self.paginator.add_line(f"  {ex}")
