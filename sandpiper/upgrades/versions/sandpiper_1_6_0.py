import logging

import discord

from ..upgrades import UpgradeHandler
from sandpiper.user_data import PrivacyType

logger = logging.getLogger(__name__)


class Sandpiper_1_6_0(UpgradeHandler):

    def version(self) -> str:
        return '1.6.0'

    async def on_upgrade(self):
        db = await self._get_database()
        if db is None:
            return

        for user_id in await db.get_all_user_ids():
            if (await db.get_privacy_age(user_id)) is PrivacyType.PUBLIC:
                await self.age_is_public(user_id)

    async def age_is_public(self, user_id: int):
        logger.info(
            f"User's age is public; switching it to private and notifying the "
            f"user (user_id={user_id})"
        )
        db = await self._get_database()
        await db.set_privacy_age(user_id, PrivacyType.PRIVATE)

        user: discord.User = self.bot.get_user(user_id)
        if user is None:
            logger.info(f"Can't find user {user_id} in any guild")
            return

        await user.send(
            "Hey! I've just updated with a birthday notification feature. "
            "This means that if you've set your birthday to public, I will "
            "announce your birthday when it comes to all the servers you and I "
            "are both in!"
            "\n\n"
            "Additionally, if you've set your age to public, I will announce "
            "your new age in the birthday message. I know this might be "
            "uncomfortable, so I've set your age to private as a precaution. "
            "If you want your age announced, you can simply type `privacy age "
            "public` to make it public again."
        )
