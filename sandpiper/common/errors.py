import logging

import discord
import discord.ext.commands as commands

logger = logging.getLogger('sandpiper.common.errors')


class UserFeedbackError(Exception):
    pass


class ErrorMessages:

    default_msg = 'Unexpected error.'
    boolean_true = ('yes', 'y', 'true', 't', '1', 'enable', 'on')
    boolean_false = ('no', 'n', 'false', 'f', '0', 'disable', 'off')

    @classmethod
    def _get(cls, error: Exception = None):
        if error is None:
            return cls.default_msg
        if isinstance(error, UserFeedbackError):
            return str(error)
        if isinstance(error, commands.PrivateMessageOnly):
            return 'For your privacy, DM me to use this command.'

        # BadArgument subclasses
        if isinstance(error, commands.MessageNotFound):
            return 'Message was not found.'
        if isinstance(error, commands.MemberNotFound):
            return f'Member ({error.argument}) was not found.'
        if isinstance(error, commands.UserNotFound):
            return f'User ({error.argument}) was not found.'
        if isinstance(error, commands.ChannelNotFound):
            return f'Channel ({error.argument}) was not found.'
        if isinstance(error, commands.ChannelNotReadable):
            return f'Channel ({error.argument}) is not readable.'
        if isinstance(error, commands.RoleNotFound):
            return f'Role {error.argument} was not found.'
        if isinstance(error, commands.EmojiNotFound):
            return f'Emoji ({error.argument}) was not found.'
        if isinstance(error, commands.PartialEmojiConversionFailure):
            return f'Emoji ({error.argument}) does not match correct format.'
        if isinstance(error, commands.BadBoolArgument):
            return (f'Value should be one of {cls.boolean_true!r} or '
                    f'{cls.boolean_false!r}.')
        # CheckFailure subclasses
        if isinstance(error, commands.MissingPermissions):
            return f'Missing permissions {error.missing_perms}.'
        if isinstance(error, commands.BotMissingPermissions):
            return f'Missing permissions {error.missing_perms}.'
        if isinstance(error, commands.MissingRole):
            return f'Missing permissions {error.missing_role!r}.'
        if isinstance(error, commands.BotMissingRole):
            return f'Missing permissions {error.missing_role!r}.'

        return None

    @classmethod
    def get(cls, error: Exception = None):
        msg = cls._get(error)
        if msg is None:
            logger.error(f'Unexpected error {error}', exc_info=False)
            return cls.default_msg
        return msg
