import asyncio

import discord
from discord.ext import commands
from main import dvvt

class GuildChannelDelete(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        if isinstance(channel, discord.TextChannel):
            await self.client.db.execute("UPDATE channels SET active = False WHERE channel_id = $1", channel.id)