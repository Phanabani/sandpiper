import asyncio
import datetime as dt
import logging
from typing import Optional

import discord
import discord.ext.commands as commands
import discord.ext.tasks as tasks
import pytz

from sandpiper.common.time import utc_now
from sandpiper.user_data import UserData, Database, PrivacyType

__all__ = ['Birthdays']

logger = logging.getLogger('sandpiper.birthdays')


class Birthdays(commands.Cog):

    def __init__(self, bot: commands.Bot):
        """ Send happy birthday messages to users. """
        self.bot = bot
        self.tasks: dict[int, asyncio.Task] = {}
        self.daily_loop.start()

    async def _get_database(self) -> Database:
        user_data: Optional[UserData] = self.bot.get_cog('UserData')
        if user_data is None:
            raise RuntimeError('UserData cog is not loaded.')
        return await user_data.get_database()

    @tasks.loop(hours=24)
    async def daily_loop(self):
        await self.schedule_todays_birthdays()

    async def schedule_todays_birthdays(self):
        """
        Gets all birthdays occurring either today or tomorrow and then tries
        to schedule each of them. Only birthdays occurring within the next 24
        hours will be scheduled.
        """
        db = await self._get_database()
        now = utc_now()
        today = now.date()

        scheduled_count = 0
        for user_id, birthday in await db.get_birthdays_range(
                today, today + dt.timedelta(days=1)
        ):
            if await self.schedule_birthday(user_id, birthday, now=now):
                scheduled_count += 1
        logger.info(f"{scheduled_count} birthdays scheduled for today")

    async def schedule_birthday(
            self, user_id: int, birthday: dt.date,
            *, now: Optional[dt.datetime] = None
    ) -> bool:
        """
        Schedule a task that will wish this user happy birthday if their
        birthday is within the next 24 hours. Will try to access their timezone
        to wish them happy birthday at midnight in their timezone.

        :param user_id: the user's Discord ID
        :param birthday: the user's birthday
        :param now: The datetime to use for calculating if the birthday occurs
            within the next 24 hours. This is important when several birthdays
            are being scheduled in a loop to prevent a possible race condition.
        :return: whether the birthday was scheduled
        """
        db = await self._get_database()

        if now is None:
            now = utc_now()
        today = now.date()

        timezone = None
        if await db.get_privacy_timezone(user_id) is PrivacyType.PUBLIC:
            timezone = await db.get_timezone(user_id)
        if timezone is None:
            # If the user's timezone is null, just use UTC
            timezone = pytz.UTC

        # Determine midnight in this person's timezone so we can
        # wish them happy birthday at the start of their day
        midnight_local: dt.datetime = timezone.localize(
            dt.datetime(today.year, birthday.month, birthday.day)
        )
        midnight_utc = midnight_local.astimezone(pytz.UTC)
        midnight_delta = midnight_utc - now
        # Only schedule the birthday task if their localized midnight is
        # within 24 hours from now
        # TODO I'm worried that it could be possible we lose a birthday
        #   in a race condition here...
        if dt.timedelta(0) < midnight_delta <= dt.timedelta(hours=24):
            self.tasks[user_id] = self.bot.loop.create_task(
                self.send_birthday_message(user_id, midnight_delta)
            )
            return True
        return False

    async def send_birthday_message(self, user_id: int, delta: dt.timedelta):
        """
        Wait for `delta` time and then send a message wishing the user a happy
        birthday in all guilds they share with Sandpiper.

        :param user_id: the user's Discord ID
        :param delta: how long to wait before sending the message
        :return:
        """
        logger.info(
            f"Waiting to send birthday message (user_id={user_id} "
            f"seconds={delta.total_seconds()})"
        )

        await asyncio.sleep(delta.total_seconds())

        logger.info(
            f"Sending birthday notifications for user (user_id={user_id})"
        )
        db = await self._get_database()
        user: discord.User = self.bot.get_user(user_id)
        if user is None:
            logger.info(
                f"Tried to send birthday message, but user is not in any "
                f"guilds with Sandpiper (user_id={user_id})"
            )
            return
        guilds: list[discord.Guild] = user.mutual_guilds

        for guild in guilds:
            bday_channel_id = await db.get_guild_birthday_channel(guild.id)
            if bday_channel_id is None:
                continue

            bday_channel: discord.TextChannel = self.bot.get_channel(bday_channel_id)
            if bday_channel is None:
                continue

            await bday_channel.send(f"it's {user.name}'s birthday!")

    async def get_past_upcoming_birthdays(
            self, past_birthdays_day_range: int = 7,
            upcoming_birthdays_day_range: int = 14
    ) -> tuple[list, list]:
        """
        Get two lists of past and upcoming birthdays. This may be used in a
        user command to see who's having a birthday soon.

        :param past_birthdays_day_range: how many days to search backward for
            past birthdays
        :param upcoming_birthdays_day_range: how many days to search forward
            for upcoming birthdays
        """
        db = await self._get_database()
        now = utc_now()
        today = now.date()
        past_delta = dt.timedelta(days=past_birthdays_day_range)
        upcoming_delta = dt.timedelta(days=upcoming_birthdays_day_range)
        past_birthdays = await db.get_birthdays_range(
            today - past_delta, today
        )
        upcoming_birthdays = await db.get_birthdays_range(
            today + dt.timedelta(days=1), today + upcoming_delta
        )
        return past_birthdays, upcoming_birthdays
