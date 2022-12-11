import logging

import discord

from sandpiper.common.discord import find_user_in_mutual_guilds
from sandpiper.common.embeds import *
from sandpiper.common.misc import listify
from sandpiper.user_data import Database, PrivacyType
from ..upgrades import UpgradeHandler

logger = logging.getLogger(__name__)


class Sandpiper_1_6_0(UpgradeHandler):
    def version(self) -> str:
        return "1.6.0"

    async def on_upgrade(self):
        db = await self._get_database()
        if db is None:
            return

        for user_id in await db.get_all_user_ids():
            if (await db.get_birthday(user_id)) is not None:
                await self.tell_about_birthday(user_id, db)

    async def tell_about_birthday(self, user_id: int, db: Database):
        logger.info(
            f"User's birthday is set; telling them about the new feature "
            f"(user_id={user_id})"
        )

        user: discord.User = self.sandpiper.get_user(user_id)
        if user is None:
            logger.info(f"Can't find user {user_id} in any guild")
            return

        # General info about the birthday announcements
        mutual_guilds = listify(
            [
                m.guild.name
                for m in find_user_in_mutual_guilds(
                    self.sandpiper, self.sandpiper.user.id, user_id
                )
            ],
            2,
        )
        embed = SpecialEmbed(title="Birthday announcements update 🥳", join="\n\n")
        embed.append(
            f"Hey!! I'm a bot from {mutual_guilds}. I've just gotten a "
            f"birthday announcement feature. I can announce your birthday "
            f"when it arrives to all the servers you and I are both in!"
        )

        # Tell them about how they can control their birthday announcement
        bday_privacy = await db.get_privacy_birthday(user_id)
        if bday_privacy is PrivacyType.PRIVATE:
            embed.append(
                "Your birthday is currently set to **private**, so I will "
                "not announce it. If you want me to announce your birthday "
                "when it comes, type `privacy birthday public`! c:"
            )
        elif bday_privacy is PrivacyType.PUBLIC:
            embed.append(
                "Your birthday is currently set to **public**, so I will "
                "announce it! If you don't want me to announce your birthday "
                "when it comes, type `privacy birthday private`. c:"
            )

        embed.append(
            "You can use `bio show` to see all your data stored with me "
            "and `help` to see all available commands. And if you have no idea "
            "who I am, feel free to use `bio delete` to delete all your data "
            "and be on your way!"
        )

        await embed.send(user)

        await self.tell_about_age(user_id, db)

    async def tell_about_age(self, user_id: int, db: Database):
        logger.info(f"Telling the user about age privacy (user_id={user_id})")

        age_privacy = await db.get_privacy_age(user_id)

        # Change their age to private as a courtesy, so they're not blindsided
        # by their age in a notification if they haven't checked DMs or
        # something
        if age_privacy is PrivacyType.PUBLIC:
            logger.info(
                f"User's age is public; switching it to private " f"(user_id={user_id})"
            )
            await db.set_privacy_age(user_id, PrivacyType.PRIVATE)

        user: discord.User = self.sandpiper.get_user(user_id)
        if user is None:
            logger.info(f"Can't find user {user_id} in any guild")
            return

        # General info about age in the announcement
        embed = SpecialEmbed(title="Age in birthday announcement", join="\n\n")
        embed.append(
            "I can also announce your new age in your birthday message "
            "if your age privacy is set to public!"
        )

        # Info about their privacy value
        if age_privacy is PrivacyType.PUBLIC:
            # Tell them we changed their privacy to private
            embed.append(
                "I know this might be uncomfortable, so I've changed your "
                "age from public to **private** as a precaution. If you want "
                "your age announced, you can type `privacy age public` to "
                "make it public again."
            )
        elif age_privacy is PrivacyType.PRIVATE:
            embed.append(
                "Yours is currently set to **private**, but if you want "
                "to change that, type `privacy age public`."
            )

        # Their birthday doesn't include birth year, so tell them how to set it
        if (await db.get_age(user_id)) is None:
            bday = await db.get_birthday(user_id)
            embed.append(
                f"You will also have to include your birth year in your "
                f"birthday (you currently only have the month and day stored). "
                f"To set your birthday with the year, type "
                f"`birthday set {bday.strftime('YYYY-%m-%d')}`!"
            )

        await embed.send(user)
