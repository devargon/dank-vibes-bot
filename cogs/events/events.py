import os
import time

from discord.ext import commands, tasks
from main import dvvt
from .on_message import OnMessage
from .on_presence_update import PresenceUpdate
from .on_ready import Ready
from .on_member_join import MemberJoin
from .status_task import StatusTasks
from .status_utils import *

from utils.format import box

guild_id = 871734809154707467 if os.getenv('state') == '1' else 595457764935991326

class Events(MemberJoin, StatusTasks, PresenceUpdate, OnMessage, commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client
        self.mafia_wait = False
        self.client: dvvt = client
        self.cooldown = []

    @tasks.loop(minutes=1)
    async def check_status(self):
        await self.client.wait_until_ready()
        for guild in self.client.guilds:
            settings = await self.client.get_guild_settings(guild.id)
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
                    if status is None:
                        status = ""
                    if role is None:
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
            settings = await self.client.get_guild_settings(guild.id)
            if settings.statusroleenabled is True:
                role = guild.get_role(settings.statusroleid)
                if role is None:
                    pass
                else:
                    for member in guild.members:
                        if member.bot:
                            continue
                        activity = get_custom_activity(member)
                        if activity is None:
                            status = ""
                        else:
                            status = activity.name
                        if status is None:
                            status = ""

                        if check_status(status, settings) is True:
                            if role in member.roles:
                                pass
                            else:
                                await member.add_roles(role, reason=f"User has \"{settings.statustext}\" in their status")
                        else:
                            if role in member.roles:
                                await member.remove_roles(role,
                                                          reason=f"User does not have \"{settings.statustext}\" in their status")
            if settings.autoban_duration > 0:
                for member in guild.members:
                    if not member.bot:
                        member_created_timestamp = member.created_at.timestamp()
                        number_of_days = settings.autoban_duration
                        number_of_days_in_seconds = number_of_days * 86400
                        now = round(time.time())
                        log_channel = member.guild.get_channel(
                            {595457764935991326: 616007729718231161, 871734809154707467: 978563862896967681}.get(
                                member.guild.id,
                                None))
                        if now - member_created_timestamp < number_of_days_in_seconds:
                            allow_bypass = await self.client.db.fetchval(
                                "SELECT bypass_ban FROM userconfig WHERE user_id = $1", member.id)
                            if allow_bypass is True:
                                continue
                            else:
                                msg = f"Welcome to {member.guild.name}, {member.name}!\nAs we do not allow alts in this server, **all new accounts are automatically banned**. \n\nIf you were wrongfully banned, feel free to appeal at this link: https://docs.google.com/forms/d/e/1FAIpQLScfv1HTWkpimqS3Q8MviVG92K0xmHm87T0vBx3dNZ19mXB7VQ/viewform\nAllow a few days for a response."
                                try:
                                    await member.send(msg)
                                except Exception as e:
                                    if log_channel is not None:
                                        await log_channel.send(
                                            f"I was unable to DM {member} ({member.id}) about their auto-ban.")
                                try:
                                    await member.ban(reason="Account too young")
                                    return
                                except Exception as e:
                                    await log_channel.send(
                                        f"I was unable to ban {member} ({member.id}):\n{box(str(e), lang='py')}")


