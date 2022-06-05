import os

import discord
from discord.ext import commands
from .status_utils import check_status, get_custom_activity
from .status_task import check_status
from main import dvvt

guild_id = 871734809154707467 if os.getenv('state') == '1' else 595457764935991326

class Ready(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @commands.Cog.listener()
    async def on_ready(self):
        check_status.start()
        for guild in self.client.guilds:
            settings = await self.client.fetch_guild_settings(guild.id)
            if settings.statusroleenabled is not True:
                return
            guild = self.client.get_guild(guild_id)
            if guild is None:
                return
            else:
                role = guild.get_role(settings.statusroleid)
                for member in guild.members:
                    if member.bot:
                        continue
                    activity = get_custom_activity(member)
                    if activity is None:
                        status = ""
                    else:
                        status = activity.name
                    if role is None:
                        print(f"invalid role id: {settings.statusroleid}")
                        return

                    if check_status(status, settings) is True:
                        if role in member.roles:
                            pass
                        else:
                            await member.add_roles(role, reason=f"User has \"{settings.statustext}\" in their status")
                    else:
                        if role in member.roles:
                            await member.remove_roles(role, reason=f"User does not have \"{settings.statustext}\" in their status")
                print("Initial Status check done")

