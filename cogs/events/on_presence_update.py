import os

import discord
from discord.ext import commands
from .status_utils import check_status, get_custom_activity

from main import dvvt
guild_id = 871734809154707467 if os.getenv('state') == '1' else 595457764935991326

class PresenceUpdate(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client
        self.cooldown = []

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        settings = await self.client.get_guild_settings(after.guild.id)
        if before.bot:
            return
        if before.id in self.cooldown:
            return
        activity = get_custom_activity(after)
        if activity is None:
            status = ""
        else:
            status = activity.name
        if status is None:
            status = ""

        settings = await self.client.get_guild_settings(after.guild.id)
        if settings.statusroleenabled:
            role = after.guild.get_role(settings.statusroleid)
            if role is None:
                return

            if check_status(status, settings) is True:
                if role in after.roles:
                    pass
                else:
                    await after.add_roles(role, reason=f"User has \"{settings.statustext}\" in their status")
            else:
                if role in after.roles:
                    await after.remove_roles(role, reason=f"User does not have \"{settings.statustext}\" in their status")




