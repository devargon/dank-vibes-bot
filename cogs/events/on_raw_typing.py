import asyncio
import contextlib
import os
import time
import discord
from discord.ext import commands

from main import dvvt
lems_id = 827080569501777942 if os.getenv('state') == '1' else 781764427287756841
telltale_channel_id = 871737314831908974 if os.getenv('state') == '1' else 929563828558135306

class RawTyping(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client
        self.last_muted = 0

    @commands.Cog.listener()
    async def on_raw_typing(self, payload: discord.RawTypingEvent):
        if payload.member is not None and payload.member.id == lems_id:
            member = payload.member
            print("found target")
        else:
            return print("not target")
        guild = self.client.get_guild(payload.guild_id)
        channel = guild.get_channel(payload.channel_id)
        settings = await self.client.get_guild_settings(payload.guild_id)
        if settings is not None and settings.mute_lem is True:
            if time.time() - self.last_muted > 35:
                # more than 35 seconds since lem was muted
                originaloverwrite = channel.overwrites_for(member) if member in channel.overwrites else None
                muteoverwrite = channel.overwrites_for(member) if member in channel.overwrites else discord.PermissionOverwrite()
                muteoverwrite.send_messages = False
                await channel.set_permissions(member, overwrite=muteoverwrite)
                with contextlib.suppress(Exception):
                    await self.client.get_channel(telltale_channel_id).send(f"{member} just got muted for typing HAHAHAHHA")
                await asyncio.sleep(5)
                self.last_muted = round(time.time())
                await channel.set_permissions(member, overwrite=originaloverwrite)
