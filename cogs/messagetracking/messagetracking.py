import discord
from discord.ext import commands

class MessageTracking(commands.Cog, name='mod'):
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
        result = await self.client.pool_pg.fetchrow("SELECT * FROM stickymessages WHERE guild_id = $1 and channel_id = $2", message.guild.id, message.channel.id)
        if result is None:
            return
        self.queue.append(message.channel)
        try:
            old_bot_message = await message.channel.fetch_message(result.get('message_id'))
        except discord.NotFound:
            pass
        else:
            await old_bot_message.delete()
        if result.get('type') == 0:
            embedjson = json.loads(result.get('message'))
            newmessage = await message.channel.send(embed=discord.Embed.from_dict(embedjson))
        else:
            newmessage = await message.channel.send(result.get('message'))
        await self.client.pool_pg.execute("UPDATE stickymessages SET message_id = $1 WHERE guild_id = $2 and channel_id = $3", newmessage.id, message.guild.id, message.channel.id)
        self.queue.remove(message.channel)