import asyncio
import time

import discord
from discord.ext import commands

import cogs.mod.decancer
from main import dvvt
from utils.time import humanize_timedelta
from utils.format import box

class MemberJoin(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        member_is_banned = False
        # check for dungeon ban
        guild_config = await self.client.get_guild_settings(member.guild.id)
        if guild_config.autoban_duration > 0:
            member_created_timestamp = member.created_at.timestamp()
            number_of_days = guild_config.autoban_duration
            number_of_days_in_seconds = number_of_days * 86400
            now = round(time.time())
            log_channel = member.guild.get_channel(
                {595457764935991326: 616007729718231161, 871734809154707467: 978563862896967681}.get(member.guild.id,
                                                                                                     None))
            if now - member_created_timestamp < number_of_days_in_seconds:
                allow_bypass = await self.client.db.fetchval("SELECT bypass_ban FROM userconfig WHERE user_id = $1", member.id)
                if allow_bypass is True:
                    if log_channel is not None:
                        await log_channel.send(f"{member} ({member.id}) was allowed to bypass the Auto-ban and allowed into the server.")
                else:
                    msg = f"Welcome to {member.guild.name}, {member.name}!\nAs we do not allow alts in this server, **all new accounts are automatically banned**. \n\nIf you were wrongfully banned, feel free to appeal at this link: https://docs.google.com/forms/d/e/1FAIpQLScfv1HTWkpimqS3Q8MviVG92K0xmHm87T0vBx3dNZ19mXB7VQ/viewform\nAllow a few days for a response."
                    try:
                        await member.send(msg)
                    except Exception as e:
                        if log_channel is not None:
                            await log_channel.send(f"I was unable to DM {member} ({member.id}) about their auto-ban.")
                    try:
                        await member.ban(reason="Account too young")
                        member_is_banned = True
                        return
                    except Exception as e:
                        await log_channel.send(f"I was unable to ban {member} ({member.id}):\n{box(str(e), lang='py')}")
                        member_is_banned = False
        await asyncio.sleep(5.0)
        if member_is_banned is True:
            return
        else:
            decancer_cog: cogs.mod.decancer.Decancer = self.client.get_cog('mod')
            member = member.guild.get_member(member.id)
            if member is not None:
                guild: discord.Guild = member.guild
                serverconfig = await self.client.get_guild_settings(guild.id)
                if not serverconfig.auto_decancer:
                    return
                old_nick = member.display_name
                if not decancer_cog.is_cancerous(old_nick):
                    return
                member = guild.get_member(member.id)
                if not member:
                    return
                if member.top_role >= guild.me.top_role:
                    return
                new_cool_nick = await decancer_cog.nick_maker(guild, old_nick)
                if old_nick.lower() != new_cool_nick.lower():
                    try:
                        await member.edit(reason=f"Auto Decancer | Old name ({old_nick}): contained special characters", nick=new_cool_nick)
                    except (discord.NotFound, discord.Forbidden):
                        pass
                    else:
                        await decancer_cog.decancer_log(guild, member, guild.me, old_nick, new_cool_nick, "Auto Decancer on join 🤖")


