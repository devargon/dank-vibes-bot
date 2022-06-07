import os

from discord.ext import commands, tasks

from .on_message import OnMessage
from .on_presence_update import PresenceUpdate
from .on_ready import Ready
from .status_task import StatusTasks
from .status_utils import *

guild_id = 871734809154707467 if os.getenv('state') == '1' else 595457764935991326

class Events(StatusTasks, PresenceUpdate, OnMessage, commands.Cog):
    def __init__(self, client):
        self.client = client
        self.cooldown = []

    @tasks.loop(minutes=1)
    async def check_status(self):
        print('checking status')
        await self.client.wait_until_ready()
        for guild in self.client.guilds:
            settings = await self.client.fetch_guild_settings(guild.id)
            if settings.statusroleenabled is not True:
                return
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
                            await member.remove_roles(role,
                                                      reason=f"User does not have \"{settings.statustext}\" in their status")

    @commands.Cog.listener()
    async def on_ready(self):
        self.check_status.start()
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
                            await member.remove_roles(role,
                                                      reason=f"User does not have \"{settings.statustext}\" in their status")
                print("Initial Status check done")


