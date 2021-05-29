import asyncio
import datetime as dt
import logging
from typing import Optional

import discord.ext.commands as commands
import discord.ext.tasks as tasks
import pytz

from sandpiper.common.time import utc_now
from sandpiper.user_data import UserData
from sandpiper.user_data.database import Database
from sandpiper.user_data.enums import PrivacyType

__all__ = ['Birthdays']

logger = logging.getLogger('sandpiper.birthdays')


class Birthdays(commands.Cog):

    def __init__(
            self, bot: commands.Bot, *, past_birthdays_day_range: int = 7,
            upcoming_birthdays_day_range: int = 14
    ):
        self.bot = bot
        self.past_birthdays_day_range = past_birthdays_day_range
        self.upcoming_birthdays_day_range = upcoming_birthdays_day_range
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
        db = await self._get_database()
        now = utc_now()
        today = now.date()

        for user_id, birthday in await db.get_birthdays_range(
                today, today + dt.timedelta(days=1)
        ):
            await self.schedule_birthday(user_id, birthday, now=now)

    async def schedule_birthday(
            self, user_id: int, birthday: dt.date,
            *, now: Optional[dt.datetime] = None
    ):
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
            await self.bot.loop.create_task(
                self.send_birthday_message(user_id, midnight_delta)
            )

    async def send_birthday_message(self, user_id: int, delta: dt.timedelta):
        await asyncio.sleep(delta.total_seconds())
        # send message here

    async def get_past_upcoming_birthdays(self) -> tuple[list, list]:
        db = await self._get_database()
        now = utc_now()
        today = now.date()
        past_delta = dt.timedelta(days=self.past_birthdays_day_range)
        upcoming_delta = dt.timedelta(days=self.upcoming_birthdays_day_range)
        past_birthdays = await db.get_birthdays_range(
            today - past_delta, today
        )
        upcoming_birthdays = await db.get_birthdays_range(
            today + dt.timedelta(days=1), today + upcoming_delta
        )
        return past_birthdays, upcoming_birthdays
