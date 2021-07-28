import asyncio
import datetime as dt
import logging
import random
from typing import Optional

import discord
import discord.ext.commands as commands
import discord.ext.tasks as tasks
import pytz

from sandpiper.common.time import utc_now
from sandpiper.user_data import (
    UserData, Database, PrivacyType,
    Pronouns, common_pronouns
)

__all__ = ['Birthdays']

logger = logging.getLogger('sandpiper.birthdays')


def format_birthday_message(
        msg: str,
        user_id: int,
        name: str,
        pronouns: Pronouns = common_pronouns['they'],
        age: Optional[int] = None
):
    p = pronouns

    # Generate normal (not explicitly lower), capitalized, and upper versions
    # of these args
    generate_cases = {
        'name': name,
        'they': p.subjective,
        'them': p.objective,
        'their': p.determiner,
        'theirs': p.possessive,
        'themself': p.reflexive,
        'are': p.to_be_conjugation,
        'theyre': p.subjective_to_be_contraction,
    }
    args_generated_cases = {}
    for k, v in generate_cases.items():
        args_generated_cases[k] = v
        args_generated_cases[k.capitalize()] = v.capitalize()
        args_generated_cases[k.upper()] = v.upper()

    return msg.format(
        **args_generated_cases,
        ping=f"<@{user_id}>",
        age=age
    )


class Birthdays(commands.Cog):

    def __init__(
            self, bot: commands.Bot, *, message_templates_no_age: list[str],
            message_templates_with_age: list[str]
    ):
        """Send happy birthday messages to users."""
        self.bot = bot
        self.message_templates_no_age = message_templates_no_age
        self.message_templates_with_age = message_templates_with_age
        self.tasks: dict[int, asyncio.Task] = {}
        self.first_run = True
        self.daily_loop.start()

    async def _get_database(self) -> Database:
        user_data: Optional[UserData] = self.bot.get_cog('UserData')
        if user_data is None:
            raise RuntimeError('UserData cog is not loaded.')
        return await user_data.get_database()

    async def _try_cancel_task(self, user_id):
        if user_id in self.tasks:
            logger.info(
                f"Canceling birthday notification task (user={user_id})"
            )
            self.tasks[user_id].cancel()
            del self.tasks[user_id]

    def _get_random_message(self, age=False):
        if age:
            return random.choice(self.message_templates_with_age)
        return random.choice(self.message_templates_no_age)

    @tasks.loop(hours=24)
    async def daily_loop(self):
        # If this is the first run of the loop, it's possible some birthday
        # notifs had been sent in a past Sandpiper runtime, so we will skip
        # them in schedule_todays_birthdays. Otherwise, we can reset all
        # birthday notif sent flags to False since it's a new day.
        if not self.first_run:
            db = await self._get_database()
            await db.reset_all_birthday_notification_sent()

        await self.schedule_todays_birthdays()
        self.first_run = False

    @daily_loop.error
    async def daily_loop_error(self, exc: Exception):
        logger.error("Unhandled exception in daily_loop task", exc_info=exc)

    async def schedule_todays_birthdays(self):
        """
        Gets all birthdays occurring either today or tomorrow and then tries
        to schedule each of them. Only birthdays occurring within the next 24
        hours will be scheduled.
        """
        db = await self._get_database()
        now = utc_now()
        today = now.date()

        # Get all birthdays occurring today or tomorrow which haven't been
        # marked as sent yet and schedule them (those occurring tomorrow will
        # be filtered out)
        # The marked as sent thing is used in case Sandpiper restarts mid-day
        # so she can continue sending bday notifs properly without any repeats
        scheduled_count = 0
        birthdays_today_tomorrow = await db.get_birthdays_range(
            today, today + dt.timedelta(days=1),
            only_if_notification_not_sent=True
        )
        for user_id, birthday in birthdays_today_tomorrow:
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

        # Cancel and remove the user's birthday task if it already exists.
        # This may happen if the user changes their timezone or something
        # when their birthday task is already scheduled.
        # We want to overwrite it.
        await self._try_cancel_task(user_id)

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
            f"Waiting to send birthday message (user={user_id} "
            f"seconds={delta.total_seconds()})"
        )
        await asyncio.sleep(delta.total_seconds())

        logger.info(
            f"Sending birthday notifications for user (user={user_id})"
        )
        db = await self._get_database()
        user: discord.User = self.bot.get_user(user_id)
        if user is None:
            logger.info(
                f"Tried to send birthday message, but user is not in any "
                f"guilds with Sandpiper (user={user_id})"
            )
            return
        guilds: list[discord.Guild] = user.mutual_guilds

        # Get some user info to use in the message

        name = None
        if (await db.get_privacy_preferred_name(user_id)) is PrivacyType.PUBLIC:
            name = await db.get_preferred_name(user_id)
        has_preferred_name = name is not None

        age = None
        if (await db.get_privacy_age(user_id)) is PrivacyType.PUBLIC:
            age = await db.get_age(user_id)

        # Send the message to each guild they're in with Sandpiper

        for guild in guilds:
            member: discord.Member = guild.get_member(user_id)
            if member is None:
                logger.debug(
                    f"User not found as a member in the guild while trying to "
                    f"send birthday message, this is most likely a rare race "
                    f"condition (user={user_id} guild={guild.id})"
                )
                continue

            bday_channel_id = await db.get_guild_birthday_channel(guild.id)
            if bday_channel_id is None:
                continue

            bday_channel: discord.TextChannel
            bday_channel = self.bot.get_channel(bday_channel_id)
            if bday_channel is None:
                logger.debug(
                    f"Birthday channel does not exist (guild={guild.id} "
                    f"channel={bday_channel_id})"
                )
                continue

            if not has_preferred_name:
                name = member.display_name

            bday_msg_template = self._get_random_message(age=age is not None)
            bday_msg = format_birthday_message(
                bday_msg_template, user_id=user_id, name=name, age=age
            )
            await bday_channel.send(bday_msg)

        await db.set_birthday_notification_sent(user_id, True)

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

    async def notify_change(self, user_id: int):
        """
        This method should be called when any one of the following user data
        change, as birthday scheduling updates may need to be made:
            - birthday
            - timezone
            - birthday privacy
            - timezone privacy
        """
        db = await self._get_database()
        birthday = await db.get_birthday(user_id)
        birthday_privacy = await db.get_privacy_birthday(user_id)

        # Either of these two conditions means the birthday must be canceled
        # and we will not reschedule
        if (
                birthday is None
                or birthday_privacy is PrivacyType.PRIVATE
        ):
            await self._try_cancel_task(user_id)
            return

        await self.schedule_birthday(user_id, birthday)
