import asyncio

import discord
from discord.ext import commands
from main import dvvt

class GuildChannelCreate(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        if isinstance(channel, discord.TextChannel):
            try:
                m = await self.client.wait_for('message', check=lambda m: m.channel.id == channel.id and len(m.mentions) > 0, timeout=60)
            except asyncio.TimeoutError:
                pass
            else:
                await self.client.db.execute("INSERT INTO channels(guild_id, channel_id, owner_id) VALUES($1, $2, $3)", channel.guild.id, channel.id, m.mentions[0].id)