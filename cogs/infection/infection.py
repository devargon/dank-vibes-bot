import discord
from discord.ext import commands

class infection(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.infected = None

    @commands.Cog.listener()
    async def on_ready(self):
        infections = await self.client.pool_pg.fetch("SELECT member_id FROM infections")
        self.infected = [i.get('member_id') for i in infections]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if type(self.infected) is not list:
            return
        if message.author.id not in self.infected:
            return
        if len(message.mentions) > 0:
            for member in message.mentions:
                if member.id == self.client.user.id:
                    return
                if member.id in self.infected:
                    return
                self.infected.append(member.id)
                await self.client.pool_pg.execute("INSERT INTO infections (member_id, guild_id, channel_id, message_id, timeinfected) VALUES ($1, $2, $3, $4, $5)", member.id, message.guild.id, message.channel.id, message.id, message.created_at.timestamp())
            await message.add_reaction('🩺')
        else:
            return