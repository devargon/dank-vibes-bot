import asyncio

import discord
from discord.ext import commands
from main import dvvt
from time import time

class GuildChannelCreate(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        if isinstance(channel, discord.TextChannel):
            try:
                def check(message: discord.Message):
                    print(f"message.channel.id == channel.id: {message.channel.id == channel.id}")
                    print(f"len(m.mentions) > 0: {len(message.mentions) > 0}")
                    print(f"DVB_PVC_CREATED in message.content: " + "DVB_PVC_CREATED" in message.content)
                    return message.channel.id == channel.id and len(message.mentions) > 0 and "DVB_PVC_CREATED" in message.content
                m = await self.client.wait_for('message', check=check, timeout=60)
            except asyncio.TimeoutError:
                pass
            else:
                owner = m.mentions[0]
                if type(channel) == discord.TextChannel and channel.category is not None and "private channels" in channel.category.name.lower():
                    active = True
                else:
                    print(f"{type(channel) == discord.TextChannel} and {channel.category is not None} and " + "private channels" in channel.category.name.lower())
                    active = False
                await self.client.db.execute("INSERT INTO channels(guild_id, channel_id, owner_id, active, last_used) VALUES($1, $2, $3, $4, $5)", channel.guild.id, channel.id, owner.id, active, round(time()))
                if active:
                    await channel.send(f"{owner.mention}, manage your channel with these commands: https://staticx.gh.nogra.app/dankvibesbot/privchannel/input-suggestion.png")