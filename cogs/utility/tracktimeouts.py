import os
import time

from utils.time import humanize_timedelta

import discord
from discord.ext import commands

modlog_channelID = 873616122388299837 if os.getenv('state') == '1' else 640029959213285387


class TimeoutTracking(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        now = round(time.time())
        if before.communication_disabled_until != after.communication_disabled_until:
            if await self.client.pool_pg.fetchval("SELECT * FROM serverconfig WHERE guild_id = $1 AND settings = $2", after.guild.id, 'timeoutlog') is True:
                guild = before.guild
                if guild.get_member(self.client.user.id).guild_permissions.view_audit_log:
                    async for entry in guild.audit_logs(limit=6, action=discord.AuditLogAction.member_update):
                        if entry.target.id == after.id and entry.target.communication_disabled_until == after.communication_disabled_until:
                            offender = entry.target
                            moderator = entry.user
                            reason = entry.reason or "NA"

                            if entry.target.communication_disabled_until is not None:
                                timeout_end_dt = entry.target.communication_disabled_until
                                timeout_end_unix = timeout_end_dt.timestamp()
                                duration = humanize_timedelta(seconds=timeout_end_unix - now)
                                embed = discord.Embed(
                                    title='Timeout', description=f'**Offender**: {offender} {offender.mention}\n**Reason**: {reason}\n**Duration**: {duration}\n**Responsible Moderator**: {moderator}', color=discord.Color.orange(), timestamp=discord.utils.utcnow())
                            else:
                                embed = discord.Embed(
                                    title='Timeout Removed', description=f'**Offender**: {offender} {offender.mention}\n**Reason**: {reason}\n**Responsible Moderator**: {moderator}', color=discord.Color.green(), timestamp=discord.utils.utcnow())
                            try:
                                await self.client.get_channel(modlog_channelID).send(embed=embed)
                            except Exception as e:
                                print(e)
                            else:
                                break
