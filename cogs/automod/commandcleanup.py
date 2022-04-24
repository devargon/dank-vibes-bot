import asyncio
import contextlib
import os
import discord
from discord.ext import commands

class CommandCleanup(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.limit = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if not message.guild:
            return
        modchannel = message.guild.get_channel(616007729718231161) if message.guild.id == 595457764935991326 else message.guild.get_channel(946245571394564107) if message.guild.id == 871734809154707467 else None
        if (result := await self.client.db.fetchrow("SELECT * FROM usercleanup WHERE target_id = $1 AND guild_id = $2 AND channel_id = $3", message.author.id, message.guild.id, message.channel.id)) is not None:
            if message.interaction: # Is an application command, we can use this to remind the user it's not allowed
                user = message.interaction.user
                if result.get('message') is not None and len(result.get('message')) > 0:
                    if message.channel.permissions_for(user).manage_messages is True:
                        return
                    await message.channel.send(f"{user.mention} {result.get('message')}", delete_after=10.0)
                if self.limit.get(user.id, 0) > 5:
                    if modchannel is not None:
                        em = discord.Embed(description = f"**{user.id}** {user.mention} has exceeded the threshold for running **{message.author}**'s commands (5 commands in a minute).", color = discord.Color.red(), timestamp = discord.utils.utcnow())
                        em.set_author(name=f"{user}", icon_url=user.display_avatar.url)
                        em.set_footer(text=f"{user.id}")
                        await modchannel.send(embed=em)
                    self.limit[user.id] = 0
            else:
                if result.get('message') is not None and len(result.get('message')) > 0:
                    await message.channel.send(result.get('message'), delete_after=10.0)
            with contextlib.suppress(Exception):
                await message.delete()
            if message.interaction and message.interaction.user:
                if message.interaction.user.id not in self.limit:
                    self.limit[message.interaction.user.id] = 0
                else:
                    self.limit[message.interaction.user.id] = self.limit[message.interaction.user.id] + 1
                await asyncio.sleep(60.0)
                self.limit[message.interaction.user.id] = self.limit[message.interaction.user.id] - 1
