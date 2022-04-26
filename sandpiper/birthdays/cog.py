import asyncio
import datetime as dt
import logging
import random
from typing import Optional

import discord
import discord.ext.commands as commands
import discord.ext.tasks as tasks
import pytz

from sandpiper.common.discord import AutoOrder, cheap_user_hash
from sandpiper.common.time import sort_dates_no_year, utc_now
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
            message_templates_with_age: list[str],
            past_birthdays_day_range: int,
            upcoming_birthdays_day_range: int
    ):
        """Send happy birthday messages to users."""
        self.bot = bot
        self.message_templates_no_age = message_templates_no_age
        self.message_templates_with_age = message_templates_with_age
        self.past_birthdays_day_range = past_birthdays_day_range
        self.upcoming_birthdays_day_range = upcoming_birthdays_day_range
        self.tasks: dict[int, asyncio.Task] = {}
        asyncio.run_coroutine_threadsafe(self.init_daily_loop(), self.bot.loop)

    def _create_birthday_task(self, user_id: int, midnight_delta: dt.timedelta):
        self.tasks[user_id] = task = self.bot.loop.create_task(
            self.send_birthday_message(user_id, midnight_delta)
        )
        task.add_done_callback(self._handle_task_exception)

    async def _get_database(self) -> Database:
        user_data: Optional[UserData] = self.bot.get_cog('UserData')
        if user_data is None:
            raise RuntimeError('UserData cog is not loaded.')
        return await user_data.get_database()

    def _get_random_message(self, age=False):
        if age:
            return random.choice(self.message_templates_with_age)
        return random.choice(self.message_templates_no_age)

    def _handle_task_exception(self, task: asyncio.Task) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            pass  # Task cancellation should not be logged as an error.
        except Exception as e:
            logger.error(f"Exception raised by task {task}", exc_info=e)

    async def _try_cancel_task(self, user_id):
        if user_id in self.tasks:
            logger.info(
                f"Canceling birthday notification task (user={user_id})"
            )
            self.tasks[user_id].cancel()
            del self.tasks[user_id]

    async def init_daily_loop(self):
        await self.bot.wait_until_ready()
        self.daily_loop.start()

    @tasks.loop(hours=24)
    async def daily_loop(self):
        await self.schedule_todays_birthdays()

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

        # Get all birthdays occurring yesterday, today, or tomorrow. This is
        # necessary bc today's date will stretch across at least 2 days
        # (relative to UTC, ahead or behind) when every timezone is taken into
        # account
        scheduled_count = 0
        birthdays_today_tomorrow = await db.get_birthdays_range(
            today - dt.timedelta(days=1), today + dt.timedelta(days=1),
            max_last_notification_time=now - dt.timedelta(hours=24)
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
            timezone = pytz.utc

        # Determine midnight in this person's timezone so we can
        # wish them happy birthday at the start of their day
        birthday_this_year = dt.datetime(today.year, birthday.month, birthday.day)
        midnight_local: dt.datetime = timezone.localize(birthday_this_year)
        midnight_utc = midnight_local.astimezone(pytz.utc)
        midnight_delta = midnight_utc - now

        # Schedule the birthday task if their localized midnight is within the
        # next 24 hours
        # TODO I'm worried that it could be possible we lose a birthday
        #   in a race condition here...
        if dt.timedelta(0) <= midnight_delta < dt.timedelta(hours=24):
            self._create_birthday_task(user_id, midnight_delta)
            return True

        # Otherwise, if we missed their midnight but it's still their birthday,
        # we can send immediately (negative delta will not sleep)
        now_local: dt.datetime = now.astimezone(timezone)
        if (midnight_delta < dt.timedelta(0)
                and now_local.date() == birthday_this_year.date()):
            self._create_birthday_task(user_id, midnight_delta)
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
        if user is self.bot.user:
            # Sandpiper herself, for easter egg below
            guilds = self.bot.guilds
        else:
            guilds: list[discord.Guild] = user.mutual_guilds

        # Get some user info to use in the message

        name = None
        if (await db.get_privacy_preferred_name(user_id)) is PrivacyType.PUBLIC:
            name = await db.get_preferred_name(user_id)
        has_preferred_name = name is not None

        pronouns = None
        if (await db.get_privacy_pronouns(user_id)) is PrivacyType.PUBLIC:
            pronouns = await db.get_pronouns_parsed(user_id)
        if pronouns:
            # This is making an assumption that the first pronouns listed
            # are preferred over the others, which is NOT true for everyone,
            # but we need to pick one, so this is the best we can do for now
            pronouns = pronouns[0]
        else:
            pronouns = common_pronouns['they']

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

            if user_id == self.bot.user.id:
                # Little easter egg for Sandpiper's birthday
                bday_msg_template = (
                    "hey! it's.... wait, it's my birthday!! thanks for the "
                    "great year everyone. ily all and I hope you've enjoyed "
                    "me being here! :heartpulse: :hatching_chick:"
                )
            else:
                bday_msg_template = self._get_random_message(age=age is not None)
            bday_msg = format_birthday_message(
                bday_msg_template, user_id=user_id,
                name=name, pronouns=pronouns, age=age
            )
            await bday_channel.send(bday_msg)

        # Store the time we sent the notification
        await db.set_last_birthday_notification(user_id, utc_now())

    async def get_past_upcoming_birthdays(
            self, past_birthdays_day_range: int = 7,
            upcoming_birthdays_day_range: int = 14
    ) -> tuple[list[tuple[int, dt.date]], list[tuple[int, dt.date]]]:
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

    # region Commands

    auto_order = AutoOrder()
    PAST_BIRTHDAY_EMOJIS = '🔷'
    UPCOMING_BIRTHDAY_EMOJIS = '🎂🍰🧁🎈🎁🎉🎊'

    @auto_order
    @commands.group(
        name='birthdays', invoke_without_command=False,
        brief="Birthday commands.",
        help="Commands for viewing birthdays."
    )
    async def birthdays(self, ctx: commands.Context):
        pass

    async def format_bday_upcoming(
            self, user_id: int, guild: discord.Guild, past: bool
    ) -> Optional[str]:
        db = await self._get_database()

        user = self.bot.get_user(user_id)
        if user is None:
            return None
        if not guild.get_member(user_id):
            return None
        if await db.get_privacy_birthday(user_id) is not PrivacyType.PUBLIC:
            return None

        emojis_set = (
            self.PAST_BIRTHDAY_EMOJIS if past else self.UPCOMING_BIRTHDAY_EMOJIS
        )
        emoji = emojis_set[cheap_user_hash(user_id) % len(emojis_set)]

        bday = await db.get_birthday(user_id)
        user_qual = f"{user.name}#{user.discriminator}"

        if await db.get_privacy_preferred_name(user_id) is PrivacyType.PUBLIC:
            name = f"**{await db.get_preferred_name(user_id)}** ({user_qual})"
        else:
            name = f"**{user_qual}**"

        return f"{emoji}  `{bday:%b %d}` - {name}"

    @auto_order
    @birthdays.command(
        name='upcoming', aliases=('soon',),
        help="View upcoming birthdays."
    )
    async def birthdays_upcoming(self, ctx: commands.Context):
        past_raw, upcoming_raw = await self.get_past_upcoming_birthdays(
            self.past_birthdays_day_range, self.upcoming_birthdays_day_range
        )
        now = utc_now()

        past = []
        for user_id, _ in sort_dates_no_year(past_raw, lambda x: x[1], now):
            bday_str = await self.format_bday_upcoming(
                user_id, ctx.guild, past=True
            )
            if bday_str:
                past.append(bday_str)

        upcoming = []
        for user_id, _ in sort_dates_no_year(upcoming_raw, lambda x: x[1], now):
            bday_str = await self.format_bday_upcoming(
                user_id, ctx.guild, past=False
            )
            if bday_str:
                upcoming.append(bday_str)

        if not past and not upcoming:
            await ctx.send("No birthdays yet!")
            return

        msg = []
        if past:
            msg.append("Past birthdays:")
            msg.extend(past)

        if past and upcoming:
            msg.append('')

        if upcoming:
            msg.append(f"Upcoming birthdays:")
            msg.extend(upcoming)

        await ctx.send('\n'.join(msg))

    # endregion
