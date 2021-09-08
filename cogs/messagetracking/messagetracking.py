import discord
from discord.ext import commands
import json
import asyncio

class MessageTracking(commands.Cog, name='MessageTracking'):
    def __init__(self, client):
        self.client = client
        self.queue = []

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel in self.queue:
            return
        if message.author == self.client.user:
            return
        if not message.guild:
            return
        if message.author.bot:
            return
        if message.webhook_id:
            return
        if message.channel.id != 871734809653833740:
            return
        self.queue.append(message.channel)
        result = await self.client.pool_pg.fetchrow("SELECT * FROM messagelog WHERE user_id = $1", message.author.id)
        if result is None:
            await self.client.pool_pg.execute("INSERT INTO messagelog VALUES($1, $2)", message.author.id, 1)
        else:
            existing_count = result.get('messagecount')
            await self.client.pool_pg.execute("UPDATE messagelog SET messagecount = $1 WHERE user_id = $2", existing_count+1, message.author.id)
        await asyncio.sleep(8)
        self.queue.remove(message.channel)