import asyncio

import discord
from discord.ext import commands
from main import dvvt
from time import time

class GuildChannelCreate(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @commands.has_permissions(manage_messages=True)
    @commands.message_command(name="Register private channel")
    async def register_private_channel(self, ctx: discord.ApplicationContext, message: discord.Message):
        """Right click on the first Ticketbot message to register it as a private channel."""
        if (not message.guild) or message.guild.id != 1288032530569625660:
            return await ctx.respond("This command should only be run in Dank Vibes.", ephemeral=True)
        if message.author.id != 557628352828014614:
            return await ctx.respond("This message was not sent by Ticket Tool.", ephemeral=True)
        if "DVB_PVC_CREATED" not in message.content:
            return await ctx.respond("This message is not a message sent on the creation of a private channel.", ephemeral=True)
        if len(message.mentions) < 1:
            return await ctx.respond("I could not find the owner of this channel.", ephemeral=True)
        owner = message.mentions[0]
        existing_channels = await self.client.db.fetch("SELECT * FROM channels WHERE channel_id = $1", message.channel.id)
        if len(existing_channels) > 1:
            await ctx.respond(f"This channel is already registered as a private channel for {existing_channels[0].get('owner_id')}", ephemeral=True)
        await self.client.db.execute(
            "INSERT INTO channels(guild_id, channel_id, owner_id, active, last_used) VALUES($1, $2, $3, $4, $5)",
            message.guild.id, message.channel.id, owner.id, True, round(time()))
        await ctx.respond("Channel registered.", ephemeral=True)
        await ctx.send(
                f"{owner.mention}, manage your channel with these commands: https://staticx.gh.nogra.app/dankvibesbot/privchannel/input-suggestion.png")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        if isinstance(channel, discord.TextChannel):
            try:
                def check(message: discord.Message):
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