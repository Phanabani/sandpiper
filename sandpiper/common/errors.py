import logging

import discord
import discord.ext.commands as commands

logger = logging.getLogger('sandpiper.common.errors')


class UserFeedbackError(Exception):
    pass


class ErrorMessages:

    default_msg = 'Unexpected error.'

    @classmethod
    def _get(cls, error: Exception = None):
        if error is None:
            return cls.default_msg
        if isinstance(error, UserFeedbackError):
            return str(error)
        if isinstance(error, commands.PrivateMessageOnly):
            return 'For your privacy, DM me to use this command.'
        return None

    @classmethod
    def get(cls, error: Exception = None):
        msg = cls._get(error)
        if msg is None:
            logger.error(f'Unexpected error {error}', exc_info=False)
            return cls.default_msg
        return msg
