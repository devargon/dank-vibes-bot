import discord
from discord.ext import commands
from time import time

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
                await self.client.pool_pg.execute("INSERT INTO infections (member_id, guild_id, channel_id, message_id, infector, timeinfected) VALUES ($1, $2, $3, $4, $5, $6)", member.id, message.guild.id, message.channel.id, message.id, message.author.id, round(time()))
            await message.add_reaction('😷')
            await message.add_reaction('⚠️')
        else:
            return

    @commands.Cog.listener()
    async def on_member_update(self, member_before, member_after):
        if member_before.display_name != member_after.display_name:
            old_nickname = member_before.display_name
            new_nickname = member_after.display_name
            if f"[AFK] {old_nickname}" == new_nickname:
                return
            if f"[AFK] {new_nickname}" == old_nickname:
                return
            result = await self.client.pool_pg.fetchrow(
                "SELECT * FROM freezenick WHERE user_id = $1 and guild_id = $2", member_after.id,
                member_after.guild.id)
            if result is not None:
                if result.get('nickname') == new_nickname:
                    return
                if result.get('nickname') == old_nickname:
                    return
                if result.get('old_nickname') == new_nickname:
                    return
                if result.get('old_nickname') == old_nickname:
                    return
            await self.client.pool_pg.execute("INSERT INTO nickname_changes VALUES($1, $2, $3, $4)",
                                              member_before.guild.id, member_before.id, new_nickname, round(time()))